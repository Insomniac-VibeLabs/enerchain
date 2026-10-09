# Fabrication pack

Edition: doc-1.1 (2026-10-09). The doc-0.9 notes below this heading are kept so the old links still resolve. Do not build from them.

## Build this

The board order is [ec-seal1/](ec-seal1/). Start at [ec-seal1/MANUFACTURER.md](ec-seal1/MANUFACTURER.md). The chip order is [../asic/](../asic/).

Do not stuff [BOM.csv](BOM.csv). The MOV in that file conducts on a 240 V crest, the LDO in that file is rated 6 V and is fed from a 12 V zener, and the divider in that file drives the STPM32 past its pin rating. The corrections are in [../../SOLUTION.md](../../SOLUTION.md).

The signer is a SEALSQ QS7001, not a VaultIC 409. The QS7001 pinout is public. The VaultIC pinout was not.

## What doc-0.9 said, and why it is still here

A board house builds from Gerber or ODB++, a drill file, a centroid file, and a BOM. Doc-0.9 had the BOM and the netlist and said the plots did not exist yet. They exist now, for EC-SEAL1, and they are not a complete QFN fanout. The manufacturer file says which copper is finished.

Do not send the SVG sheets in `docs/schematics/` as fabrication artwork. They are design drawings, and several of them draw the parts doc-1.1 rejected.
