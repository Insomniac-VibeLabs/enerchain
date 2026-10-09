# Enerchain economics

Edition: v0.0.1 (doc-1.2, 2026-10-09). Adds net export, the pair rule, and the questions v0.0.1 leaves open.

## Plain language

People who put electricity on a grid receive coins locked to what they delivered. They can transfer those coins. Regions trade them the way regions already trade power. A scarce region can value the same coin more than a surplus region.

## Why electricity

Electricity is the carrier the technical economy is moving toward, and compute is a rising part of that load. Energy scarcity constrains output [Stern 2011]. A proof-of-work coin is already priced in electricity, because the miner pays the power bill [de Vries 2018]. Enerchain mints on the contribution instead of on the bill.

## Who can mint

Anyone who can put measured energy across a certified meter onto a grid: a house, a community array, a wind plant, a hydro plant, a nuclear plant, a later reactor. Prosumers — parties that both take and supply — are the household case [Parag and Sovacool 2016]. The watt-hour does not encode fuel type. The same schedule applies.

## Regional trade

Interconnected grids exchange energy across boundaries. The price at one node is not the price at another [Schweppe et al. 1988; Hogan 1992]. Enerchain uses that fact. The coin is the common unit. Each region can clear its own price. Conversion between regional books is a public trade of the same unit.

## Issuance baseline

One coin per accepted kilowatt-hour of net export, counted in the meter. A site's coins are the smaller of what its generator meter saw produced and what its grid meter saw leave the site net of what came in. A household that uses its own solar power mints only the surplus it sends out. Transfer does not remint. A region with a lot of generation can see a lower local price for the coin than a region that is short of power.

The grid meter counts the high-water mark of net export. A site that exports by day and imports in the evening is credited for the day's peak; the evening import then has to be exported again before anything more is minted. Over months the count follows cumulative net export.

## Questions this version leaves open

- **Double counting.** The same kilowatt-hour is usually sold to a utility and may also earn a renewable energy certificate. Whether a coin replaces, accompanies or must be reconciled with those is a market and legal decision. See open item S-5.
- **Value.** Supply grows with net generation and has no cap, and nothing redeems a coin for energy. The hypothesis is that settlement demand from electricity-hungry loads and regional books gives it value; the code does not establish that. See S-6.
- **Fuel.** The watt-hour does not encode fuel type, by design. A region that wants to price clean energy differently does so in its own market, not in the unit.
