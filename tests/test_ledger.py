"""Ledger: certification, the pair issuance rule, transfers and blocks."""

import copy

import pytest

from enerchain import crypto
from enerchain.ledger import (BLOCK_BYTES, Ledger, LedgerError, cert_tx, issuance_tx,
                              make_genesis)
from enerchain.meter import EcMint1, Fram, SignerOracle, calibration_image
from enerchain.record import ROLE_GEN, ROLE_GRID, MeterRecord
from enerchain.registry import Certifier, MeterCert, PairCert, Revocation
from enerchain.wallet import Wallet

IMG = b"\x00" * 48


class Net:
    def __init__(self, k=2):
        self.val_pk, self.val_sk = crypto.keygen(crypto.ACCOUNT_ALG)
        self.certs = [Certifier() for _ in range(3)]
        self.ledger = Ledger(make_genesis("test", [self.val_pk],
                                          [c.pk for c in self.certs], k))
        self.t = 1

    def approve(self, body, n=2):
        return [c.approve(body) for c in self.certs[:n]]

    def block(self, txs):
        b = self.ledger.build_block(txs, self.val_sk, self.t)
        self.t += 1
        self.ledger.add_block(b)
        return b

    def meter(self, mid, role, q=1000, every=1):
        s = SignerOracle()
        s.personalize(mid, role)
        m = EcMint1(fram=Fram(), signer=s, q=q, sign_every=every)
        m.provision(calibration_image(mid, role, [b"\x01"]))
        c = MeterCert(mid, role, "ML-DSA-44", s.pk, m.cal_crc, IMG)
        return m, cert_tx("meter_cert", c, self.approve(c.body()))

    def pair(self, pid, gen, grid, who):
        c = PairCert(pid, gen, grid, who)
        return cert_tx("pair_cert", c, self.approve(c.body()))


@pytest.fixture
def setup():
    net = Net()
    owner = Wallet.create()
    gen, tg = net.meter(11, ROLE_GEN)
    grid, tr = net.meter(12, ROLE_GRID)
    b = net.block([tg, tr, net.pair(1, 11, 12, owner.address)])
    assert len(b["txs"]) == 3
    return net, owner, gen, grid


def recs(m):
    out = [issuance_tx(r.record, r.signature) for r in m.records]
    m.records = []
    return out


def test_one_meter_alone_mints_nothing(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(5000)
    net.block(recs(gen))
    assert net.ledger.balance(owner.address) == 0


def test_pair_mints_minimum_of_both(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(5000)
    grid.pulse_export(3000)
    net.block(recs(gen) + recs(grid))
    assert net.ledger.balance(owner.address) == 3000
    grid.pulse_export(4000)
    net.block(recs(grid))
    assert net.ledger.balance(owner.address) == 5000
    assert net.ledger.state["supply_wh"] == 5000


def test_records_out_of_step_converge(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(2000)
    g1 = recs(gen)
    gen.pulse_export(2000)
    g2 = recs(gen)
    grid.pulse_export(4000)
    # Grid first, then only the latest GEN record; the first GEN record is lost.
    net.block(recs(grid) + g2[-1:])
    assert net.ledger.balance(owner.address) == 4000
    # The lost, older record is now stale and is refused.
    b = net.block(g1)
    assert b["txs"] == []


def test_replay_and_tamper_refused(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(1000)
    tx = recs(gen)[0]
    net.block([tx])
    with pytest.raises(LedgerError, match="seq"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), tx)
    raw = bytearray(bytes.fromhex(tx["record"]))
    raw[27] += 5                                    # more tokens
    bad = {"type": "issuance", "record": raw.hex(), "sig": tx["sig"]}
    with pytest.raises(LedgerError, match="signature"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), bad)


def test_wrong_calibration_refused(setup):
    net, owner, gen, grid = setup
    # A record correctly signed but over a different calibration image.
    rec = MeterRecord(11, ROLE_GEN, 99, 5000, 0, 5, gen.cal_crc ^ 1).pack()
    sig = crypto.sign("ML-DSA-44", gen.signer._sk, rec)
    with pytest.raises(LedgerError, match="calibration"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), issuance_tx(rec, sig))


def test_tokens_above_energy_refused(setup):
    net, owner, gen, grid = setup
    rec = MeterRecord(11, ROLE_GEN, 99, 5000, 0, 6, gen.cal_crc).pack()
    sig = crypto.sign("ML-DSA-44", gen.signer._sk, rec)
    with pytest.raises(LedgerError, match="exceed"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), issuance_tx(rec, sig))


def test_certification_needs_k_approvals():
    net = Net(k=2)
    s = SignerOracle()
    s.personalize(5, ROLE_GEN)
    c = MeterCert(5, ROLE_GEN, "ML-DSA-44", s.pk, 0, IMG)
    one = cert_tx("meter_cert", c, net.approve(c.body(), n=1))
    with pytest.raises(LedgerError, match="approvals"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), one)
    # The same certifier twice is still one approval.
    twice = cert_tx("meter_cert", c, net.approve(c.body(), n=1) * 2)
    with pytest.raises(LedgerError, match="approvals"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), twice)
    outsider = Certifier()
    mixed = cert_tx("meter_cert", c, net.approve(c.body(), n=1) + [outsider.approve(c.body())])
    with pytest.raises(LedgerError, match="approvals"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), mixed)


def test_pair_needs_gen_and_grid(setup):
    net, owner, gen, grid = setup
    g2, t2 = net.meter(21, ROLE_GEN)
    g3, t3 = net.meter(22, ROLE_GEN)
    net.block([t2, t3])
    with pytest.raises(LedgerError, match="GEN and one GRID"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), net.pair(2, 21, 22, owner.address))
    with pytest.raises(LedgerError, match="at most one pair"):
        net.ledger.apply_tx(copy.deepcopy(net.ledger.state), net.pair(3, 21, 12, owner.address))


def test_revoked_meter_stops_minting(setup):
    net, owner, gen, grid = setup
    r = Revocation(12, "seal broken")
    net.block([cert_tx("revoke", r, net.approve(r.body()))])
    gen.pulse_export(2000)
    grid.pulse_export(2000)
    net.block(recs(gen) + recs(grid))
    assert net.ledger.balance(owner.address) == 0


def test_transfers(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(3000)
    grid.pulse_export(3000)
    net.block(recs(gen) + recs(grid))
    bob = Wallet.create()
    t1 = owner.transfer("test", bob.address, 1250, 1)
    net.block([t1])
    assert net.ledger.balance(bob.address) == 1250
    assert net.ledger.balance(owner.address) == 1750
    st = copy.deepcopy(net.ledger.state)
    with pytest.raises(LedgerError, match="nonce"):
        net.ledger.apply_tx(st, t1)                               # replay
    with pytest.raises(LedgerError, match="insufficient"):
        net.ledger.apply_tx(st, owner.transfer("test", bob.address, 10_000, 2))
    with pytest.raises(LedgerError, match="signature"):
        net.ledger.apply_tx(st, owner.transfer("other-chain", bob.address, 1, 2))
    forged = dict(owner.transfer("test", bob.address, 1, 2), pk=bob.pk.hex())
    with pytest.raises(LedgerError, match="address"):
        net.ledger.apply_tx(st, forged)


def test_block_rules(setup):
    net, owner, gen, grid = setup
    other_pk, other_sk = crypto.keygen(crypto.ACCOUNT_ALG)
    b = net.ledger.build_block([], other_sk, net.t)
    with pytest.raises(LedgerError, match="proposer"):
        net.ledger.add_block(b)
    b = net.ledger.build_block([], net.val_sk, net.t)
    b2 = copy.deepcopy(b)
    b2["header"]["state_root"] = "00" * 48
    with pytest.raises(LedgerError):
        net.ledger.add_block(b2)
    net.ledger.add_block(b)
    with pytest.raises(LedgerError, match="height"):
        net.ledger.add_block(b)


def test_replay_from_genesis_reaches_same_state(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(2000)
    grid.pulse_export(2000)
    net.block(recs(gen) + recs(grid))
    fresh = Ledger(net.ledger.genesis)
    fresh.replay(net.ledger.blocks)
    assert fresh.state == net.ledger.state


def test_block_cap_constant():
    assert BLOCK_BYTES == 1 << 20
