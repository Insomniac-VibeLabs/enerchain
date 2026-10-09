# Energy verification

Edition: doc-0.2 (2026-10-08).

## Plain language

Enerchain only works if the network can tell a real delivery from a story. The meter has to be identifiable, the reading has to be signed, and the same energy must not be counted twice. A signature proves who signed. It does not, by itself, prove where the electrons came from.

## Objective

Define the minimum evidence for a Proof of Generation claim, and name the frauds that evidence does not yet stop.

## What a claim must carry

Every accepted generation event needs:

- Meter identity, bound to a certified key.
- Interval start and end in UTC, with a stated clock-error bound.
- Voltage, current, and power factor, or the raw samples from which they were derived.
- Duration and integrated active energy in kilowatt-hours.
- Delivery boundary: injection point, load point, or another boundary the specification defines.
- A digital signature over the canonical record.
- A nullifier so this interval cannot be submitted again.

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
  "boundary": "injection",
  "signature": "<detached signature>"
}
```

Internal check: `voltage * current * power_factor * hours / 1000` should land near `active_energy_kwh`, inside the meter’s accuracy class and sampling error. For this example, `240 * 40 * 0.98 * 1 / 1000 = 9.408`, which matches 9.4 kWh at the reported precision. A mismatch is a reason to reject. A match is not proof of a generator.

## Hardware assumptions

A research-grade Enerchain meter would need a secure element holding a unique key, tamper detection, and firmware that the certification policy recognizes. Accuracy of active-energy measurement is a solved standards problem at the class level [IEC 62053-22:2020]. Tamper resistance is not. Field studies of advanced metering infrastructure show usage data can be altered at the sensor, at rest in the device, and in transit [McLaughlin, Podkuiko, and McDaniel 2010]. Generation fraud is that literature with the sign flipped: inflate delivered energy instead of hiding consumed energy.

## Verification steps

1. Meter integrates energy at the stated boundary.
2. Meter signs the record with its device key.
3. The record is submitted to validators.
4. Validators check signature, certification, time window, and nullifier.
5. A delivery rule, not yet specified, accepts or rejects the physical claim.
6. Only then may issuance run.

Step 5 is the open problem. Step 4 can be decentralized. Step 5 cannot be decentralized by wishing.

## Frauds the design must resist

- Fabricated generation, including a source feeding the meter with no net delivery.
- Cloned hardware and extracted keys.
- Double counting across Enerchain and a certificate registry [Gillenwater 2008].
- Replay of an old signed interval.
- Circular schemes: charge a battery from the grid, discharge it through the meter, mint on both legs.
- Storage reported as generation.

## Open research question

How can Enerchain verify production while minimizing reliance on a single utility oracle?

Candidate directions, none selected:

- Cross-check against an independent sensor at the same boundary.
- Statistical tests on electrical signatures of the claimed source.
- Commitment of encrypted interval data, with later audit by a rotating set of observers.
- Economic bonding of the meter operator, slashed on demonstrated fraud.

Any direction that quietly appoints one company as the permanent oracle fails the governance rule in [governance.md](governance.md). Any direction that ignores the utility’s physical switch fails the grid. Both constraints stand.
