# EC-SEAL1 stackup

Edition: doc-1.1. 100.0 mm by 70.0 mm, origin at the lower-left corner of the outline.

| Layer | Copper | What is on it |
| --- | --- | --- |
| Top | 1 oz | All mains, all analog, all component pads. Ground and 3.3 V only as short ties to vias, and only to the right of x = 46 mm. |
| Inner 1 | 1 oz | Ground plane, x = 46 mm to 98 mm, y = 2 mm to 68 mm. No copper left of x = 46 mm. |
| Inner 2 | 1 oz | 3.3 V plane, same window as the ground plane. The signer rail QS_VDD is not this plane. It stays on the top, after R23. |
| Bottom | 1 oz | No copper is released on this layer. It is the fanout layer if the top channel is full. No mains. |

Dielectric 1.6 mm finished, FR-4, Tg 150 °C or better. Soldermask both sides, green is fine. Silkscreen top, reference designators from the centroid. Surface finish ENIG. No lead.

Holes in [gerber/ec-seal1-PTH.drl](gerber/ec-seal1-PTH.drl). The three 3.2 mm holes are the line and neutral studs. The 1.2 mm pair is the fuse. TV1 is the 0.30 mm via at (48, 5) mm, Neutral into the inner ground plane. Any further signal via is 0.30 mm drill, 0.60 mm pad, added where the fanout needs it. Tent the vias on the bottom.

The pours already in the top Gerber are part of the released copper. Replay them. Do not "clean them up." The divider series nodes, the Kelvin pair, the rectifier, and the signer rail are in the netlist and are not in that Gerber yet.
