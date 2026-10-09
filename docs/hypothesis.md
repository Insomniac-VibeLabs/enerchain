# Hypothesis

Edition: doc-0.3 (2026-10-08). Unchanged in v0.0.1; the issuance event is now net export, see [hardware-binding.md](hardware-binding.md).

## Plain language

The bet is that the next couple of centuries of money should be denominated in electricity. Computation and the rest of the technical stack already run on it, and the cost of that stack keeps rising. Generation is no longer only a power-station business: a household can put power onto a larger grid. Proof-of-work cryptocurrencies are already electricity currencies, because mining is paid for in electricity. Enerchain turns that around. The work that mints the unit is electricity delivered to the grid, not electricity burned on a puzzle.

That unit should move like a modern cryptocurrency: easy to transfer, signed so the sender cannot deny it, and recorded on a public ledger. The amount minted is not a vote and not a story. It is fixed by the electrical measurement — voltage, current, time — inside hardware that will not sign a larger total than the energy that passed through it.

Trade follows the same pattern grids already use. Regions exchange power. As settlement spreads off Earth, the region is a planet, then a solar system. The common trade good is the electricity unit.

## Technical statement

Enerchain’s issuance event is active energy delivered across a meter into a grid, net of energy drawn from it, integrated from voltage and current. A secure element in the meter holds the signing key and will emit coins only as a published function of that integral. The resulting balance is a public-ledger asset: transferable, non-repudiable under the device signature, and ordered by the ledger.

Proof-of-work currencies already price block production in electricity [de Vries 2018]. Enerchain keeps the public ledger and the non-repudiation property, and replaces the hashing expenditure with evidenced injection. A peer-reviewed predecessor minted a unit for renewable injection and cleared its price on an exchange [Mihaylov et al. 2014]. Prosumers — agents who both consume and produce — are already a market-design problem, not a slogan [Parag and Sovacool 2016]. Locational prices already differ by region inside one interconnected system [Schweppe et al. 1988; Hogan 1992]. The long-range extension is to treat a planet or a system as another such region, with the same unit as the trade instrument.
