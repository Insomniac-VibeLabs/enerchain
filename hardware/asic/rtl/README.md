# RTL

Edition: v0.0.1 (doc-1.3).

`ec_mint1.v` is the top. It instantiates `ec_mint1_schedule.v` (the net-export schedule), three `spi_byte.v` masters (FRAM, STPM32, QS7001) and `uart_tx.v`. That is the netlist. Run it with:

```sh
iverilog -g2012 -o /tmp/ec_mint1 hardware/asic/rtl/{ec_mint1,ec_mint1_schedule,spi_byte,uart_tx}.v \
  hardware/asic/tb/models.v hardware/asic/tb/tb_ec_mint1.v && vvp /tmp/ec_mint1
python3 tools/check_rtl.py   # same run, compared with the Python model
```

`keccak_round.v` and `ntt_butterfly.v` are the doc-0.8 sketches. They are not instantiated. The butterfly is written with a modulo operator so the arithmetic is obvious, which is also why it is not a mask set. Leave them in the tree as the record of what was considered and rejected. `hardware/rtl/mint_schedule.v` is the doc-0.9 schedule; it is superseded by `ec_mint1_schedule.v`.
