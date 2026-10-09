# Hardware binding of generation to tokens

Edition: doc-0.4 (2026-10-08).

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

Let \(q\) be the quantum, in watt-hours, of one token. The core holds two registers, both inside the seal:

- \(W\), cumulative watt-hours since commissioning, monotone.
- \(r\), the residual below one token, \(0 \le r < q\).

On each sealed interval the core adds the new watt-hours \(w\) and signs an issuance only for the whole tokens that fall out:

\[
n = \left\lfloor \frac{r + w}{q} \right\rfloor, \qquad r \leftarrow (r + w) - n q, \qquad W \leftarrow W + w.
\]

doc-0.4 sets \(q = 1000\) Wh, so one token per accepted kilowatt-hour. \(n\) is a function of registers the host cannot write. Carrying \(r\) stops an attacker from minting by splitting an interval into pieces that each round up. The signed payload is

\[
(\text{meter id},\; t_0,\; t_1,\; w,\; n,\; W,\; r,\; \text{class}).
\]

Validators mint \(n\) and store \(W\). A later interval whose \(W\) is not exactly the previous \(W\) plus its \(w\) is rejected. That chain makes a deleted or replayed interval fail the next check.

## Hardware boundary

The following sit inside one tamper-responding enclosure, on the conductor that delivers energy to the grid:

- shunt in series with the current path, so current is a voltage across a part the attacker cannot swap without opening the seal
- voltage divider on the same terminals
- anti-alias filters and ADCs
- metrology core that alone executes the sum and the schedule
- secure element holding the signing key
- mesh, light sensor, and temperature sensor tied to key zeroization

The host processor that talks to the network is outside the core. It can submit the signed payload. It cannot increment \(W\) or ask the element to sign a different \(n\). Legal-metrology software guidance for active-energy meters already separates legally relevant measurement software from the rest of the instrument and requires that an alteration be detectable [WELMEC Guide 7.2]. Enerchain uses that split: only the metrology image can touch the registers, and its hash is inside the signed payload.

Identity of the core is bound to the silicon, not to a sticker. SRAM startup state used as a physically unclonable identifier is a published meter-security construction [Rincón, Melo, Farias, and Carmo 2021]. The certification record maps that identifier to the device public key. A cloned board that does not reproduce the identifier does not match the certified key.

## Why the host cannot fake the total

1. The ADC codes never leave the core except inside a signature.
2. \(n = \lfloor (r+w)/q \rfloor\) is computed in the core. The element signs that \(n\) or it signs nothing.
3. Opening the enclosure zeroizes the key. A later signature from that key fails.
4. \(W\) is monotone and chained. Replaying an old signature fails the chain. Skipping an interval fails the chain.

A verifier accepts an issuance if and only if the signature verifies under the certified key, the schedule identity matches, and \(W\) extends the stored chain. Under those checks the holder cannot deny the core signed that integral. That is the hardware non-repudiation claim.

## What this does not silently assume

Energy through the sealed terminals is what the signature asserts. Forcing a current through those terminals produces a real integral; the core will sign it, because the integral is real. Net generation, as against a loop that returns the same energy, is a second measurement: a grid-side meter on the same terminals, sealed by the interconnection, whose signed \(w\) must match the generator meter inside the class tolerance. Issuance requires both signatures. One meter cannot mint alone.

Software on the inverter, a rewritten host, and a database edit are not on that path. Those are the manipulations this binding is built to refuse.

## Sources

IEC 62053-22:2020. OIML R 46-1/-2:2012, *Active electrical energy meters*. WELMEC Guide 7.2, *Software Guide* (Measuring Instruments Directive 2014/32/EU), section on active electrical energy meters. Rincón, A. E. R., Melo Jr., W. S., Farias, C. M., & Carmo, L. F. R. C. (2021). Securing smart meters through physical properties of their components. *IEEE Transactions on Instrumentation and Measurement*, 70, 3000511. https://doi.org/10.1109/TIM.2020.3041098
