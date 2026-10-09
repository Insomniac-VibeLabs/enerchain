"""ML-DSA (FIPS 204) signatures and SHA-384 hashing.

The meter key is ML-DSA-44 by default (2420-byte signature). If the signer
part only offers ML-DSA-87, the meter is certified with that algorithm and
the ledger verifies with it; the record format does not change.
Account and validator keys are ML-DSA-65.

The implementation is the pure-Python ``dilithium-py`` package. It is fine
for a development network and for tests. It is not constant-time and must
not hold keys that protect value.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from dilithium_py.ml_dsa import ML_DSA_44, ML_DSA_65, ML_DSA_87

ALGS = {"ML-DSA-44": ML_DSA_44, "ML-DSA-65": ML_DSA_65, "ML-DSA-87": ML_DSA_87}
SIG_LEN = {"ML-DSA-44": 2420, "ML-DSA-65": 3309, "ML-DSA-87": 4627}
PK_LEN = {"ML-DSA-44": 1312, "ML-DSA-65": 1952, "ML-DSA-87": 2592}
METER_ALG = "ML-DSA-44"
ACCOUNT_ALG = "ML-DSA-65"


def _alg(name: str):
    try:
        return ALGS[name]
    except KeyError:
        raise ValueError(f"unknown algorithm {name}") from None


def keygen(alg: str = ACCOUNT_ALG, seed: bytes | None = None) -> tuple[bytes, bytes]:
    """Return (public key, secret key). A 32-byte seed makes it repeatable."""
    a = _alg(alg)
    if seed is not None:
        return a.key_derive(seed)
    return a.keygen()


def sign(alg: str, sk: bytes, msg: bytes, ctx: bytes = b"") -> bytes:
    return _alg(alg).sign(sk, msg, ctx=ctx)


def verify(alg: str, pk: bytes, msg: bytes, sig: bytes, ctx: bytes = b"") -> bool:
    if len(sig) != SIG_LEN[alg] or len(pk) != PK_LEN[alg]:
        return False
    try:
        return bool(_alg(alg).verify(pk, msg, sig, ctx=ctx))
    except Exception:
        return False


def sha384(data: bytes) -> bytes:
    return hashlib.sha384(data).digest()


def canonical(obj: Any) -> bytes:
    """Deterministic JSON: sorted keys, no spaces, bytes as hex strings."""

    def enc(o: Any) -> Any:
        if isinstance(o, (bytes, bytearray)):
            return o.hex()
        if isinstance(o, dict):
            return {str(k): enc(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [enc(v) for v in o]
        return o

    return json.dumps(enc(obj), sort_keys=True, separators=(",", ":")).encode()


def address(pk: bytes) -> str:
    """Account address: 'ec' + the first 20 bytes of SHA-384(public key), hex."""
    return "ec" + sha384(pk)[:20].hex()
