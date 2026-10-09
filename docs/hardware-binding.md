# Hardware binding of generation to tokens

Edition: v0.0.1 (doc-1.3, 2026-10-09). The token schedule, the signed payload and the pair rule below replace the doc-0.4 versions; the binding itself is unchanged.

This note specifies a measurement path whose signed output is the only input to token issuance. The signature is non-repudiable for the energy that passed the sealed terminals. It is proof of that integral. It is not a shipment of energy to another region.

## Plain language

Put the sensor, the running total, and the signing key inside one sealed box on the wire that feeds the grid. The box adds up voltage times current over time. It will sign a token issue only for that total. If the seal is broken, the key is destroyed, so a broken box cannot keep signing. A verifier checks the signature and the total. They do not accept a number typed by a person.

## Quantity

For a single-phase circuit the instantaneous power and the active energy over an interval \([t_0, t_1]\) are

\[
p(t) = v(t)\, i(t), \qquad E = \int_{t_0}^{t_1} p(t)\, dt.
\]

Three-phase energy is the sum of the three phase integrals. \(E\) is in joules; the register reports kilowatt-hours, \(E / 3.6 \times 10^6\). Billing-grade static meters already compute this integral to a stated class [IEC 62053-22:2020]. OIML R 46 is the matching international recommendation for active-energy meters.

## Discrete form, and the error that must be signed

The metrology core samples voltage and current at interval \(\Delta t\) and accumulates in integer units so the sum cannot be edited from outside:

\[
\hat{E} = \Delta t \sum_{n=0}^{N-1} v[n]\, i[n].
\]

With a shunt of resistance \(R_s\) on the current path and a divider of ratio \(k_v\) on the voltage path, the core converts ADC codes \(c_v, c_i\) by calibration constants stored in one-time memory:

\[
v[n] = k_v\, c_v[n], \qquad i[n] = c_i[n] / R_s.
\]

The truncation error of a rectangular sum is bounded by the variation of \(p\) inside one sample. For a band-limited waveform sampled above the Nyquist rate of the front-end filter, that bound is fixed by the filter and the class. The core stores \(\hat{E}\) and the class tag. A signature over a total that omits the class tag is rejected. Accuracy class is a standards fact about the integral [IEC 62053-22:2020]. It is the allowed miss between \(\hat{E}\) and \(E\), not a knob a host processor can turn.

## Token schedule

Let \(q\) be the quantum, in watt-hours, of one token; \(q = 1000\) Wh, one token per accepted kilowatt-hour. The meter counts active energy in both directions as whole watt-hour pulses. The core holds, inside the seal:

- \(E_x\), cumulative export watt-hours, monotone.
- \(E_m\), cumulative import watt-hours, monotone.
- \(T\), cumulative tokens, monotone.
- \(c\), a signed credit, \(c = E_x - E_m - qT\).

An export pulse adds one to \(E_x\) and to \(c\); when \(c\) reaches \(q\), \(T\) increases by one and \(c\) returns to zero. An import pulse adds one to \(E_m\) and subtracts one from \(c\). Therefore

\[
T = \left\lfloor \frac{\max_{t' \le t} \bigl(E_x(t') - E_m(t')\bigr)}{q} \right\rfloor .
\]

Tokens follow the high-water mark of net export. Energy imported and exported again does not raise that mark, so a loop through a battery mints nothing. Carrying \(c\) pulse by pulse means an interval cannot be split to round up. None of the four registers has a host write port.

For every token, that is for every kilowatt-hour of net export, the core builds a record and the signer signs it:

\[
(\text{meter id},\; \text{role},\; \text{class},\; \text{seq},\; E_x,\; E_m,\; T,\; \text{CRC of the calibration image}).
\]

The record is built the moment its token is minted, when \(c = 0\), so every record satisfies \(E_x - E_m = qT\) exactly. Every field is cumulative, so a record that is lost costs nothing: the next one carries the totals. The exact byte layout is in [hardware/asic/spec.md](../hardware/asic/spec.md). Validators accept a record only if \(\text{seq}\) is greater than the last accepted one and none of \(E_x, E_m, T\) went down. A replayed record fails the sequence check; a deleted record is simply superseded.

The registers, the sequence number and the calibration image are kept in an F-RAM inside the seal, in two CRC-checked slots, so a power cut does not reset them. The signer also stores the last values it signed and will not sign lower ones, so rolling the F-RAM back does not produce a second signature over the same energy.

## Hardware boundary

The following sit inside one tamper-responding enclosure, on the conductor that delivers energy to the grid:

- shunt in series with the current path, so current is a voltage across a part the attacker cannot swap without opening the seal
- voltage divider on the same terminals
- anti-alias filters and ADCs
- metrology core that alone executes the sum and the schedule
- the F-RAM that holds the counters and the calibration image
- secure element holding the signing key
- mesh, light sensor, and temperature sensor tied to key zeroization

The host processor that talks to the network is outside the core. It can submit the signed payload. It cannot increment a counter or ask the element to sign a different token count. doc-0.6 removes the host from the mint path entirely: the metrology core pulses, the element signs, a slept radio forwards. Draw is capped at a present-day meter in [meter-burden.md](meter-burden.md). The wiring is [schematics/mint-path.svg](schematics/mint-path.svg) and the circuit sheets in [schematics/](schematics/README.md).

Identity of the core is bound to the silicon, not to a sticker. SRAM startup state used as a physically unclonable identifier is a published meter-security construction [Rincón, Melo, Farias, and Carmo 2021]. The certification record maps that identifier to the device public key. A cloned board that does not reproduce the identifier does not match the certified key.

## Why the host cannot fake the total

1. The ADC codes never leave the core except inside a signature.
2. \(T\) is computed in the core from the pulses. The element signs the record the core built or it signs nothing.
3. Opening the enclosure zeroizes the key. A later signature from that key fails.
4. The sequence number and the counters only increase. Replaying an old signature fails the sequence check. Losing a record loses nothing, because the next record is cumulative.

A verifier accepts a record if and only if the signature verifies under the certified key, the calibration CRC matches the certificate, and the sequence number and counters advance. Under those checks the holder cannot deny the core signed that integral. That is the hardware non-repudiation claim.

## What this does not silently assume

Energy through the sealed terminals is what the signature asserts. Forcing a current through those terminals produces a real integral, and the core will count it, because the integral is real. Two measurements close that gap.

- The import register. Energy that comes in through the meter and goes back out nets to zero, so it does not raise the token count.
- A second meter. A site has a GEN meter at the generator terminals and a GRID meter at the point of connection, each sealed, each with its own key, both certified as a pair. The ledger credits the pair with \(\min(T_{GEN}, T_{GRID})\). The GEN meter says the energy was generated; the GRID meter says it left the site, net of what came in. Because both counts are cumulative, the two meters never have to report the same interval, and a record that arrives late or not at all does not matter. One meter cannot mint alone.

Software on the inverter, a rewritten host, and a database edit are not on that path. Those are the manipulations this binding is built to refuse. Opening the cover while the meter is unpowered is not yet refused; that is open item O-1 in [open-items.md](open-items.md).

## Sources

IEC 62053-22:2020. OIML R 46-1/-2:2012, *Active electrical energy meters*. WELMEC Guide 7.2, *Software Guide* (Measuring Instruments Directive 2014/32/EU), section on active electrical energy meters. Rincón, A. E. R., Melo Jr., W. S., Farias, C. M., & Carmo, L. F. R. C. (2021). Securing smart meters through physical properties of their components. *IEEE Transactions on Instrumentation and Measurement*, 70, 3000511. https://doi.org/10.1109/TIM.2020.3041098
