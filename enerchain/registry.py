"""Meter and pair certification.

A meter enters the ledger only through a certificate approved by at least
``k`` of the ``n`` certifier keys named in genesis. No single organization
can certify a meter alone, and a manufacturer's signature alone mints
nothing (docs/governance.md).

A pair binds one GEN meter (generator terminals) and one GRID meter (the
point of connection to the grid) to one beneficiary account. Issuance for
the pair is min(tokens_GEN, tokens_GRID): both meters must agree that the
energy was generated and that it left the site.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

from . import crypto
from .record import ROLE_GEN, ROLE_GRID

CERT_CTX = b"enerchain/v0.0.1/cert"


@dataclass(frozen=True)
class MeterCert:
    meter_id: int
    role: int
    alg: str
    pk: bytes
    cal_crc: int
    image_hash: bytes  # SHA-384 of the QS7001 image the key was made under

    def body(self) -> bytes:
        return crypto.canonical({"kind": "meter", **asdict(self)})


@dataclass(frozen=True)
class PairCert:
    pair_id: int
    gen_id: int
    grid_id: int
    beneficiary: str

    def body(self) -> bytes:
        return crypto.canonical({"kind": "pair", **asdict(self)})


@dataclass(frozen=True)
class Revocation:
    meter_id: int
    reason: str

    def body(self) -> bytes:
        return crypto.canonical({"kind": "revoke", **asdict(self)})


class Certifier:
    """One certifier key. In genesis these are named, independent bodies."""

    def __init__(self, seed: bytes | None = None) -> None:
        self.pk, self._sk = crypto.keygen(crypto.ACCOUNT_ALG, seed)

    def approve(self, body: bytes) -> tuple[bytes, bytes]:
        return self.pk, crypto.sign(crypto.ACCOUNT_ALG, self._sk, body, CERT_CTX)


def approvals_ok(body: bytes, approvals: list[tuple[bytes, bytes]],
                 certifiers: list[bytes], k: int) -> bool:
    """True if at least k distinct genesis certifiers signed body."""
    seen = set()
    for pk, sig in approvals:
        if pk in certifiers and pk not in seen and crypto.verify(
                crypto.ACCOUNT_ALG, pk, body, sig, CERT_CTX):
            seen.add(pk)
    return len(seen) >= k


def check_meter_cert(c: MeterCert) -> None:
    if c.role not in (ROLE_GEN, ROLE_GRID):
        raise ValueError("role must be GEN or GRID")
    if c.alg not in ("ML-DSA-44", "ML-DSA-87"):
        raise ValueError("meter algorithm must be ML-DSA-44 or ML-DSA-87")
    if len(c.pk) != crypto.PK_LEN[c.alg]:
        raise ValueError("public key length")
    if not 0 <= c.cal_crc < 1 << 16 or not 0 <= c.meter_id < 1 << 32:
        raise ValueError("meter id or calibration CRC out of range")
