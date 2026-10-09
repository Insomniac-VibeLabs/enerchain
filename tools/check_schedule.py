#!/usr/bin/env python3
"""Executable spec of the EC-MINT1 schedule, v0.0.1. Mirrors
hardware/asic/rtl/ec_mint1_schedule.v. No dependencies beyond Python 3.

Rule: credit = e_exp - e_imp - tokens*Q. An export pulse adds one; at Q a
token is minted and credit returns to zero. An import pulse subtracts one.
tokens = floor(max over time of (e_exp - e_imp) / Q).
"""

Q = 1000


class Schedule:
    def __init__(self) -> None:
        self.e_exp = self.e_imp = self.tokens = self.credit = 0

    def exp(self, n: int) -> None:
        for _ in range(n):
            self.e_exp += 1
            if self.credit == Q - 1:
                self.credit = 0
                self.tokens += 1
            else:
                self.credit += 1

    def imp(self, n: int) -> None:
        for _ in range(n):
            self.e_imp += 1
            self.credit -= 1


def main() -> None:
    s = Schedule()
    s.exp(999)
    assert s.tokens == 0
    s.exp(1)
    assert (s.tokens, s.credit) == (1, 0)

    # Splitting an interval must not mint extra tokens.
    a = Schedule()
    a.exp(400)
    a.exp(600)
    assert a.tokens == 1 and a.credit == 0

    # Import cancels export: 500 in, 1500 out is a net 1000 -> one token.
    b = Schedule()
    b.imp(500)
    b.exp(1500)
    assert b.tokens == 1, b.tokens

    # A grid -> battery -> grid loop mints nothing beyond the real export.
    c = Schedule()
    c.exp(2500)          # real export
    c.imp(3000)          # battery charges from the grid
    c.exp(3000)          # battery pushes the same energy back
    assert c.tokens == 2, c.tokens

    # Invariant: tokens = floor(max net / Q).
    d = Schedule()
    best = 0
    for step, n in enumerate([700, -300, 900, -2000, 2600, 10, -5, 1200]):
        d.exp(n) if n > 0 else d.imp(-n)
        best = max(best, d.e_exp - d.e_imp)
        assert d.tokens == best // Q, (step, d.tokens, best)
        assert d.credit == d.e_exp - d.e_imp - d.tokens * Q
    print("PASS schedule: 1000 net-export Wh -> 1 token, splits and loops mint nothing extra")


if __name__ == "__main__":
    main()
