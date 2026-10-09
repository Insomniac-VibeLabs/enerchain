# EC-SEAL1 build package

Edition: doc-1.1. Read this before the plot files.

You are building a sealed single-phase meter. You are not choosing the circuit. The parts, the nets, and the analog copper are already decided. Two assemblies ship as a pair: one in the generator lead, one in the grid lead. Same board. The ledger, not the board, requires both signatures.

## What is finished

- [BOM.csv](BOM.csv) is the buy list. One manufacturer part number per line. Do not substitute the shunt, the four 499 kΩ resistors, the MOV, the X2 capacitor, the LDO, the STPM32, or the QS7001.
- [netlist.txt](netlist.txt) is the connectivity. Every pin of every part is named. Logic ground and Neutral are one net, `GND`.
- [centroid.csv](centroid.csv) is the pick-and-place, millimetres, origin at the board's lower left, rotation in degrees.
- [CIRCUITS.md](CIRCUITS.md) is the discrete circuit, including the transistors.
- The Gerber in [gerber/](gerber/) already contains the copper that is not allowed to move:
  - the 40 A generator pour, H2 to the shunt force pad
  - the 40 A grid pour, the shunt force pad to H1 and to the fuse
  - the line tap from that pour, down the left edge, into R4
  - the fused tap from the fuse, through the MOV line pin, to the upper lead of C1
  - the neutral tie from H3 along the bottom edge into via TV1, where the inner ground plane begins
- That copper stays. Do not redraw it. [gerber/README.md](gerber/README.md) says which file is which.

## What you still execute, and what you do not invent

Everything else in the netlist is not yet copper. A 0.25 mm grid cannot hold a 0.60 mm via pad next to a 0.50 mm pitch pad without a short, and a shorted Gerber is worse than an honest ratsnest. Fan the remaining nets from [netlist.txt](netlist.txt) with these rules and stop:

- 4-layer, 1.6 mm, FR-4. Stack in [STACKUP.md](STACKUP.md). Inner 1 and inner 2 are already the plane windows in the Gerber.
- Top and bottom signal, 0.15 mm trace, 0.15 mm clearance, except the mains pours above, which are already wide. Inner 1 is ground. Inner 2 is 3.3 V, only under the logic half, x greater than 46 mm. QS_VDD is not that plane. It is the net after R23, on the top.
- Mains copper, everything left of x = 46 mm, stays on the top. No ground plane under it. Line-to-neutral spacing on the top is 2.5 mm minimum. The released pours already clear that. Board edge to any mains copper is 3 mm minimum.
- Kelvin sense from RS.SG and RS.SI is a pair of 0.25 mm traces to R11 and R10. They do not share copper with the force path or with the supply.
- The supply taps L_GRID, on the grid side of the shunt, so the meter's own current is not in the integral. The fuse is that tap. It is not in the 40 A path.
- EC-MINT1 is the only SPI master of the QS7001. J4 pin 4 is the only radio conductor, and it is an output. Do not add a trace from the radio back to U3 or U4.
- J5 is a factory pogo row. After calibration it is covered by the mesh. It is not a connector a person can touch.
- Via drill 0.30 mm, via pad 0.60 mm, only in open channel or in a power pad. Do not via under the line copper. TV1 is the one via already drilled. It ties Neutral to inner 1.

## Do not redesign

- Token quantum, gains, and the CF rate are not board options. They are the EC-MINT1 ROM.
- Do not fit the doc-0.9 BOM. The MOV, the LDO, and the divider in that file are the wrong parts. The reasons are in [../../../SOLUTION.md](../../../SOLUTION.md).
- Do not bond the radio to the signer.

## Enclosure

The board is at mains potential. The cover is the insulation.

- Polycarbonate, no metal fastener that reaches a pad.
- A conductive mesh on the inside of the cover lands across SW1. Opening the cover opens that contact.
- VEMT3700 looks at a light well. Light on that sensor must reach PT1. A sealed cover keeps it dark.
- No user connector. The radio antenna is the module on J4, inside the plastic.
- Hipot and creepage are the board house's process check against IEC 62052-31 for a 240 V class II meter. The spacing numbers above are the layout rule. They are not a certificate.

## Order

One panel, two circuits, both stuffed the same. Mark one GEN and one GRID in the silkscreen after the pair is serialized. The meter id itself is burned into EC-MINT1 at the provision jig, not by the stencil.
