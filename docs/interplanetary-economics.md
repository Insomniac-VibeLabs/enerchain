# Interplanetary economics

Edition: doc-0.2 (2026-10-08).

## Plain language

If people live on the Moon, on Mars, or in orbit, a watt-hour is still a watt-hour. It will not be worth the same in each place, and it cannot be mailed from one world to another at a useful cost. Enerchain’s long-range idea is a shared way to record verified generation, plus a public way to convert between local prices. The electricity stays where it was made.

## What is in scope

Signed generation records, local markets, and exchange rates between those markets’ units. Settlement that still completes when messages take minutes.

## What is out of scope

Beaming or shipping electrical energy between planets. No peer-reviewed result in this document set supports that as an economic transport mode. Space-industry models treat local energy and landed mass as the binding constraints on off-Earth industry [Metzger et al. 2013]. That is why a frontier settlement can value a local watt-hour highly. It is not a plan to export the watt-hour.

## Measurement versus value

Physical measurement is universal: voltage, current, time, and integrated active energy do not change their definitions with location. Economic value is local for the same reason it is local on Earth. Spot and locational prices already diverge by node and hour inside one grid [Schweppe et al. 1988; Hogan 1992]. A mature region with surplus generation and a new settlement with thin infrastructure are two more nodes, farther apart. Examples used as scarcity cases, not as forecasts: surplus solar on a terrestrial grid; a capacity-short region; an early Martian surface system; a station whose generation is a reactor and whose storage is limited.

## Exchange

The hypothesis: one evidence rule for generation, many markets for value.

Proof of Generation would establish quantity, location, time, and the delivery check. Markets would establish price, scarcity premia, and infrastructure premia. Possible books, if the research ever gets there: terrestrial regions, a planetary book, an orbital book, a colony book. Conversion between books should be public. The protocol should not force the prices to be equal.

A frontier premium is an incentive to build generation where it is scarce. As local capacity grows, that premium can fall. That is an economic conjecture, consistent with locational pricing, not a measured result.

## Delay

Earth–Mars one-way light time is roughly 3 to 22 minutes. Delay-tolerant networking exists because interactive Internet protocols fail across that gap [Burleigh et al. 2003]. An interplanetary Enerchain cannot use a consensus round that waits on the other planet inside a block time. Local books finalize locally. Cross-book transfers are messages with explicit delay, not atomic swaps across light-minutes.

## Vision, labeled as vision

A civilization with many energy markets can share a measurement language without sharing a price. Enerchain’s interplanetary claim is only that language, plus auditable conversion. It is not a claim that the markets exist, and not a claim that energy is the same economic good on every world.
