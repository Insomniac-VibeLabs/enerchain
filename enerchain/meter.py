"""Reference model of one EC-SEAL1 meter: EC-MINT1, its FRAM, and the QS7001
signing oracle.

The model follows hardware/asic/rtl/ec_mint1.v and
firmware/qs7001/sign_oracle.c rule for rule, so that

- tools/check_rtl.py can run the RTL testbench scenario here and compare the
  signed records byte for byte, and
- the development network can be fed records that a real pair would produce.

It models events (pulses, power cuts, tamper), not clock cycles.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import crypto
from .record import (CLASS_TAG, MAX48, ROLE_GEN, ROLE_GRID, MeterRecord,
                     crc8, crc16)

Q_WH = 1000
SIGN_EVERY = 10
CMIN = -(1 << 47)

ROM_ADDR = 0x0100
LOCK_ADDR = 0x0200
SLOT_ADDR = (0x0000, 0x0040)


def calibration_image(meter_id: int, role: int, frames: list[bytes]) -> bytes:
    """Factory image: A5 5A role id[4] then length-prefixed STPM32 frames."""
    if role not in (ROLE_GEN, ROLE_GRID):
        raise ValueError("role must be GEN (1) or GRID (2)")
    body = b"\xA5\x5A" + bytes([role]) + meter_id.to_bytes(4, "big")
    for f in frames:
        if not 0 < len(f) < 256:
            raise ValueError("frame length 1..255")
        body += bytes([len(f)]) + f
    body += b"\x00"
    if len(body) > 256:
        raise ValueError("image longer than 256 bytes")
    return body + bytes(256 - len(body))


class Fram:
    """FM25V02A contents. Survives power cuts. Blank parts read 0xFF here."""

    def __init__(self) -> None:
        self.mem = bytearray(b"\xFF" * 32768)

    def read(self, addr: int, n: int) -> bytes:
        return bytes(self.mem[addr:addr + n])

    def write(self, addr: int, data: bytes) -> None:
        self.mem[addr:addr + len(data)] = data


class SignerOracle:
    """QS7001 image semantics (firmware/qs7001/sign_oracle.c)."""

    def __init__(self, alg: str = crypto.METER_ALG, seed: bytes | None = None,
                 q: int = Q_WH) -> None:
        self.alg = alg
        self.q = q          # the firmware constant Q_WH; tests may shrink it
        self.seed = seed
        self.pk: bytes | None = None
        self._sk: bytes | None = None
        self.personalized = False
        self.wiped = False
        self.meter_id = 0
        self.role = 0
        self.last = (0, 0, 0, 0)  # seq, e_exp, e_imp, tokens
        self.keygens = 0

    def personalize(self, meter_id: int, role: int) -> bytes:
        if self.personalized or self.wiped:
            raise RuntimeError("already personalized")
        self.pk, self._sk = crypto.keygen(self.alg, self.seed)
        self.keygens += 1
        self.personalized = True
        self.meter_id, self.role = meter_id, role
        return self.pk

    def wipe(self) -> None:
        self._sk = None
        self.wiped = True

    def sign(self, raw: bytes) -> bytes | None:
        """Return the signature, or None for a refusal (EE) or a dead part."""
        if self.wiped or not self.personalized:
            return None
        r = MeterRecord.unpack(raw)
        seq0, exp0, imp0, tok0 = self.last
        ok = (
            r.meter_id == self.meter_id and r.version == 1 and r.role == self.role
            and r.class_tag == CLASS_TAG and r.seq > seq0
            and r.e_exp >= exp0 and r.e_imp >= imp0 and r.tokens >= tok0
            and r.tokens * self.q <= r.e_exp
        )
        if not ok:
            return None
        self.last = (r.seq, r.e_exp, r.e_imp, r.tokens)
        assert self._sk is not None
        return crypto.sign(self.alg, self._sk, raw)


@dataclass
class _Slot:
    gen: int = 0
    e_exp: int = 0
    e_imp: int = 0
    tokens: int = 0
    credit: int = 0
    seq: int = 0
    since: int = 0

    def pack(self) -> bytes:
        body = (
            b"\xEC\x01" + self.gen.to_bytes(4, "big")
            + self.e_exp.to_bytes(6, "big") + self.e_imp.to_bytes(6, "big")
            + self.tokens.to_bytes(6, "big")
            + (self.credit & MAX48).to_bytes(6, "big")
            + self.seq.to_bytes(4, "big") + bytes([self.since])
        )
        return body + bytes([crc8(body)])

    @classmethod
    def unpack(cls, raw: bytes) -> "_Slot | None":
        if raw[:2] != b"\xEC\x01" or crc8(raw[:35]) != raw[35]:
            return None
        credit = int.from_bytes(raw[24:30], "big")
        if credit >> 47:
            credit -= 1 << 48
        return cls(
            gen=int.from_bytes(raw[2:6], "big"),
            e_exp=int.from_bytes(raw[6:12], "big"),
            e_imp=int.from_bytes(raw[12:18], "big"),
            tokens=int.from_bytes(raw[18:24], "big"),
            credit=credit,
            seq=int.from_bytes(raw[30:34], "big"),
            since=raw[34],
        )


@dataclass
class SignedRecord:
    record: bytes
    signature: bytes

    @property
    def parsed(self) -> MeterRecord:
        return MeterRecord.unpack(self.record)


@dataclass
class EcMint1:
    """EC-MINT1 behavior. One instance is one die on one board."""

    fram: Fram = field(default_factory=Fram)
    signer: SignerOracle = field(default_factory=SignerOracle)
    q: int = Q_WH
    sign_every: int = SIGN_EVERY

    def __post_init__(self) -> None:
        self.records: list[SignedRecord] = []
        self.refused = 0
        self.dead = False
        self._dirty_pulses = 0
        self.boot()

    # ---------------- boot, provisioning, persistence ---------------------
    def boot(self) -> None:
        self.locked = False
        self.armed = False
        self.e_exp = self.e_imp = self.tokens = self.credit = self.since = 0
        self.seq = self.gen = 0
        rom = self.fram.read(ROM_ADDR, 256)
        mark = self.fram.read(LOCK_ADDR, 4)
        if mark[:2] == b"LK" and int.from_bytes(mark[2:4], "big") == crc16(rom):
            self._lock(rom)

    def provision(self, image: bytes) -> None:
        """Factory transcript on J5. Ignored once the image is locked."""
        if self.locked or len(image) != 256:
            return
        self.fram.write(ROM_ADDR, image)
        self.fram.write(LOCK_ADDR, b"LK" + crc16(image).to_bytes(2, "big"))
        self._lock(image)

    def _lock(self, rom: bytes) -> None:
        self.locked = True
        self.rom = rom
        self.cal_crc = crc16(rom)
        self.role = rom[2]
        self.meter_id = int.from_bytes(rom[3:7], "big")
        best = None
        for a in SLOT_ADDR:
            s = _Slot.unpack(self.fram.read(a, 36))
            if s and (best is None or s.gen > best.gen):
                best = s
        if best:
            self.gen, self.e_exp, self.e_imp = best.gen, best.e_exp, best.e_imp
            self.tokens, self.credit, self.seq, self.since = (
                best.tokens, best.credit, best.seq, best.since)
        self.armed = (rom[0:2] == b"\xA5\x5A" and rom[2] in (ROLE_GEN, ROLE_GRID)
                      and rom[7] != 0)

    def _persist(self) -> None:
        self.gen += 1
        s = _Slot(self.gen, self.e_exp, self.e_imp, self.tokens, self.credit,
                  self.seq, self.since)
        self.fram.write(SLOT_ADDR[self.gen & 1], s.pack())
        self._dirty_pulses = 0

    def power_cycle(self) -> None:
        """Power cut. Anything not yet in FRAM is lost, as on the board."""
        self.boot()

    @property
    def counting(self) -> bool:
        return self.locked and self.armed and not self.dead

    # ---------------- schedule --------------------------------------------
    def pulse_export(self, n: int = 1, persist: bool = True) -> None:
        for _ in range(n):
            if not self.counting:
                return
            self.e_exp += 1
            sign_req = False
            if self.credit == self.q - 1:
                self.credit = 0
                self.tokens += 1
                if self.since >= self.sign_every - 1:
                    self.since = 0
                    sign_req = True
                else:
                    self.since += 1
            else:
                self.credit += 1
            self._after_pulse(persist, sign_req)

    def pulse_import(self, n: int = 1, persist: bool = True) -> None:
        for _ in range(n):
            if not self.counting:
                return
            self.e_imp += 1
            if self.credit != CMIN:
                self.credit -= 1
            self._after_pulse(persist, False)

    def _after_pulse(self, persist: bool, sign_req: bool) -> None:
        if persist:
            self._persist()
        else:
            self._dirty_pulses += 1
        if sign_req:
            self._sign()

    def _sign(self) -> None:
        self.seq += 1
        rec = MeterRecord(self.meter_id, self.role, self.seq, self.e_exp,
                          self.e_imp, self.tokens, self.cal_crc).pack()
        self._persist()
        sig = self.signer.sign(rec)
        if sig is None:
            self.refused += 1
            return
        self.records.append(SignedRecord(rec, sig))

    # ---------------- tamper ----------------------------------------------
    def zeroize(self) -> None:
        self.signer.wipe()
        self.dead = True


class EnergyMeter:
    """An EC-SEAL1 fed by power instead of pulses.

    ``step(export_w, import_w, seconds)`` converts energy to whole watt-hour
    pulses and carries the fraction, as the STPM32 does internally.
    ``error`` is the meter's multiplicative error (0.005 is +0.5 %).
    """

    def __init__(self, meter_id: int, role: int, error: float = 0.0,
                 alg: str = crypto.METER_ALG, seed: bytes | None = None,
                 frames: list[bytes] | None = None) -> None:
        self.mint = EcMint1(signer=SignerOracle(alg, seed))
        self.pk = self.mint.signer.personalize(meter_id, role)
        self.image = calibration_image(meter_id, role, frames or [b"\x00\x00\x00\x00"])
        self.mint.provision(self.image)
        self.error = error
        self._exp_j = 0.0
        self._imp_j = 0.0

    @property
    def alg(self) -> str:
        return self.mint.signer.alg

    @property
    def cal_crc(self) -> int:
        return self.mint.cal_crc

    def step(self, export_w: float, import_w: float, seconds: float) -> None:
        k = 1.0 + self.error
        self._exp_j += max(export_w, 0.0) * seconds * k
        self._imp_j += max(import_w, 0.0) * seconds * k
        n_exp, self._exp_j = divmod(self._exp_j, 3600.0)
        n_imp, self._imp_j = divmod(self._imp_j, 3600.0)
        self.mint.pulse_import(int(n_imp))
        self.mint.pulse_export(int(n_exp))

    def take_records(self) -> list[SignedRecord]:
        out, self.mint.records = self.mint.records, []
        return out
