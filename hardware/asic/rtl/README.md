# RTL

`ec_mint1.v` is the doc-1.1 top. It instantiates `ec_mint1_schedule.v` and `spi_byte.v`. That is the netlist.

`keccak_round.v` and `ntt_butterfly.v` are the doc-0.8 sketches. They are not instantiated. The butterfly is written with a modulo operator so the arithmetic is obvious, which is also why it is not a mask set. Leave them in the tree as the record of what was considered and rejected.
