#!/usr/bin/env python3
"""Run the EC-MINT1 RTL testbench and compare every signed record with the
Python reference model (enerchain.meter) fed the same events.

Needs Icarus Verilog (iverilog, vvp). Exit status 0 on a byte-exact match.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from enerchain.meter import EcMint1, Fram, SignerOracle, calibration_image  # noqa: E402

RTL = ["ec_mint1.v", "ec_mint1_schedule.v", "spi_byte.v", "uart_tx.v"]
TB = ["models.v", "tb_ec_mint1.v"]


class StandInSigner(SignerOracle):
    """The testbench signer's rules with no key: only the record matters here."""

    def __init__(self) -> None:
        super().__init__()
        self.personalized = True
        self.tamper_used = False
        self.meter_id, self.role = 0x42, 2

    def sign(self, raw: bytes):
        seq = int.from_bytes(raw[6:10], "big")
        if self.wiped or seq <= self.last[0] or raw[30] != 0:
            return None
        self.last = (seq,) + self.last[1:]
        return b""

    def sign_tamper(self, raw: bytes):
        seq = int.from_bytes(raw[6:10], "big")
        if not self.wiped or self.tamper_used or seq <= self.last[0] or raw[30] != 1:
            return None
        self.tamper_used = True
        self.last = (seq,) + self.last[1:]
        return b""


def model_records() -> list[str]:
    """The testbench scenario, step for step (hardware/asic/tb/tb_ec_mint1.v)."""
    signer = StandInSigner()
    m = EcMint1(fram=Fram(), signer=signer, q=10, sign_every=2, resend_s=20)
    m.pulse_export(30)                                  # before provisioning
    m.provision(calibration_image(0x42, 2, [b"\x11\x22\x33", b"\x44\x55"]))
    m.pulse_export(20)
    m.pulse_import(15)
    m.pulse_export(14)
    m.pulse_export(21)
    m.pulse_export(5)
    m.power_cycle()
    m.pulse_export(15)
    m.pulse_export(1, persist=False)                    # torn FRAM write
    m.power_cycle()
    signer.last = (4,) + signer.last[1:]
    m.pulse_export(20)                                  # seq 4 refused
    m.pulse_export(20)                                  # seq 5
    m.idle(20)                                          # re-send, seq 6
    m.pulse_export(7)
    m.zeroize()                                         # tamper record, seq 7
    m.pulse_export(40)
    return [r.record.hex() for r in m.records]


def rtl_records() -> list[str]:
    if not (shutil.which("iverilog") and shutil.which("vvp")):
        raise SystemExit("SKIP: iverilog/vvp not installed")
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "sim")
        srcs = [os.path.join(ROOT, "hardware/asic/rtl", f) for f in RTL]
        srcs += [os.path.join(ROOT, "hardware/asic/tb", f) for f in TB]
        subprocess.run(["iverilog", "-g2012", "-o", out, *srcs], check=True)
        run = subprocess.run(["vvp", out], check=True, capture_output=True, text=True)
    lines = run.stdout.splitlines()
    if not any(line.startswith("PASS ec_mint1") for line in lines):
        print(run.stdout)
        raise SystemExit("FAIL: RTL testbench did not pass")
    return [line.split()[1] for line in lines if line.startswith("REC ")]


def main() -> int:
    want = model_records()
    got = rtl_records()
    if want != got:
        print("FAIL: RTL and model records differ")
        for i in range(max(len(want), len(got))):
            print(" model", want[i] if i < len(want) else "-")
            print(" rtl  ", got[i] if i < len(got) else "-")
        return 1
    print(f"PASS rtl == model: {len(got)} signed records byte-exact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
