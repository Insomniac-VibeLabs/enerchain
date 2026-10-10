"""Meter and pair certification, revocation, rebinding and attestation.

A meter enters the ledger only through a certificate approved by at least
``k`` of the ``n`` certifier keys named in genesis. No single organization
can certify a meter alone, and a manufacturer's signature alone mints
nothing (docs/governance.md). Genesis also labels every certifier with a
sector, and no sector may hold ``k`` keys, so a grid operator (or any one
industry) can never approve on its own.

A pair binds one GEN meter (generator terminals) and one GRID meter (the
point of connection to the grid) to one beneficiary account. Issuance for
the pair is min(tokens_GEN, tokens_GRID): both meters must agree that the
energy was generated and that it left the site. A pair may also bind a LOAD
meter on the site's own consumption; it mints nothing, but it lets the
ledger check GEN = GRID + LOAD within a stated loss allowance, which is how
energy taken between the GEN and GRID meters shows up (docs/grid-operator.md).

Every certificate body below is what k certifiers sign.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from . import crypto
from .record import ROLE_GEN, ROLE_GRID, ROLE_LOAD

CERT_CTX = b"enerchain/v0.0.1/cert"

# A revocation names one of these. Free text is not a reason.
REASONS = ("seal_broken", "metrology_fault", "key_compromise",
           "decommissioned", "misinstalled")

# Certifier sectors. Genesis refuses a set in which one sector holds k keys.
SECTORS = ("metrology", "grid_operator", "consumer", "manufacturer", "other")

# Attestations release escrowed credit for one of these causes.
ATTEST_REASONS = ("outage", "balance")

EVIDENCE_LEN = 48   # SHA-384 of the evidence file
DEFAULT_LOSS_PPM = 20000   # 2 % of GEN: cable and inverter-to-meter losses


@dataclass(frozen=True)
class MeterCert:
    meter_id: int
    role: int
    alg: str
    pk: bytes          # meter key: signs token records
    tamper_pk: bytes   # tamper key: signs the one tamper record after a wipe
    cal_crc: int
    image_hash: bytes  # SHA-384 of the QS7001 image the keys were made under

    def body(self) -> bytes:
        return crypto.canonical({"kind": "meter", **asdict(self)})


@dataclass(frozen=True)
class PairCert:
    pair_id: int
    gen_id: int
    grid_id: int
    beneficiary: str
    load_id: int = 0                  # 0: no LOAD meter, no balance check
    loss_ppm: int = DEFAULT_LOSS_PPM  # allowed GEN - GRID - LOAD, per million of GEN
    site_hash: bytes = bytes(EVIDENCE_LEN)  # SHA-384 of the approved single-line
                                            # diagram and installation record

    def body(self) -> bytes:
        return crypto.canonical({"kind": "pair", **asdict(self)})


@dataclass(frozen=True)
class Revocation:
    meter_id: int
    reason: str          # one of REASONS
    effective_seq: int   # records with seq <= this are still accepted
    evidence: bytes      # SHA-384 of the evidence file

    def body(self) -> bytes:
        return crypto.canonical({"kind": "revoke", **asdict(self)})


@dataclass(frozen=True)
class PairRebind:
    """Replace a pair's revoked or wiped meter with a newly certified one."""
    pair_id: int
    old_id: int
    new_id: int

    def body(self) -> bytes:
        return crypto.canonical({"kind": "rebind", **asdict(self)})


@dataclass(frozen=True)
class Attestation:
    """Release escrowed tokens to a pair: energy its GEN meter counted that
    no GRID meter could (an outage), or that a balance flag shows went
    missing between the meters. Capped by the ledger; see ledger.claimable."""
    pair_id: int
    tokens: int
    reason: str          # one of ATTEST_REASONS
    evidence: bytes      # SHA-384 of the evidence file
    nonce: int           # the pair's next attestation number; no replay

    def body(self) -> bytes:
        return crypto.canonical({"kind": "attest", **asdict(self)})


class Certifier:
    """One certifier key. In genesis these are named, independent bodies."""

    def __init__(self, seed: bytes | None = None) -> None:
        self.pk, self._sk = crypto.keygen(crypto.ACCOUNT_ALG, seed)

    def approve(self, body: bytes) -> tuple[bytes, bytes]:
        return self.pk, crypto.sign(crypto.ACCOUNT_ALG, self._sk, body, CERT_CTX)


def count_approvals(body: bytes, approvals: list[tuple[bytes, bytes]],
                    certifiers: list[bytes]) -> int:
    """Number of distinct genesis certifiers that signed body."""
    seen = set()
    for pk, sig in approvals:
        if pk in certifiers and pk not in seen and crypto.verify(
                crypto.ACCOUNT_ALG, pk, body, sig, CERT_CTX):
            seen.add(pk)
    return len(seen)


def approvals_ok(body: bytes, approvals: list[tuple[bytes, bytes]],
                 certifiers: list[bytes], k: int) -> bool:
    """True if at least k distinct genesis certifiers signed body."""
    return count_approvals(body, approvals, certifiers) >= k


def check_sectors(sectors: list[str], k: int) -> None:
    """No sector may hold k keys: none can approve alone."""
    for s in set(sectors):
        if sectors.count(s) >= k:
            raise ValueError(f"sector {s!r} holds {sectors.count(s)} certifier keys; "
                             f"it must hold fewer than k = {k}")


def check_meter_cert(c: MeterCert) -> None:
    if c.role not in (ROLE_GEN, ROLE_GRID, ROLE_LOAD):
        raise ValueError("role must be GEN, GRID or LOAD")
    if c.alg not in ("ML-DSA-44", "ML-DSA-87"):
        raise ValueError("meter algorithm must be ML-DSA-44 or ML-DSA-87")
    if len(c.pk) != crypto.PK_LEN[c.alg] or len(c.tamper_pk) != crypto.PK_LEN[c.alg]:
        raise ValueError("public key length")
    if c.pk == c.tamper_pk:
        raise ValueError("the tamper key must differ from the meter key")
    if not 0 <= c.cal_crc < 1 << 16 or not 0 <= c.meter_id < 1 << 32:
        raise ValueError("meter id or calibration CRC out of range")
