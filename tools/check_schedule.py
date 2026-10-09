#!/usr/bin/env python3
"""Executable spec of the EC-MINT1 watt-hour schedule. Mirrors ec_mint1_schedule.v."""


def step(r, w, tokens, pulses):
    mints = []
    for _ in range(pulses):
        w += 1
        if r >= 999:
            r = 0
            tokens += 1
            mints.append(tokens)
        else:
            r += 1
    return r, w, tokens, mints


def main():
    r, w, t, m = step(0, 0, 0, 999)
    assert (r, w, t, m) == (999, 999, 0, []), (r, w, t, m)
    r, w, t, m = step(0, 0, 0, 1000)
    assert (r, w, t, len(m)) == (0, 1000, 1, 1), (r, w, t, m)
    r, w, t, m = step(0, 0, 0, 1001)
    assert (r, t) == (1, 1), (r, t)
    r, w, t, m = step(0, 0, 0, 2500)
    assert (r, t) == (500, 2), (r, t)
    # Splitting an interval must not mint extra tokens.
    r, w, t, _ = step(0, 0, 0, 400)
    r, w, t, m2 = step(r, w, t, 600)
    assert t == 1 and r == 0 and m2 == [1]
    print("PASS schedule: 1000 Wh -> 1 token, residual chain holds across splits")


if __name__ == "__main__":
    main()
