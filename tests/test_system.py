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


def run_site(tmp_path, loop_w, load_id=0, siphon_w=0.0, days=2):
    net = Devnet.init(str(tmp_path / f"net{int(loop_w)}-{load_id}-{int(siphon_w)}"),
                      n_validators=2)
    owner = Wallet.create()
    site = Site.new(1, 2, load_id, battery_loop_w=loop_w, siphon_w=siphon_w)
    for m in site.meters:
        c = MeterCert(m.mint.meter_id, m.mint.role, m.alg, m.pk, m.tamper_pk, m.cal_crc,
                      b"\x00" * 48)
        net.submit(cert_tx("meter_cert", c, net.approve(c.body())))
    p = PairCert(1, 1, 2, owner.address, load_id)
    net.submit(cert_tx("pair_cert", p, net.approve(p.body())))
    net.produce(now=1)
    site.run_days(days)
    for r in site.take_records():
        net.submit(issuance_tx(r.record, r.signature))
    net.produce(now=2)
    # A second node replaying the files reaches the same state.
    again = Devnet(net.path)
    assert again.ledger.state == net.ledger.state
    return net.ledger.balance(owner.address), site, net


def test_battery_loop_mints_nothing(tmp_path):
    base, s0, _ = run_site(tmp_path, 0.0)
    looped, s1, _ = run_site(tmp_path, 3000.0)
    assert base > 0
    assert looped == base
    assert s1.grid.mint.e_imp > s0.grid.mint.e_imp     # the loop was real


def test_minted_never_exceeds_generation(tmp_path):
    bal, site, _ = run_site(tmp_path, 0.0)
    assert bal <= site.log["gen_wh"]
    assert bal <= site.grid.mint.e_exp


def test_honest_load_site_balances(tmp_path):
    for loop_w in (0.0, 3000.0):
        bal, site, net = run_site(tmp_path, loop_w, load_id=3, days=3)
        rep = net.ledger.pair_report(1)
        assert rep["tokens"]["load"] > 0
        assert not rep["balance"]["flag"], rep["balance"]


def test_siphon_before_the_grid_meter_is_flagged(tmp_path):
    bal, site, net = run_site(tmp_path, 0.0, load_id=3, siphon_w=300.0, days=3)
    rep = net.ledger.pair_report(1)
    assert rep["balance"]["flag"]
    # The flag bounds the missing energy from below; it never over-states it.
    assert 0 < rep["claimable"]["balance"] * 1000 <= site.log["siphon_wh"]


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
    assert cli.main(["pair", "report", d, "1"]) == 1
    assert "unknown pair" in capsys.readouterr().out
    assert cli.main(["pair", "request", d, w, "1", "2"]) == 0
    assert cli.main(["pair", "contest", d, w, "2"]) == 0
    assert cli.main(["devnet", "produce", d]) == 0
    assert "0 tx" in capsys.readouterr().out.splitlines()[-1]   # meters 1, 2 unknown


def test_cli_frame_submit(tmp_path, capsys):
    from enerchain.meter import EnergyMeter
    from enerchain.record import ROLE_GEN
    d = str(tmp_path / "dn")
    assert cli.main(["devnet", "init", d]) == 0
    em = EnergyMeter(5, ROLE_GEN)
    em.step(1000.0, 0.0, 3600)
    sr = em.take_records()[0]
    frame = (b"\xEC\x01" + sr.record + sr.signature).hex()
    assert cli.main(["frame", "verify", "--pk", em.pk.hex(), frame]) == 0
    assert cli.main(["frame", "submit", d, frame]) == 0
    assert "queued issuance" in capsys.readouterr().out
    assert cli.main(["frame", "submit", d, "00"]) == 2


def test_cli_demo_siphon(capsys):
    assert cli.main(["demo", "--days", "2", "--siphon-w", "300"]) == 0
    assert "flag RAISED" in capsys.readouterr().out


@pytest.mark.skipif(not shutil.which("iverilog"), reason="iverilog not installed")
def test_rtl_matches_model():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools/check_rtl.py")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
