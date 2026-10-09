# Enerchain economics

Edition: doc-0.2 (2026-10-08).

## Plain language

People would receive new units for delivering electricity. They would not receive a guaranteed price. A unit minted in a region with plenty of power can be worth less than a unit minted where power is scarce. The protocol’s job is the measurement and the mint. The market’s job is the price.

## Assumption, and its limit

Energy is an input to production, and scarcity of energy constrains growth more than abundance does [Stern 2011]. That supports measuring electricity as an economic fact. It does not support a fixed exchange rate between kilowatt-hours and a currency. Stern also notes that energy per unit of output falls as economies move to higher-quality carriers, especially electricity. A mint tied only to gross generation can therefore grow while the value of an extra kilowatt-hour falls.

## Issuance and price

Enerchain’s economic hypothesis, inherited in outline from generation-minted designs such as NRGcoin [Mihaylov et al. 2014]:

- Accepted delivery mints units under a published function.
- Holders sell or spend units on an open market.
- Nothing in the mint function sets the market price.

Wholesale power already prices the physical megawatt-hour by node and interval [Schweppe et al. 1988; Hogan 1992; Tan et al. 2022]. Enerchain should not publish a second, protocol-level price for the same electrons. If both a wholesale settlement and a PoG mint exist for one interval, the specification must say which claim is exclusive.

## Who could contribute

Any installation that can present the evidence in [energy-verification.md](energy-verification.md): residential and community solar, wind, hydro, nuclear, and later sources. Fuel type is not measured by a watt-hour meter. A carbon claim needs its own evidence and must not be smuggled into the energy field.

## Benefits worth testing

- A public link from accepted delivery to issuance.
- Participation that is not limited to one utility’s billing system.
- A common measurement that local markets can price differently, which is how power systems already work.

These are hypotheses. The Brooklyn Microgrid study found that a ledger can run a local market design and still be stopped by regulation [Mengelkamp et al. 2018].

## Risks

- Oversupply of the unit if issuance tracks a growing capital stock of generators and demand for the unit does not.
- Hardware centralization: a handful of meter vendors become de facto issuers.
- Regulatory conflict with franchise, tariff, and certificate law.
- Manipulation of the measurement, which is a security property, not a market property. See [energy-verification.md](energy-verification.md).
- Uneven access: regions that cannot field certified meters cannot mint, so the protocol can recreate the asymmetry it describes.

None of these are closed.
