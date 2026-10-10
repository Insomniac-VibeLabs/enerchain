# Enerchain whitepaper

Edition: v0.0.1 (doc-1.4, 2026-10-10). Sections 3, 4 and 7 are restated for the v0.0.1 issuance rule; the proposal is unchanged. Section 4 adds the protections against a grid operator that would under-credit a supplier.

## 1. Plain-language summary

Enerchain is a public currency minted by delivering electricity to a grid. The meter is the mint. It watches voltage, current, and time, and it will only sign a coin total that matches the energy that passed. Those coins transfer on a public ledger. The sender’s signature is the proof they cannot walk back.

The motive is the next couple of centuries of technical life. Computation, communications, manufacture, and transport are electrical loads, and computation’s share is growing. Generation is also spreading to people who used to only buy power. A cryptocurrency that spends electricity on puzzles is already an electricity currency. This one records electricity contributed.

Regions already trade power. The proposal is that the same unit remains the trade good when the region is a planet or a solar system.

## 2. Problem

Settlement media in general use are liabilities of banks and states. They are not dimensioned in joules. Electricity is an input to the technical economy, and energy scarcity constrains output more tightly than energy abundance does [Stern 2011]. Proof-of-work ledgers already convert electricity into the cost of ordering transactions [de Vries 2018]. They do not convert delivered grid energy into the unit itself.

Small agents can now both consume and produce. Market design for that prosumer case — grid integration, peer-to-peer trade, community groups — is a published problem [Parag and Sovacool 2016]. A review of energy-ledger projects found many chains and thin links from those chains to the meter [Andoni et al. 2019].

## 3. Proposal

Proof of Generation is the mint rule.

Ordinary language: coins come from power you put on the grid, in an amount the hardware will allow, and they move like any other public-ledger asset.

Technical language: the issuance transaction consumes a signed record from a meter and produces a balance. The record carries the meter identity, a sequence number, cumulative export and import watt-hours, and the cumulative token count the meter's schedule allowed for them. The device key lives in a secure element. The element signs only records built by the fixed-function schedule die, and only if they advance the last record it signed. Two certified meters form a pair: one at the generator terminals, one at the grid connection. The ledger credits the pair's owner with the smaller of the two token counts. Account keys then transfer the balance. Validators accept the transfer if the signatures verify and the nonce is next.

Ordering of the ledger is a separate choice. It must not be the thing the electricity unit rewards. Hashing spends electricity to choose a history [de Vries 2018]. Injection mints the unit [Mihaylov et al. 2014].

## 4. The hardware lock

Active energy on a single-phase circuit is the time integral of voltage times current. Billing-grade meters report that integral in kilowatt-hours, inside a stated accuracy class [IEC 62053-22:2020]. Enerchain uses the same quantities as the coin schedule:

- voltage
- current
- power factor
- interval length
- integrated watt-hours

The meter counts energy in both directions. The schedule is one token per 1000 Wh (1 kWh) of net export, and every token is signed and credited as it is minted: imported energy is subtracted before anything is minted, so energy bought from the grid and sent back mints nothing. The count is computed in a die with no host write port and signed by a secure element that will not sign a record whose counters go backward. Two meters that saw the same energy sign the same token count; the ledger takes the smaller of a pair's two counts, so a meter cannot mint past its partner. The schedule and the hardware are specified in [docs/hardware-binding.md](docs/hardware-binding.md).

The pair rule also gives the other side of the meter a lever. The grid operator owns the wires past the GRID meter and may be one of the certifiers. It cannot forge a lower count. It could disable or revoke the GRID meter, delay pairing, drop frames, or tap energy before the GRID meter. The ledger answers each of these. A revocation takes effect at a stated sequence number, so energy already measured is credited. It waits out a notice period the supplier can contest unless a larger quorum signs it. A meter opened under power signs one last tamper record with a separate key. Energy the GEN meter counted while no GRID meter could count is held in escrow. A pair request fixes the pair's starting counts when it is filed. Anyone may submit a frame, and the meter re-sends after a day without one. With a third, LOAD meter, energy missing between GEN and GRID raises a public flag. Genesis refuses a certifier set in which one sector can approve alone. [docs/grid-operator.md](docs/grid-operator.md) gives the rules and the arithmetic. Physical curtailment of an inverter is not a counting fault and is out of scope.

## 5. Transfer

A holder spends with an account signature over the destination, the amount, and a nonce. The ledger is public, so a third party can check the signature and the history. Non-repudiation is that signature. Ease of transfer is a standard account transfer, not a bilateral contract with a utility.

## 6. Regions

Wholesale markets already price a megawatt-hour by place and time [Schweppe et al. 1988; Hogan 1992; Tan et al. 2022]. Enerchain keeps one measurement and lets regional books trade the unit. A feeder, a national grid, a planet, and a solar system are successive region sizes. The trade instrument does not change with the size.

## 7. Prior art, and what is new here

Minting a currency unit for generated electricity is not new. NRGcoin minted for renewable injection and cleared it on a market [Mihaylov et al. 2014]. SolarCoin, launched in 2014, grants a coin per verified megawatt-hour of solar generation. Energy-sector ledgers such as Energy Web and Power Ledger, and certificate systems such as renewable energy certificates and guarantees of origin, already tie records to generation [Andoni et al. 2019]. Cryptographically signed meter readings are in commercial use, for example signed charging-station readings under German calibration law.

What this design adds, in combination:

- The token count is fixed in a dedicated schedule die with no processor and no host write port, and the signer will only sign what that die builds.
- Minting is on the net-export high-water mark, so storage loops and self-dealing through the grid connection mint nothing.
- Two independently sealed meters per site, and the ledger mints the minimum of their cumulative counts, which tolerates lost and late records.
- The meter signature is a NIST post-quantum signature (ML-DSA) inside a meter-class power budget.
- One measurement language from a feeder to a planetary region (a thesis, not a mechanism).

## 8. Sources

Full citations are in [docs/references.md](docs/references.md).
