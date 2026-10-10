# A dishonest grid operator

Edition: v0.0.1 (doc-1.4, 2026-10-10). Issue [#4](https://github.com/Insomniac-VibeLabs/enerchain/issues/4).

## Plain language

The rest of the threat model asks whether a site owner can mint too much. This page asks the opposite question. Can the grid operator, who owns the wires on the other side of the meter and may sit among the certifiers, see to it that a supplier is credited for less than it exported?

It cannot forge a lower count. Each meter counts inside its seal and signs what it counted. It could do several other things: make the ledger ignore an honest count, throw it away, delay the start of counting, or take energy before the GRID meter sees it. doc-1.4 adds a rule against each of these. When a rule cannot prevent the loss, it makes the loss public and gives the supplier a way to recover it.

Physical curtailment is not a counting fault. An operator who limits or trips an inverter under grid rules gets less energy, and the meters correctly count less. Interconnection rules and regulators deal with that, not this protocol.

## What already held

- **Counters cannot be written from outside.** EC-MINT1 has no host write port, and the radio cannot receive. The QS7001 signs only records EC-MINT1 builds. A smaller record that verifies cannot be made.
- **Records are cumulative.** A dropped frame is replaced by the next one.
- **The current sensor is a shunt.** A magnet near the cover does not bias a resistive shunt the way it biases a current transformer.

## Attacks and answers

| The operator tries to | What answers it in doc-1.4 | Where |
| --- | --- | --- |
| Kill the GRID meter by opening its cover under power (the key wipe is by design) | The meter now signs one **tamper record** with a separate tamper key after its meter key is erased. The ledger marks the meter wiped. Token records built before the wipe still count when they arrive. The pair can **rebind** to a new GRID meter without a revocation vote. GEN tokens counted while no GRID meter could count go into **escrow**. | EC-MINT1, QS7001, board R22·C14, ledger |
| Unplug, remove or swap the GRID meter | The GRID meter goes **silent**. After `silent_s` (3 days) with no GRID record, GEN tokens beyond the last GRID record are in escrow, released by a k-of-n **attestation**. A meter that has signed a record since its last power-up re-sends at least daily, so 3 days of silence from it is not normal. After a power cut, the re-send restarts with the next token. | Ledger, EC-MINT1 re-send |
| Get a meter revoked | A revocation names a reason from a fixed list, carries an evidence hash and an **effective seq**: records at or below it are still credited. With k approvals it waits a 30-day **notice period**, and the beneficiary can **contest** it, which stops it. Only `k_urgent` approvals (default k + 1) make it immediate. **Genesis refuses** a certifier set in which one sector, the grid operator's included, holds k keys. | Registry, ledger, genesis |
| Delay pairing, so energy exported meanwhile is never minted | The supplier files a **pair request** signed by its own account. It fixes the starting counts when it is filed. The certificate, whenever it lands, starts from those counts and mints what was counted in between. The delay is public: the pair records both heights. | Ledger |
| Drop frames on the way to the ledger | **Anyone** may submit a frame (`enerchain frame submit`): the ledger checks the meter's signature, not the sender. The meter **re-sends** its last record after 24 h without one, so even a final frame comes back. | Ledger, CLI, EC-MINT1 |
| Take energy between the GEN and GRID meters ("siphon") | With a **LOAD meter** on the site's own consumption, the ledger checks GEN = GRID + LOAD within the pair's **loss allowance**. Missing energy raises a public **balance flag**, and the amount over the allowance is claimable by attestation. Without a LOAD meter the gap cannot be told apart from on-site use; see below. | Ledger, LOAD role |
| Curtail the inverter | Not a counting fault; out of scope. | Interconnection rules |

## Revocation

```
Revocation(meter_id, reason, effective_seq, evidence)
reason ∈ {seal_broken, metrology_fault, key_compromise, decommissioned, misinstalled}
evidence = SHA-384 of the inspection report, photographs, test record
```

| Approvals | Effect |
| --- | --- |
| fewer than k | refused |
| k to k_urgent − 1 | **pending** for `notice_s` (30 days); records keep minting; the pair's beneficiary may contest, which stops it for good |
| k_urgent or more | **active** at once; cannot be contested; also replaces a pending or contested filing |

Once active, a record is accepted only if its seq is at or below `effective_seq`. A revocation for tampering sets it to the last record the certifiers trust. An administrative one (decommissioning) sets it to the meter's current seq, so nothing measured is lost. Coins already minted stay.

A meter that sent a tamper record needs no revocation. Its tamper record is the evidence, signed by the meter itself.

## Rebind and escrow

```
PairRebind(pair_id, old_id, new_id)        k approvals
```

The old meter must be wiped or under an active revocation. The new one must have the same role, be certified, and be unpaired. A side of a pair is now a list of meters, and its count is

\[
T_{\text{side}} = \sum_{m \in \text{side}} \bigl(T_m - \text{base}_m\bigr),
\]

so late records from the old meter (seq at or below its effective seq) still add to the side. Minting is

\[
\text{minted} = \min\bigl(T_{\text{GEN}},\; T_{\text{GRID}} + A\bigr),
\]

where \(A\) is the tokens released by attestation. \(A\) starts at zero, and the GEN count caps the total.

**Outage escrow.** The pair is in outage while its current GRID meter is wiped, revoked, or unheard for `silent_s`. The escrow is the GEN tokens counted since the GRID meter was last heard, less what was already attested. When a GRID meter is replaced, its open escrow is carried over and stays claimable. When the same GRID meter is heard again, its cumulative count already covers the silence, so the live escrow closes.

```
Attestation(pair_id, tokens, reason ∈ {outage, balance}, evidence, nonce)   k approvals
```

The nonce is the pair's next attestation number, so an approved attestation cannot be replayed. The ledger refuses tokens above the escrow for that reason.

Attestation is the one place certifiers can add credit. The GEN meter's count bounds it, and it needs k approvals with evidence. This weakens the rule that both meters must agree, so it applies only to the energy the GRID side provably could not count.

## Siphoning before the GRID meter

### Where a tap can be

- **Downstream of the GRID meter**, on the operator's side: the GRID meter has already counted the energy, so the supplier is credited. Nothing to do.
- **Inside the GRID meter's cover**: opening it under power erases the key and produces a tamper record. Opening it unpowered is O-1.
- **Across the GRID meter's terminals, or on the conductors between the GEN and GRID meters**: the GRID meter counts less than left the generator, so \(\min(T_{\text{GEN}}, T_{\text{GRID}})\) is lower. This is the case to catch.

### Installation rule

The GRID meter sits at the ownership boundary, on the supplier's side, in the supplier's sealed enclosure. Its terminal shroud is sealed. The pair certificate carries `site_hash`, the SHA-384 of the single-line diagram and installation record the certifiers approved. A tap upstream of the GRID meter is then a change to the supplier's own wiring, against an approved drawing, and an inspection can find it.

### The balance check

Without a third meter, GEN − GRID is generation minus export, which is the site's own use plus losses plus any tap. The ledger cannot separate them. A LOAD meter on the site's consumption separates them. It is the same EC-SEAL1 board with role 3, wired so that consumption flows from its generator stud to its grid stud, so its tokens count consumed kilowatt-hours. It mints nothing.

At the bus between the meters, energy is conserved:

\[
G(t) = N(t) + L(t) + \text{losses}(t) + S(t),
\]

where \(G\) is generation, \(N\) net export, \(L\) consumption and \(S\) the energy a tap took.

Records carry no time (S-8), so the ledger cannot read all three at one instant. It bounds the gap from below instead. Let a GRID record be accepted at time \(T\). Then:

- The GEN count on chain at \(T\) was built no later than \(T\): \(q\,T_G \le G(T)\), up to the inverter's standby import.
- The GRID count is the high-water of net export at \(T\): \(N(T) < q\,(T_N + 1)\).
- The first LOAD record accepted after \(T\) bounds consumption by \(T\): \(L(T) < q\,(T_L + 1)\).

So

\[
r = T_G - T_N - T_L - A \quad\Rightarrow\quad \frac{\text{losses}(T) + S(T)}{q} > r - 2 .
\]

The ledger computes \(r\) each time a GRID record and the next LOAD record pair up, and again with the roles swapped. It raises the flag when

\[
r > \left\lceil T_G \cdot \frac{\text{loss\_ppm}}{10^{6}} \right\rceil + 2 .
\]

If true losses are within the allowance, a raised flag means energy went missing, and the claimable amount, \(r\) minus the allowance, is less than what the tap took. The test `test_siphon_before_the_grid_meter_is_flagged` checks that bound against the simulated tap.

The bound holds only if records reach the ledger in the order they were built. A transmit-only radio delivers them that way. A record held back and delivered late can lower \(r\) until the next pairing. It can also raise \(r\) by at most what it held back, which is why the flag moves no credit by itself.

### What it catches

The default allowance is 2 % of GEN (`loss_ppm = 20000`), for cable, inverter-to-meter and metering error. It is a placeholder. Certifiers should set each pair's allowance from the I²R loss its site survey computes for the run between the GEN and GRID meters, plus the two meters' accuracy classes.

The simulated site (5 kW peak, 38.2 kWh a day, a 400 W house load with a 1.5 kW evening peak) gives these results:

| Tap | Taken per day | Share of generation | Flag (2 % allowance) |
| --- | --- | --- | --- |
| none | 0 | 0 | clear, \(r\) between −1 and 0 |
| none, 3 kW battery loop behind LOAD | 0 | 0 | clear, \(r\) between −5 and −4 |
| 150 W | 3.6 kWh | 9.4 % | raised on day 2 |
| 300 W | 7.2 kWh | 19 % | raised on day 2 |
| 50 W | 1.2 kWh | 3.1 % | clear after 8 days: \(r\) 9 against an allowance of 9 |

A tap smaller than the allowance is not caught. Neither, for a long time, is one only slightly larger. Tightening `loss_ppm` to the surveyed loss is how a pair catches smaller taps. Run `enerchain demo --siphon-w 300` to see the flag raised.

### Storage

A battery behind the LOAD meter is fine: charging counts as consumption, discharging is subtracted, and a loop nets out over time. A battery on the bus between GEN and GRID, but not behind LOAD, looks like a tap while it charges and like extra export while it discharges. Such a site should not use the balance check, or should meter the battery as part of LOAD.

## Hardware changes

**Daily re-send.** EC-MINT1 counts seconds from a 16 MHz prescaler. After `RESEND_S = 86400` seconds with no record started, it signs the last accepted token record again, with the same counters and the next seq. A site that is generating sends records every kWh anyway, so the re-send costs at most one extra frame a day per meter. It does not survive a power cut: after one, the first new token restarts it.

**Tamper record.** On ZEROIZE, EC-MINT1 still sends `5C 5C` first, and the QS7001 erases the meter key within microseconds. Then EC-MINT1 sends `A7` and a record of kind 1 holding the counters as they stand. The QS7001 signs it once with a second key, the tamper key, made at personalization and published in the meter certificate. It then erases that key. A power cut before that point erases the tamper key unused at the next boot. The tamper record passes the same rollback guard as any record and mints nothing.

**Signer-rail delay.** The QS7001 must stay powered long enough to sign the tamper record: the 1.1 s ready-poll limit plus a 0.21 s frame. R22·C14 goes from 220 kΩ × 1 µF (0.22 s) to 1.5 MΩ × 2.2 µF (3.3 s). Q5 stays fully on (|V_GS| ≥ 1.8 V) until CROW_G reaches 1.5 V:

\[
t = 3.3\ \text{s} \times \ln\frac{3.3}{1.8} = 2.0\ \text{s},
\]

and 1.4 s if DC bias leaves C14 30 % low. Both exceed 1.31 s. Q5 opens at about 4.3 s. The meter key is still erased within microseconds. The longer window only keeps the tamper key, which can sign nothing else, alive for those seconds. See [electrical-review.md](electrical-review.md) M-9 and open item O-11.

**LOAD role.** The role byte accepts 3. The die, the schedule and the board are unchanged.

## What this does not stop

- **Physical curtailment** of the inverter under grid rules.
- **A tap smaller than the loss allowance**, or any tap at a site without a LOAD meter. At such a site, the installation rule and inspection are the defense.
- **A GEN-side failure.** GRID-only energy is not escrowed, because the GEN meter is what proves the energy came from the certified generator. The GEN meter sits on the supplier's side, out of the operator's reach.
- **Collusion of k_urgent certifiers.** They can revoke at once. The sector rule makes it take more than one industry.
- **Opening a meter while it is unpowered** (O-1).

## Parameters

| Parameter | Value | Where |
| --- | --- | --- |
| `notice_s` | 30 days | genesis |
| `silent_s` | 3 days | genesis |
| `k_urgent` | k + 1, at most n | genesis |
| certifier sectors | no sector holds k keys | genesis |
| `loss_ppm` | 20 000 (2 %) default, per pair | pair certificate |
| `RESEND_S` | 86 400 s | EC-MINT1 parameter |
| R22·C14 | 1.5 MΩ × 2.2 µF = 3.3 s | EC-SEAL1 |
