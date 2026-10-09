# Enerchain whitepaper

Edition: doc-0.3 (2026-10-08).

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

Technical language: the issuance transaction consumes a signed interval from a meter and produces a balance. The interval carries identity, time, voltage, current, power factor, and integrated active energy. The device key lives in a secure element. The element’s firmware releases a signature only for a coin count inside the published function of that integral. Account keys then transfer the balance. Validators accept the transfer if the signatures verify and the interval has not been minted.

Ordering of the ledger is a separate choice. It must not be the thing the electricity unit rewards. Hashing spends electricity to choose a history [de Vries 2018]. Injection mints the unit [Mihaylov et al. 2014].

## 4. The hardware lock

Active energy on a single-phase circuit is the time integral of voltage times current. Billing-grade meters report that integral in kilowatt-hours, inside a stated accuracy class [IEC 62053-22:2020]. Enerchain uses the same quantities as the coin schedule:

- voltage
- current
- power factor
- interval length
- integrated watt-hours

The lock is that the secure element will not sign a record whose coin count exceeds the schedule for the integral it measured. A later specification sets the schedule. The research baseline is a fixed number of units per accepted kilowatt-hour, so two meters that saw the same energy sign the same issuance.

## 5. Transfer

A holder spends with an account signature over the destination, the amount, and a nonce. The ledger is public, so a third party can check the signature and the history. Non-repudiation is that signature. Ease of transfer is a standard account transfer, not a bilateral contract with a utility.

## 6. Regions

Wholesale markets already price a megawatt-hour by place and time [Schweppe et al. 1988; Hogan 1992; Tan et al. 2022]. Enerchain keeps one measurement and lets regional books trade the unit. A feeder, a national grid, a planet, and a solar system are successive region sizes. The trade instrument does not change with the size.

## 7. Sources

Full citations are in [docs/references.md](docs/references.md).
