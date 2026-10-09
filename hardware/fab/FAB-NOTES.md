# Fabrication pack

Edition: v0.0.1 (doc-1.2, 2026-10-09). The doc-0.9 notes below this heading are kept so the old links still resolve. Do not build from them.

## Build this

The board order is [ec-seal1/](ec-seal1/), revision B. Start at [ec-seal1/MANUFACTURER.md](ec-seal1/MANUFACTURER.md). The chip order is [../asic/](../asic/). Revision B is a bench prototype until the open items in [../../docs/open-items.md](../../docs/open-items.md) are closed.

Do not build revision A (doc-1.1) either. Its logic ground was Neutral while the shunt sat in Line, its dropper rectifier was reversed, and its signer rail ran through 47 Ω. The review is [../../docs/electrical-review.md](../../docs/electrical-review.md).

Do not stuff [BOM.csv](BOM.csv). The MOV in that file conducts on a 240 V crest, the LDO in that file is rated 6 V and is fed from a 12 V zener, and the divider in that file drives the STPM32 past its pin rating. The corrections are in [../../SOLUTION.md](../../SOLUTION.md).

The signer is a SEALSQ QS7001, not a VaultIC 409. The QS7001 pin map used here is from the vendor summary; confirm it against the full datasheet before ordering (open item O-3).

## What doc-0.9 said, and why it is still here

A board house builds from Gerber or ODB++, a drill file, a centroid file, and a BOM. Doc-0.9 had the BOM and the netlist and said the plots did not exist yet. They exist now, for EC-SEAL1, and they are not a complete QFN fanout. The manufacturer file says which copper is finished.

Do not send the SVG sheets in `docs/schematics/` as fabrication artwork. They are design drawings of revision B, generated from the same values as the netlist; the order is the files in `hardware/fab/ec-seal1/`.
