"""System tests: a simulated site on the devnet, the CLI, and the RTL check."""

import os
import shutil
import subprocess
import sys

import pytest

from enerchain import cli
from enerchain.ledger import cert_tx, issuance_tx
from enerchain.node import Devnet
from enerchain.registry import MeterCert, PairCert
from enerchain.sim import Site
from enerchain.wallet import Wallet

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_site(tmp_path, loop_w):
    net = Devnet.init(str(tmp_path / f"net{int(loop_w)}"), n_validators=2)
    owner = Wallet.create()
    site = Site.new(1, 2, battery_loop_w=loop_w)
    for m in (site.gen, site.grid):
        c = MeterCert(m.mint.meter_id, m.mint.role, m.alg, m.pk, m.cal_crc, b"\x00" * 48)
        net.submit(cert_tx("meter_cert", c, net.approve(c.body())))
    p = PairCert(1, 1, 2, owner.address)
    net.submit(cert_tx("pair_cert", p, net.approve(p.body())))
    net.produce(now=1)
    site.run_days(2)
    for m in (site.gen, site.grid):
        for r in m.take_records():
            net.submit(issuance_tx(r.record, r.signature))
    net.produce(now=2)
    # A second node replaying the files reaches the same state.
    again = Devnet(net.path)
    assert again.ledger.state == net.ledger.state
    return net.ledger.balance(owner.address), site


def test_battery_loop_mints_nothing(tmp_path):
    base, s0 = run_site(tmp_path, 0.0)
    looped, s1 = run_site(tmp_path, 3000.0)
    assert base > 0
    assert looped == base
    assert s1.grid.mint.e_imp > s0.grid.mint.e_imp     # the loop was real


def test_minted_never_exceeds_generation(tmp_path):
    bal, site = run_site(tmp_path, 0.0)
    assert bal <= site.log["gen_wh"]
    assert bal <= site.grid.mint.e_exp


def test_cli_demo_and_version(capsys):
    assert cli.main(["demo", "--days", "1"]) == 0
    out = capsys.readouterr().out
    assert "replayed record included: 0" in out
    with pytest.raises(SystemExit):
        cli.main(["--version"])


def test_cli_devnet_wallet_transfer(tmp_path, capsys):
    d = str(tmp_path / "dn")
    assert cli.main(["devnet", "init", d]) == 0
    w = str(tmp_path / "w.json")
    assert cli.main(["wallet", "new", w]) == 0
    addr = capsys.readouterr().out.split()[-1]
    assert cli.main(["balance", d, addr]) == 0
    assert "0 Wh" in capsys.readouterr().out
    # No balance: the transfer is queued but never included.
    assert cli.main(["transfer", d, w, addr, "5"]) == 0
    assert cli.main(["devnet", "produce", d]) == 0
    assert "0 tx" in capsys.readouterr().out.splitlines()[-1]
    assert cli.main(["devnet", "show", d]) == 0


@pytest.mark.skipif(not shutil.which("iverilog"), reason="iverilog not installed")
def test_rtl_matches_model():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools/check_rtl.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
