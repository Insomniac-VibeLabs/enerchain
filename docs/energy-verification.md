# Energy verification

Edition: v0.0.1 (doc-1.4, 2026-10-10). The record below is the v0.0.1 wire format; the doc-0.3 illustration it replaces was not one. doc-1.4 adds the kind field and the LOAD role.

## Plain language

The meter is a locked mint. It measures the electricity, signs what it measured, and only then can coins exist. The coin count comes from the physics of the interval, not from a request.

## Quantities

The meter measures voltage and current and integrates active power, in both directions, into whole watt-hours. What it signs is cumulative:

- meter identity and role (GEN at the generator terminals, GRID at the grid connection, optionally LOAD on the site's own consumption)
- a sequence number
- cumulative export watt-hours
- cumulative import watt-hours
- cumulative tokens, one per 1000 Wh (1 kWh) of net export
- the CRC of the calibration image the meter was certified with
- the kind: a token record, or the one tamper record a meter signs after its cover is opened under power
- the device signature

A decoded record, as `enerchain frame verify` prints it:

```json
{
  "valid_signature": true,
  "meter_id": 1002,
  "role": 2,
  "seq": 30,
  "e_exp": 36208,
  "e_imp": 6208,
  "tokens": 30,
  "cal_crc": 49326,
  "version": 1,
  "class_tag": 34,
  "kind": 0
}
```

This GRID meter exported 5000 Wh, imported 6208 Wh, then exported 31 208 Wh. Check: the tokens field may not exceed export divided by 1000 (30 ≤ 36.208), and it equals the high-water mark of export minus import, divided by 1000, rounded down. A record is built the moment its token is minted, so in every record export minus import is exactly 1000 × tokens (36 208 − 6208 = 30 000), and seq is 30 because each of the 30 tokens produced one record and no day passed without one, so the meter re-sent nothing. Voltage, current and power factor are inside the STPM32's integral; they are not in the record, because the record is what mints and the integral is what the meter is certified for. Accuracy classes for this integral are standardized [IEC 62053-22:2020].

## Hardware

The meter contains a secure element, a unique identity, a private key that does not leave the element, tamper detection, a fixed-function schedule die that applies the schedule, and non-volatile storage for the counters. The element signs only what the die builds. Validators on the public ledger check the signature and that the record advances the last one from that meter. Transfer of the resulting coins uses a separate account key, also on the public ledger, so a spend is non-repudiable.

## Steps

1. The GEN meter and the GRID meter each integrate voltage and current in both directions.
2. Each schedule die counts tokens on net export and, for every token (every kilowatt-hour), builds a record; each secure element signs its own.
3. The records are submitted.
4. Validators accept each record whose signature verifies and whose sequence and counters advance.
5. The pair's owner is credited with min(GEN tokens, GRID tokens), less what was already credited. If the GRID meter is silent, revoked or wiped, GEN tokens beyond it wait in escrow; with a LOAD meter, energy missing between GEN and GRID raises a public flag ([grid-operator.md](grid-operator.md)).
6. The holder transfers them with an account signature.

## Schedule

The construction, the error bound, and the two-register schedule are specified in [hardware-binding.md](hardware-binding.md).
