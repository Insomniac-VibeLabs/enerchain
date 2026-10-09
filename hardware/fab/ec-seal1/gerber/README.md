# EC-SEAL1 plot files

Edition: doc-1.1. Units are millimetres. Coordinates match the centroid: origin at the lower left of the outline, y up.

| File | Layer |
| --- | --- |
| ec-seal1-Edge_Cuts.gbr | Board outline, 100 × 70 mm |
| ec-seal1-F_Cu.gbr | Top copper. Lands, the 40 A pours, the divider tap, the fused tap, the neutral tie |
| ec-seal1-B_Cu.gbr | Bottom. Empty on purpose. Fanout goes here if the top channel is full |
| ec-seal1-In1_Cu.gbr | Ground plane, x = 46 to 98 mm, y = 2 to 68 mm |
| ec-seal1-In2_Cu.gbr | 3.3 V plane, same window. Not QS_VDD |
| ec-seal1-F_Mask.gbr | Top solder mask openings |
| ec-seal1-F_Silk.gbr | Plane-cut mark at x = 46 mm |
| ec-seal1-PTH.drl | Studs, fuse, electrolytic, headers, and via TV1 |

No paste Gerber is included. Open the mask over the lands and use 60% paste on the three exposed pads, four windows each, so the QFN packages do not float.

The files this directory does not contain are the QFN escapes, the Kelvin pair, the rectifier, and the signer-rail trace. Those nets are in [../netlist.txt](../netlist.txt). Routing them is mechanical. Choosing a different circuit is not.
