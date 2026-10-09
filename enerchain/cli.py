"""The ``enerchain`` command (v0.0.1 development network).

    enerchain --version
    enerchain demo [--days N] [--battery-loop-w W]
    enerchain devnet init DIR [--validators N] [--certifiers N] [--k K]
    enerchain devnet produce DIR
    enerchain devnet show DIR
    enerchain wallet new FILE
    enerchain wallet address FILE
    enerchain balance DIR ADDRESS
    enerchain transfer DIR WALLET TO AMOUNT_WH
    enerchain frame verify --alg ML-DSA-44 --pk HEX FRAME_HEX
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile

from . import __version__, crypto
from .ledger import WH_PER_TOKEN, cert_tx, issuance_tx
from .node import Devnet
from .record import ROLES, MeterRecord, RecordError, parse_frame
from .registry import MeterCert, PairCert
from .sim import Site
from .wallet import Wallet

IMAGE_HASH = crypto.sha384(b"firmware/qs7001/sign_oracle.c@v0.0.1")


def _tokens(wh: int) -> str:
    return f"{wh / WH_PER_TOKEN:.3f}"


def cmd_demo(args: argparse.Namespace) -> int:
    with tempfile.TemporaryDirectory() as d:
        net = Devnet.init(d, n_validators=2, n_certifiers=3, k=2)
        owner = Wallet.create()
        friend = Wallet.create()
        site = Site.new(1001, 1002, battery_loop_w=args.battery_loop_w)
        for meter in (site.gen, site.grid):
            r = meter.mint
            cert = MeterCert(r.meter_id, r.role, meter.alg, meter.pk, meter.cal_crc, IMAGE_HASH)
            net.submit(cert_tx("meter_cert", cert, net.approve(cert.body())))
        pair = PairCert(1, 1001, 1002, owner.address)
        net.submit(cert_tx("pair_cert", pair, net.approve(pair.body())))
        net.produce()
        print(f"enerchain {__version__} demo: 2 validators, 3 certifiers (k=2), "
              f"one GEN/GRID pair, {args.days} day(s)")
        for day in range(args.days):
            site.run_days(1)
            for meter in (site.gen, site.grid):
                for sr in meter.take_records():
                    net.submit(issuance_tx(sr.record, sr.signature))
            net.produce()
            g = site.gen.mint
            r = site.grid.mint
            print(f" day {day + 1}: generated {site.log['gen_wh'] / 1000:.1f} kWh, "
                  f"net export {site.log['net_export_wh'] / 1000:.1f} kWh | "
                  f"GEN tokens {g.tokens} GRID tokens {r.tokens} | "
                  f"minted {net.ledger.state['pairs']['1']['minted_tokens']} | "
                  f"balance {_tokens(net.ledger.balance(owner.address))}")
        bal = net.ledger.balance(owner.address)
        if bal >= 2500:
            tx = owner.transfer(net.ledger.chain_id, friend.address, 2500, net.ledger.nonce(owner.address) + 1)
            net.submit(tx)
            net.produce()
            print(f" transfer 2.500 tokens -> {friend.address[:12]}…: "
                  f"owner {_tokens(net.ledger.balance(owner.address))}, "
                  f"friend {_tokens(net.ledger.balance(friend.address))}")
        # A replayed record is refused.
        dup = issuance_tx(*_last_record(net))
        before = net.ledger.height
        net.submit(dup)
        net.produce()
        print(f" replayed record included: {len(net.ledger.blocks[-1]['txs'])} "
              f"(height {before} -> {net.ledger.height})")
        print(f" supply {_tokens(net.ledger.state['supply_wh'])} tokens, "
              f"{net.ledger.height} blocks")
    return 0


def _last_record(net: Devnet) -> tuple[bytes, bytes]:
    for b in reversed(net.ledger.blocks):
        for tx in reversed(b["txs"]):
            if tx["type"] == "issuance":
                return bytes.fromhex(tx["record"]), bytes.fromhex(tx["sig"])
    raise SystemExit("no issuance on chain")


def cmd_devnet(args: argparse.Namespace) -> int:
    if args.action == "init":
        net = Devnet.init(args.dir, args.validators, args.certifiers, args.k)
        print(f"devnet in {args.dir}: chain {net.ledger.chain_id}, "
              f"{len(net.ledger.validators)} validator(s), k={net.ledger.k} of "
              f"{len(net.ledger.certifiers)} certifiers")
    elif args.action == "produce":
        net = Devnet(args.dir)
        b = net.produce()
        print(f"block {b['header']['height']}: {len(b['txs'])} tx")
    else:
        net = Devnet(args.dir)
        st = net.ledger.state
        print(json.dumps({"height": net.ledger.height, "supply_wh": st["supply_wh"],
                          "meters": {k: {"role": ROLES.get(v["role"]), "last": v["last"],
                                         "revoked": v["revoked"]}
                                     for k, v in st["meters"].items()},
                          "pairs": st["pairs"], "accounts": st["accounts"]}, indent=1))
    return 0


def cmd_wallet(args: argparse.Namespace) -> int:
    if args.action == "new":
        w = Wallet.create()
        w.save(args.file)
        print(w.address)
    else:
        print(Wallet.load(args.file).address)
    return 0


def cmd_balance(args: argparse.Namespace) -> int:
    net = Devnet(args.dir)
    wh = net.ledger.balance(args.address)
    print(f"{wh} Wh ({_tokens(wh)} tokens)")
    return 0


def cmd_transfer(args: argparse.Namespace) -> int:
    net = Devnet(args.dir)
    w = Wallet.load(args.wallet)
    pending = [t for t in net.mempool() if t.get("type") == "transfer" and t.get("from") == w.address]
    nonce = net.ledger.nonce(w.address) + 1 + len(pending)
    net.submit(w.transfer(net.ledger.chain_id, args.to, args.amount_wh, nonce))
    print(f"queued transfer of {args.amount_wh} Wh, nonce {nonce}")
    return 0


def cmd_frame(args: argparse.Namespace) -> int:
    frame = bytes.fromhex(args.frame)
    try:
        raw, sig = parse_frame(frame, crypto.SIG_LEN[args.alg])
        rec = MeterRecord.unpack(raw)
    except (RecordError, KeyError) as e:
        print(f"bad frame: {e}")
        return 2
    ok = crypto.verify(args.alg, bytes.fromhex(args.pk), raw, sig)
    print(json.dumps({"valid_signature": ok, **rec.__dict__}, indent=1))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="enerchain", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"enerchain {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("demo", help="run a self-contained devnet scenario")
    p.add_argument("--days", type=int, default=3)
    p.add_argument("--battery-loop-w", type=float, default=0.0,
                   help="grid->battery->grid loop power; it should mint nothing")
    p.set_defaults(fn=cmd_demo)

    p = sub.add_parser("devnet")
    p.add_argument("action", choices=["init", "produce", "show"])
    p.add_argument("dir")
    p.add_argument("--validators", type=int, default=1)
    p.add_argument("--certifiers", type=int, default=3)
    p.add_argument("--k", type=int, default=2)
    p.set_defaults(fn=cmd_devnet)

    p = sub.add_parser("wallet")
    p.add_argument("action", choices=["new", "address"])
    p.add_argument("file")
    p.set_defaults(fn=cmd_wallet)

    p = sub.add_parser("balance")
    p.add_argument("dir")
    p.add_argument("address")
    p.set_defaults(fn=cmd_balance)

    p = sub.add_parser("transfer")
    p.add_argument("dir")
    p.add_argument("wallet")
    p.add_argument("to")
    p.add_argument("amount_wh", type=int)
    p.set_defaults(fn=cmd_transfer)

    p = sub.add_parser("frame")
    p.add_argument("action", choices=["verify"])
    p.add_argument("--alg", default=crypto.METER_ALG, choices=sorted(crypto.SIG_LEN))
    p.add_argument("--pk", required=True)
    p.add_argument("frame")
    p.set_defaults(fn=cmd_frame)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
