# EC-SEAL1 build package

Edition: v0.0.1 (doc-1.4), board revision B. Read this before the plot files.

You are building a sealed single-phase meter. You are not choosing the circuit. The parts, the nets, and the mains copper are already decided. Two assemblies ship as a pair: one at the generator terminals (GEN), one at the point of connection to the grid (GRID). Same board. The ledger, not the board, requires both signatures. A site may order a third, identical assembly for its own load (LOAD); only the calibration image and the wiring differ.

Revision B is a bench prototype. It is not a field meter until open item O-1 (tamper while unpowered) is closed. See [docs/open-items.md](../../../docs/open-items.md).

## What is finished

- [BOM.csv](BOM.csv) is the buy list. One manufacturer part number per line. Do not substitute the shunt, the four 499 kΩ resistors, the MOV, the LNK304, the LDO, the STPM32, the FRAM, or the QS7001. R22 (1.5 MΩ) and C14 (2.2 µF X7R, 16 V) set how long the signer stays powered after a tamper event; a lower value or a capacitor with more DC-bias loss can stop the tamper record from being signed (doc-1.4, M-9).
- [netlist.txt](netlist.txt) is the connectivity. Every pin of every part is named. Logic ground is Line on the grid side of the shunt, net `GND`. Neutral is net `N`.
- [centroid.csv](centroid.csv) is the pick-and-place, millimetres, origin at the board's lower left, rotation in degrees.
- [CIRCUITS.md](CIRCUITS.md) is the circuit and its calculations.
- The Gerber in [gerber/](gerber/) already contains the copper that is not allowed to move:
  - the 40 A generator pour, H2 to the shunt force pad
  - the 40 A grid pour, the shunt force pad to H1, which is also logic ground
  - the ground strip along the top edge from that pour into via TV1, where the inner ground plane begins
  - the Neutral pour from H3 to the fuse, and the Neutral gutter down the left edge into R4
  - the fused-Neutral tap from the fuse, through the MOV, to R1
- That copper stays. Do not redraw it. [gerber/README.md](gerber/README.md) says which file is which.

## What you still execute, and what you do not invent

Everything else in the netlist is not yet copper. Fan the remaining nets from [netlist.txt](netlist.txt) with these rules:

- 4-layer, 1.6 mm, FR-4. Stack in [STACKUP.md](STACKUP.md). Inner 1 and inner 2 are already the plane windows in the Gerber.
- Top and bottom signal, 0.15 mm trace, 0.15 mm clearance, except the mains pours above, which are already wide. Inner 1 is ground. Inner 2 is 3.3 V, only under the logic half, x greater than 46 mm. QS_VDD is not that plane; it is the net after Q5, on the top.
- Mains nets are `N`, `N_F`, `N_R`, `VD1`–`VD3`, `VB1`, `VBULK`, `SW`, `BP`, `FB` and `FBC`. They stay on the top, left of x = 43.5 mm, at least 2.5 mm from any other net and 3 mm from the board edge. The one exception is VD3 to VIP_S across R7 itself, which carries a quarter of the line voltage. `tools/gen_board.py` checks the placed lands against these rules and exits non-zero if any fails; keep your fanout to the same numbers.
- The U5 switching loop (U5 S, D3, L2, C18, C17) is short and on the top. Keep the feedback node FB short and away from L2.
- Kelvin sense from RS.SG and RS.SI is a pair of 0.25 mm traces to R11 and R10. They do not share copper with the force path or with the supply return.
- EC-MINT1 is the only SPI master of the QS7001 and of the FRAM. J4 pin 4 is the only radio signal, and it is an output. Do not add a trace from the radio back to U3, U4 or U6.
- J5 is a factory pogo row. After calibration it is covered by the mesh. It is not a connector a person can touch.
- Via drill 0.30 mm, via pad 0.60 mm, only in open channel or in a power pad. Do not via under mains copper. TV1 is the one via already drilled. It ties ground to inner 1.

## Do not redesign

- Token quantum, gains, and the pulse rate are not board options. They are the EC-MINT1 calibration image.
- Do not fit the doc-0.9 BOM or the doc-1.1 supply. The doc-1.1 dropper had its clamp diode reversed and could not supply the logic. The reasons are in [../../../docs/electrical-review.md](../../../docs/electrical-review.md).
- Do not bond the radio to the signer or the FRAM.

## Enclosure

The whole board, logic included, is at mains potential. The cover is the insulation.

- Polycarbonate, no metal fastener that reaches a pad.
- A conductive mesh on the inside of the cover lands across SW1. Opening the cover opens that contact.
- VEMT3700 looks at a light well. Light on that sensor must reach PT1. A sealed cover keeps it dark.
- No user connector. The radio module and its antenna are inside the plastic.
- Hipot and creepage are the board house's process check against IEC 62052-31 for a 240 V class II meter. The spacing numbers above are the layout rule. They are not a certificate.

## Order

One panel, two circuits, both stuffed the same. Mark one GEN and one GRID (and LOAD, if ordered) in the silkscreen after the set is serialized. The meter id and role are in the calibration image shifted in at the provision jig, not in the stencil.
