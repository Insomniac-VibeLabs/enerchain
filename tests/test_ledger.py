"""Ledger: certification, the pair issuance rule, transfers and blocks, and
the rules that keep a dishonest grid operator from under-crediting a pair
(docs/grid-operator.md)."""

import copy

import pytest

from enerchain import crypto
from enerchain.ledger import (BLOCK_BYTES, NOTICE_S, SILENT_S, Ledger, LedgerError,
                              cert_tx, frame_tx, issuance_tx, make_genesis)
from enerchain.meter import EcMint1, Fram, SignerOracle, calibration_image
from enerchain.record import (KIND_TAMPER, ROLE_GEN, ROLE_GRID, ROLE_LOAD,
                              MeterRecord)
from enerchain.registry import (Attestation, Certifier, MeterCert, PairCert,
                                PairRebind, Revocation)
from enerchain.wallet import Wallet

IMG = b"\x00" * 48
EVIDENCE = crypto.sha384(b"inspection report")


class Net:
    def __init__(self, k=2):
        self.val_pk, self.val_sk = crypto.keygen(crypto.ACCOUNT_ALG)
        self.certs = [Certifier() for _ in range(3)]
        self.ledger = Ledger(make_genesis("test", [self.val_pk],
                                          [c.pk for c in self.certs], k))
        self.t = 1

    def approve(self, body, n=2):
        return [c.approve(body) for c in self.certs[:n]]

    def block(self, txs, dt=1):
        b = self.ledger.build_block(txs, self.val_sk, self.t)
        self.t += dt
        self.ledger.add_block(b)
        return b

    def meter(self, mid, role, q=1000, every=1):
        s = SignerOracle()
        s.personalize(mid, role)
        m = EcMint1(fram=Fram(), signer=s, q=q, sign_every=every)
        m.provision(calibration_image(mid, role, [b"\x01"]))
        c = MeterCert(mid, role, "ML-DSA-44", s.pk, s.tamper_pk, m.cal_crc, IMG)
        return m, cert_tx("meter_cert", c, self.approve(c.body()))

    def pair(self, pid, gen, grid, who, load=0):
        c = PairCert(pid, gen, grid, who, load)
        return cert_tx("pair_cert", c, self.approve(c.body()))

    def revoke(self, mid, effective_seq, n=3, reason="seal_broken"):
        r = Revocation(mid, reason, effective_seq, EVIDENCE)
        return cert_tx("revoke", r, self.approve(r.body(), n))

    def rebind(self, pid, old, new):
        c = PairRebind(pid, old, new)
        return cert_tx("rebind", c, self.approve(c.body()))

    def attest(self, pid, tokens, reason, nonce):
        c = Attestation(pid, tokens, reason, EVIDENCE, nonce)
        return cert_tx("attest", c, self.approve(c.body()))

    def ok(self, tx):
        """Apply tx to a scratch copy; raise if it would be refused."""
        self.ledger.apply_tx(copy.deepcopy(self.ledger.state), tx)


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
    c = MeterCert(5, ROLE_GEN, "ML-DSA-44", s.pk, s.tamper_pk, 0, IMG)
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
    net.block([net.revoke(12, 0)])
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


# --------------------------------------------------------------------------
# What a dishonest grid operator could try (docs/grid-operator.md)

def test_genesis_refuses_a_sector_that_can_approve_alone():
    pks = [Certifier().pk for _ in range(3)]
    val = crypto.keygen(crypto.ACCOUNT_ALG)[0]
    with pytest.raises(LedgerError, match="grid_operator"):
        make_genesis("t", [val], pks, 2, sectors=["grid_operator", "grid_operator", "consumer"])
    g = make_genesis("t", [val], pks, 2, sectors=["metrology", "grid_operator", "consumer"])
    assert g["k_urgent"] == 3 and g["params"]["notice_s"] == NOTICE_S


def test_revocation_honours_records_built_before_it(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(3000)
    grid.pulse_export(3000)                # GRID records seq 1..3 exist
    held = recs(grid)                      # ...but have not reached the ledger
    net.block([net.revoke(12, effective_seq=3)])
    grid.pulse_export(2000)                # seq 4, 5: built after the revocation
    late = recs(grid)
    net.block(recs(gen) + held + late)
    assert net.ledger.balance(owner.address) == 3000
    st = net.ledger.state["meters"]["12"]
    assert st["last"][0] == 3 and st["revocation"]["status"] == "active"


def test_revocation_needs_a_listed_reason_and_evidence(setup):
    net, owner, gen, grid = setup
    r = Revocation(12, "because", 0, EVIDENCE)
    with pytest.raises(LedgerError, match="reason"):
        net.ok(cert_tx("revoke", r, net.approve(r.body(), 3)))
    r = Revocation(12, "seal_broken", 0, b"\x01")
    with pytest.raises(LedgerError, match="SHA-384"):
        net.ok(cert_tx("revoke", r, net.approve(r.body(), 3)))


def test_k_revocation_waits_out_notice_then_applies(setup):
    net, owner, gen, grid = setup
    net.block([net.revoke(12, effective_seq=0, n=2)])
    rev = net.ledger.state["meters"]["12"]["revocation"]
    assert rev["status"] == "pending"
    gen.pulse_export(2000)
    grid.pulse_export(2000)
    net.block(recs(gen) + recs(grid), dt=NOTICE_S)     # during notice: still credited
    assert net.ledger.balance(owner.address) == 2000
    net.block([])                                       # notice has run out
    assert net.ledger.state["meters"]["12"]["revocation"]["status"] == "active"
    gen.pulse_export(1000)
    grid.pulse_export(1000)
    net.block(recs(gen) + recs(grid))
    assert net.ledger.balance(owner.address) == 2000


def test_beneficiary_contest_stops_a_k_revocation(setup):
    net, owner, gen, grid = setup
    net.block([net.revoke(12, effective_seq=0, n=2)])
    stranger = Wallet.create()
    with pytest.raises(LedgerError, match="account"):
        net.ok(stranger.contest("test", 12))
    net.block([owner.contest("test", 12)], dt=NOTICE_S + 1)
    net.block([])
    assert net.ledger.state["meters"]["12"]["revocation"]["status"] == "contested"
    gen.pulse_export(1000)
    grid.pulse_export(1000)
    net.block(recs(gen) + recs(grid))
    assert net.ledger.balance(owner.address) == 1000
    # A second k-only filing cannot override the contest; k_urgent can.
    with pytest.raises(LedgerError, match="k_urgent"):
        net.ok(net.revoke(12, 1, n=2))
    net.block([net.revoke(12, 1, n=3)])
    assert net.ledger.state["meters"]["12"]["revocation"]["status"] == "active"


def test_tamper_record_marks_wipe_and_mints_nothing(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(2000)
    grid.pulse_export(2000)
    early = recs(grid)                     # seq 1, 2 still in flight
    grid.pulse_export(500)
    grid.zeroize()                         # cover opened under power
    tamper = recs(grid)
    assert len(tamper) == 1
    t = MeterRecord.unpack(bytes.fromhex(tamper[0]["record"]))
    assert t.kind == KIND_TAMPER and t.seq == 3 and t.e_exp == 2500
    net.block(recs(gen) + tamper)
    assert net.ledger.state["meters"]["12"]["wiped"]["seq"] == 3
    assert net.ledger.balance(owner.address) == 0
    net.block(early)                       # built before the wipe: still counts
    assert net.ledger.balance(owner.address) == 2000
    # A "tamper record" signed with a meter key is refused: only the tamper
    # key, which signs once and only after a wipe, can mark a meter wiped.
    raw = MeterRecord(11, ROLE_GEN, 99, 2000, 0, 2, gen.cal_crc, kind=KIND_TAMPER).pack()
    with pytest.raises(LedgerError, match="signature"):
        net.ok(issuance_tx(raw, crypto.sign("ML-DSA-44", gen.signer._sk, raw)))


def test_rebind_replaces_a_wiped_grid_meter_and_keeps_escrow(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(2000)
    grid.pulse_export(2000)
    grid.zeroize()
    net.block(recs(gen) + recs(grid))
    assert net.ledger.balance(owner.address) == 2000
    gen.pulse_export(3000)                 # exported while no GRID meter counts
    net.block(recs(gen))
    rep = net.ledger.pair_report(1)
    assert rep["outage_open"] and rep["claimable"]["outage"] == 3000 // 1000
    new, tn = net.meter(13, ROLE_GRID)
    other, to = net.meter(14, ROLE_GRID)
    with pytest.raises(LedgerError, match="revoked or wiped"):
        net.ok(net.rebind(1, 11, 13))     # GEN 11 is fine; it cannot be swapped
    net.block([tn, to, net.rebind(1, 12, 13)])
    gen.pulse_export(1000)
    new.pulse_export(1000)
    net.block(recs(gen) + recs(new))
    assert net.ledger.balance(owner.address) == 3000     # the new meter counts
    rep = net.ledger.pair_report(1)
    assert not rep["outage_open"] and rep["claimable"]["outage"] == 3
    # Escrow is released only by k certifiers, once, and never above the cap.
    with pytest.raises(LedgerError, match="escrow"):
        net.ok(net.attest(1, 4, "outage", 1))
    a = net.attest(1, 3, "outage", 1)
    net.block([a])
    assert net.ledger.balance(owner.address) == 6000
    with pytest.raises(LedgerError, match="nonce"):
        net.ok(a)
    assert net.ledger.pair_report(1)["claimable"]["outage"] == 0


def test_silent_grid_meter_opens_an_outage(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(1000)
    grid.pulse_export(1000)
    net.block(recs(gen) + recs(grid))
    gen.pulse_export(4000)
    grid.pulse_export(4000)
    withheld = recs(grid)                  # a relay drops the GRID frames
    net.block(recs(gen), dt=SILENT_S + 1)
    net.block([])
    rep = net.ledger.pair_report(1)
    assert rep["outage_open"] and rep["claimable"]["outage"] == 4
    assert net.ledger.balance(owner.address) == 1000
    # The frames turn up (or the daily re-send gets through): the GRID
    # meter's cumulative count covers the silence and the outage closes.
    net.block(withheld[-1:])
    rep = net.ledger.pair_report(1)
    assert not rep["outage_open"] and rep["claimable"]["outage"] == 0
    assert net.ledger.balance(owner.address) == 5000


def test_pair_request_fixes_the_start_while_certifiers_wait(setup):
    net, owner, gen0, grid0 = setup
    gen, tg = net.meter(31, ROLE_GEN)
    grid, tr = net.meter(32, ROLE_GRID)
    net.block([tg, tr])
    gen.pulse_export(1000)
    grid.pulse_export(1000)
    net.block(recs(gen) + recs(grid))      # counted before the request
    supplier = Wallet.create()
    net.block([supplier.pair_request("test", 31, 32)])
    gen.pulse_export(4000)                 # exported while certifiers wait
    grid.pulse_export(4000)
    net.block(recs(gen) + recs(grid))
    net.block([net.pair(2, 31, 32, supplier.address)])
    assert net.ledger.balance(supplier.address) == 4000
    p = net.ledger.state["pairs"]["2"]
    assert p["requested"]["height"] < p["certified"]["height"]
    with pytest.raises(LedgerError, match="account"):
        bad = dict(supplier.pair_request("test", 31, 32), beneficiary=owner.address)
        net.ok(bad)


def load_site(net, owner):
    gen, tg = net.meter(41, ROLE_GEN)
    grid, tr = net.meter(42, ROLE_GRID)
    load, tl = net.meter(43, ROLE_LOAD)
    net.block([tg, tr, tl, net.pair(4, 41, 42, owner.address, load=43)])
    return gen, grid, load


def test_load_meter_mints_nothing_and_balances(setup):
    net, owner, *_ = setup
    gen, grid, load = load_site(net, owner)
    for _ in range(10):                     # 10 kWh: 6 exported, 4 used on site
        gen.pulse_export(1000)
        net.block(recs(gen))
        if _ % 5 in (0, 2, 4):
            grid.pulse_export(1000)
            net.block(recs(grid))
        if _ % 5 in (1, 3):
            load.pulse_export(1000)
            net.block(recs(load))
    rep = net.ledger.pair_report(4)
    assert rep["tokens"] == {"gen": 10, "grid": 6, "load": 4}
    assert net.ledger.balance(owner.address) == 6000
    assert not rep["balance"]["flag"] and rep["claimable"]["balance"] == 0


def test_tap_between_gen_and_grid_raises_the_balance_flag(setup):
    net, owner, *_ = setup
    gen, grid, load = load_site(net, owner)
    for i in range(30):                     # 30 kWh: 12 exported, 12 used, 6 taken
        gen.pulse_export(1000)
        net.block(recs(gen))
        if i % 5 in (0, 2):
            grid.pulse_export(1000)
            net.block(recs(grid))
        elif i % 5 in (1, 3):
            load.pulse_export(1000)
            net.block(recs(load))
        # i % 5 == 4: a tap upstream of the GRID meter takes the kWh
    rep = net.ledger.pair_report(4)
    assert rep["balance"]["flag"] and rep["balance"]["since"] is not None
    over = rep["claimable"]["balance"]
    assert over > 0
    assert net.ledger.balance(owner.address) == rep["tokens"]["grid"] * 1000
    with pytest.raises(LedgerError, match="escrow"):
        net.ok(net.attest(4, over + 1, "balance", 1))
    net.block([net.attest(4, over, "balance", 1)])
    rep = net.ledger.pair_report(4)
    assert not rep["balance"]["flag"] and rep["attested_tokens"] == over


def test_load_meter_cannot_sit_in_the_grid_slot(setup):
    net, owner, *_ = setup
    load, tl = net.meter(51, ROLE_LOAD)
    gen, tg = net.meter(52, ROLE_GEN)
    net.block([tl, tg])
    with pytest.raises(LedgerError, match="GEN and one GRID"):
        net.ok(net.pair(5, 52, 51, owner.address))


def test_anyone_may_submit_a_raw_frame(setup):
    net, owner, gen, grid = setup
    gen.pulse_export(1000)
    grid.pulse_export(1000)
    frames = [b"\xEC\x01" + r.record + r.signature for r in gen.records + grid.records]
    gen.records, grid.records = [], []
    net.block([frame_tx(f, "ML-DSA-44") for f in frames])
    assert net.ledger.balance(owner.address) == 1000
