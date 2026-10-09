"""The signed meter record and the EC-MINT1 UART frame.

Record, 32 bytes, big-endian fields (hardware/asic/spec.md):

====== ===== ==================================================
offset bytes field
====== ===== ==================================================
0      4     meter id
4      1     version (high nibble, 1) and role (low nibble)
5      1     accuracy class tag, 0x22
6      4     seq, strictly increasing per meter
10     6     e_exp, cumulative export watt-hours
16     6     e_imp, cumulative import watt-hours
22     6     tokens, cumulative, from the net-export schedule
28     2     CRC-16/CCITT-FALSE of the factory calibration image
30     2     zero
====== ===== ==================================================

UART frame: ``EC 01``, the record, then the ML-DSA signature.
"""

from __future__ import annotations

from dataclasses import dataclass

RECORD_LEN = 32
VERSION = 1
CLASS_TAG = 0x22
ROLE_GEN = 1
ROLE_GRID = 2
ROLES = {ROLE_GEN: "GEN", ROLE_GRID: "GRID"}
FRAME_HEADER = b"\xEC\x01"
MAX48 = (1 << 48) - 1


def crc8(data: bytes, crc: int = 0) -> int:
    """CRC-8, polynomial 0x07, initial value 0 (the SPI record check)."""
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def crc16(data: bytes, crc: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE, polynomial 0x1021, initial value 0xFFFF."""
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


class RecordError(ValueError):
    pass


@dataclass(frozen=True)
class MeterRecord:
    meter_id: int
    role: int
    seq: int
    e_exp: int
    e_imp: int
    tokens: int
    cal_crc: int
    version: int = VERSION
    class_tag: int = CLASS_TAG

    def pack(self) -> bytes:
        for name, v, bits in (
            ("meter_id", self.meter_id, 32), ("seq", self.seq, 32),
            ("e_exp", self.e_exp, 48), ("e_imp", self.e_imp, 48),
            ("tokens", self.tokens, 48), ("cal_crc", self.cal_crc, 16),
        ):
            if not 0 <= v < (1 << bits):
                raise RecordError(f"{name} out of range")
        if not (0 <= self.role < 16 and 0 <= self.version < 16):
            raise RecordError("role or version out of range")
        return (
            self.meter_id.to_bytes(4, "big")
            + bytes([(self.version << 4) | self.role, self.class_tag])
            + self.seq.to_bytes(4, "big")
            + self.e_exp.to_bytes(6, "big")
            + self.e_imp.to_bytes(6, "big")
            + self.tokens.to_bytes(6, "big")
            + self.cal_crc.to_bytes(2, "big")
            + b"\x00\x00"
        )

    @classmethod
    def unpack(cls, raw: bytes) -> "MeterRecord":
        if len(raw) != RECORD_LEN:
            raise RecordError("record must be 32 bytes")
        if raw[30:32] != b"\x00\x00":
            raise RecordError("reserved bytes must be zero")
        return cls(
            meter_id=int.from_bytes(raw[0:4], "big"),
            version=raw[4] >> 4,
            role=raw[4] & 0x0F,
            class_tag=raw[5],
            seq=int.from_bytes(raw[6:10], "big"),
            e_exp=int.from_bytes(raw[10:16], "big"),
            e_imp=int.from_bytes(raw[16:22], "big"),
            tokens=int.from_bytes(raw[22:28], "big"),
            cal_crc=int.from_bytes(raw[28:30], "big"),
        )


def parse_frame(frame: bytes, sig_len: int) -> tuple[bytes, bytes]:
    """Split an EC-MINT1 UART frame into (record bytes, signature)."""
    if len(frame) != 2 + RECORD_LEN + sig_len:
        raise RecordError(f"frame must be {2 + RECORD_LEN + sig_len} bytes")
    if frame[:2] != FRAME_HEADER:
        raise RecordError("bad frame header")
    return frame[2:2 + RECORD_LEN], frame[2 + RECORD_LEN:]
