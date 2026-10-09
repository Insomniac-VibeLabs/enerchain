"""Enerchain v0.0.1 reference software.

This package is the software half of the design in this repository:

- ``record``   the 32-byte meter record EC-MINT1 builds and the QS7001 signs
- ``meter``    a bit-exact model of EC-MINT1 and the signing oracle, used as a
               meter emulator and to cross-check the RTL
- ``crypto``   ML-DSA (FIPS 204) keys and signatures, SHA-384 hashing
- ``registry`` k-of-n meter and pair certification
- ``ledger``   the issuance rule, transfers, blocks and the chain
- ``wallet``   account keys and addresses
- ``node``     an in-process development network
- ``cli``      the ``enerchain`` command

It is a development network. It is not a production ledger. See
docs/software.md for what v0.0.1 does and does not do.
"""

__version__ = "0.0.1"
