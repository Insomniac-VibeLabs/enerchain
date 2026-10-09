# Energy verification

Edition: v0.0.1 (doc-1.2, 2026-10-09). The record below is the v0.0.1 wire format; the doc-0.3 illustration it replaces was not one.

## Plain language

The meter is a locked mint. It measures the electricity, signs what it measured, and only then can coins exist. The coin count comes from the physics of the interval, not from a request.

## Quantities

The meter measures voltage and current and integrates active power, in both directions, into whole watt-hours. What it signs is cumulative:

- meter identity and role (GEN at the generator terminals, GRID at the grid connection)
- a sequence number
- cumulative export watt-hours
- cumulative import watt-hours
- cumulative tokens, one per 1000 Wh of net export
- the CRC of the calibration image the meter was certified with
- the device signature

A decoded record, as `enerchain frame verify` prints it:

```json
{
  "valid_signature": true,
  "meter_id": 1002,
  "role": 2,
  "seq": 3,
  "e_exp": 30412,
  "e_imp": 6208,
  "tokens": 30,
  "cal_crc": 18017,
  "version": 1,
  "class_tag": 34
}
```

Check: the tokens field may not exceed export divided by 1000 (30 ≤ 30.412), and it equals the high-water mark of export minus import, divided by 1000. Voltage, current and power factor are inside the STPM32's integral; they are not in the record, because the record is what mints and the integral is what the meter is certified for. Accuracy classes for this integral are standardized [IEC 62053-22:2020].

## Hardware

The meter contains a secure element, a unique identity, a private key that does not leave the element, tamper detection, a fixed-function schedule die that applies the schedule, and non-volatile storage for the counters. The element signs only what the die builds. Validators on the public ledger check the signature and that the record advances the last one from that meter. Transfer of the resulting coins uses a separate account key, also on the public ledger, so a spend is non-repudiable.

## Steps

1. The GEN meter and the GRID meter each integrate voltage and current in both directions.
2. Each schedule die counts tokens on net export and, every 10 tokens, builds a record; each secure element signs its own.
3. The records are submitted.
4. Validators accept each record whose signature verifies and whose sequence and counters advance.
5. The pair's owner is credited with min(GEN tokens, GRID tokens), less what was already credited.
6. The holder transfers them with an account signature.

## Schedule

The construction, the error bound, and the two-register schedule are specified in [hardware-binding.md](hardware-binding.md).
