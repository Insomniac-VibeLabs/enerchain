# Enerchain whitepaper

Edition: doc-0.2 (2026-10-08). Research note. Not a specification and not an offer of a token.

## 1. Plain-language summary

Civilizations run on electricity: computation, factories, communications, and transport all stop when the power stops. Money, meanwhile, is mostly a record kept by institutions. Enerchain asks whether a public record can be issued when useful electricity is produced and delivered, and whether that record can move even when the electricity cannot.

Two ideas are kept apart on purpose.

- The measurement is the same everywhere. A watt-hour is a watt-hour on Earth or on Mars.
- The price is not. A watt-hour in a place that already has surplus solar is not worth what a watt-hour is worth in a place that is short of power.

The protocol would check the measurement. A market would set the price. This document does not claim that such a market already exists, or that the check can yet be done without trusted hardware.

## 2. Problem

Modern settlement systems represent value with liabilities of banks and states. Those liabilities are not denominated in energy. At the same time, electricity demand from computation and industry is large enough that energy use shows up in macroeconomic studies: energy and output move together, and energy scarcity constrains growth more tightly than energy abundance does [Stern 2011].

Direct generation is still rarely the native unit of a digital asset. Where a digital unit does track generation, it is usually an energy-attribute certificate in a registry, or a token granted by a foundation after someone uploads a meter reading. Those systems work only as well as the registry and the reading. A systematic review of energy-blockchain projects found many ledgers and few settled connections to meters, operators, and law [Andoni et al. 2019].

The research question is narrower than “can energy be money?”:

> Can a publicly auditable unit be issued only when a bounded electrical delivery has been evidenced, without giving one organization the sole right to declare that the delivery happened?

## 3. Proposal

Enerchain proposes Proof of Generation (PoG).

In ordinary language: you do not earn the unit by solving a puzzle. You earn it by delivering measured electrical energy under rules the network can check.

In technical language: PoG is the acceptance predicate for an issuance transaction. Inputs are a signed measurement record from a certified meter, a statement of the delivery boundary (injection to a grid, delivery to a stated load, or another boundary the specification will have to define), and a uniqueness proof for the interval. Outputs are a minted balance and a spent nullifier for that interval, so the same watt-hours cannot be presented again.

PoG is not a block-ordering algorithm. A later specification may order transactions with proof of stake, a committee, or another rule. The research constraint is that ordering must not itself be the thing being rewarded with the energy unit. Proof-of-work ordering spends electricity to choose a history [de Vries 2018]. Enerchain’s issuance event is the opposite direction: a claimed delivery of electricity. Mihaylov and colleagues stated a related split in 2014: mint the unit for injected renewable energy, and let an exchange discover the unit’s price [Mihaylov et al. 2014]. Enerchain adopts that split as prior art and does not adopt any NRGcoin parameter.

## 4. Measurement is not value

### Plain language

A scale can tell you the mass of a shipment. It cannot tell you the price. Enerchain wants the scale to be common and the price to be local.

### Technical statement

Active energy is the time integral of instantaneous power. For a single-phase circuit, instantaneous power is voltage times current; for billing-grade meters, active energy is that product integrated over the interval and corrected by the measured power factor, reported in kilowatt-hours. Accuracy classes for static AC meters are standardized [IEC 62053-22:2020]. A signed record of voltage, current, power factor, interval, and integrated energy can be checked for internal consistency (energy should match voltage, current, power factor, and duration within the accuracy class and within sampling error). Consistency is not delivery. A meter can be fed by a battery wheeled in a circle.

Economic value is already local in real power systems. Spot pricing treats electric energy as a commodity whose price varies by time and place [Schweppe et al. 1988]. Locational marginal price at a node is the cost of serving one more unit there, including congestion and losses; contract-network formulations carry that price through a meshed grid without pretending the physics is a simple path [Hogan 1992; Tan et al. 2022]. A kilowatt-hour in a congested load pocket is not the same economic object as a kilowatt-hour behind an export constraint.

Enerchain therefore refuses a protocol peg of “one token equals one currency unit of local retail electricity.” Physical generation is the issuance meter. Regional markets, if they form, discover value. Examples of different scarcity, not of different physics: a surplus solar hour in a mature grid; a constrained feeder; an isolated microgrid; a lunar settlement whose generation is sized to landed mass and storage [Metzger et al. 2013].

## 5. Issuance

### Plain language

Producing energy would be what creates new units. Spending units would not destroy the memory of the energy. The unit is a record of accepted generation, not a warehouse receipt, unless a later market explicitly makes it one.

### Technical statement

Proposed mint rule, still unspecified in parameters:

`minted_units = f(accepted_kWh, region, time, policy)`

`f` is not defined in doc-0.2. A constant `f` (one unit per kilowatt-hour, forever) is the simplest research baseline and is probably a bad monetary rule: generation can grow faster than demand for the unit, and SolarCoin’s public history is a warning that a token granted per megawatt-hour can trade far below the cost of the energy it records. That history is industry prior art, not a peer-reviewed result. See [docs/references.md](docs/references.md).

What doc-0.2 does fix:

- No mint without an accepted PoG record.
- No second mint on the same delivered interval (double counting).
- No silent overlap with an exclusive attribute certificate. Renewable energy certificates already separate a generation attribute from the energy; using one megawatt-hour as both an exclusive certificate and a mint is the failure Gillenwater and later scope-2 critiques describe [Gillenwater 2008; Brander, Gillenwater, and Ascui 2018].
- Redeemability for physical energy is out of scope. A mint is not a claim-check.

Candidate contributors in a future trial: rooftop and community solar, wind, hydro, nuclear, and any later source that can present the same evidence. The protocol should not encode a fuel preference it cannot measure. Carbon attributes, if wanted, belong in a separate attested field, not in the watt-hour.

## 6. Verification, in one page

A generation record carries meter identity, time, electrical quantities, integrated energy, and a signature from a key that is supposed to live in a secure element. Validators check the signature, the certification status of the key, freshness, and uniqueness. They cannot, from the signature alone, know that the current came from a generator rather than a spoofed source. Meter fraud against advanced metering infrastructure is documented at the sensor, in storage, and on the wire [McLaughlin, Podkuiko, and McDaniel 2010]. The open question is stated in [docs/energy-verification.md](docs/energy-verification.md): how far can those checks go without appointing the local utility as the only oracle?

## 7. What Enerchain explicitly does not claim

- That a running system exists.
- That PoG solves consensus.
- That hardware roots of trust are decentralized. Certification of meters is a governance problem. See [docs/governance.md](docs/governance.md).
- That peer-to-peer energy markets are legal. In the Brooklyn Microgrid case study, regulation was the component the project could not satisfy [Mengelkamp et al. 2018].
- That interplanetary trade moves energy. It would move records, on a delay-tolerant network [Burleigh et al. 2003].

## 8. Open research questions

1. Delivery boundary: injection, consumption, or net export?
2. Uniqueness against storage loops and virtual meters.
3. Issuance function `f` under growing generation.
4. Meter certification without a permanent central gatekeeper.
5. Coexistence with wholesale markets and certificate registries.
6. Finality under multi-minute light time.

## 9. Sources

Citations in the text are listed in full in [docs/references.md](docs/references.md).
