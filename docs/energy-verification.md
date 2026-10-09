# Energy verification

Edition: doc-0.3 (2026-10-08).

## Plain language

The meter is a locked mint. It measures the electricity, signs what it measured, and only then can coins exist. The coin count comes from the physics of the interval, not from a request.

## Quantities

Every generation interval carries:

- meter identity
- start and end in UTC
- voltage
- current
- power factor
- duration
- integrated kilowatt-hours
- the device signature

Illustrative record, not a wire format:

```json
{
  "meter_id": "example-not-a-real-device",
  "interval_start": "2026-10-08T18:00:00Z",
  "interval_end": "2026-10-08T19:00:00Z",
  "voltage_v": 240,
  "current_a": 40,
  "power_factor": 0.98,
  "active_energy_kwh": 9.4,
  "coins": 9.4,
  "signature": "<device signature>"
}
```

Check: \(240 \times 40 \times 0.98 \times 1 / 1000 = 9.408\), which matches 9.4 kWh at the reported precision. The coin field has to match the schedule for that integral. Accuracy classes for this integral are standardized [IEC 62053-22:2020].

## Hardware

The meter contains a secure element, a unique identity, a private key that does not leave the element, tamper detection, and firmware that applies the schedule. The element signs. Validators on the public ledger check the signature and that this interval has not been minted. Transfer of the resulting coins uses a separate account key, also on the public ledger, so a spend is non-repudiable.

## Steps

1. The meter integrates voltage and current over the interval.
2. The secure element applies the coin schedule and signs.
3. The record is submitted.
4. Validators accept the signature and the fresh interval.
5. Coins are issued.
6. The holder transfers them with an account signature.

## Schedule

doc-0.3 uses a one-to-one baseline: one coin per accepted kilowatt-hour. A later edition can change the schedule. It cannot change the rule that the element will not sign above the schedule.
