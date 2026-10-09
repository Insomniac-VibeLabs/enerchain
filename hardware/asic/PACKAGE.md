# EC-MINT1 package

Edition: doc-1.1. The assembly house builds this drawing. It does not redesign the leadframe.

## Body

- QFN-32, 5.00 × 5.00 × 0.90 mm, 0.50 mm pitch
- Lead width 0.25 mm, lead length 0.40 mm
- Exposed pad 3.10 × 3.10 mm, tied to VSS inside the package
- Pin 1 mark: laser dot on the top, 0.30 mm, over the pin-1 corner
- Mold compound: halogen-free, MSL 3, 260 °C peak reflow
- Bond wire: 25 µm gold or copper, whatever the OSAT’s qualified stack is for this leadframe. Wire assignment is the pin table in [PINOUT.md](PINOUT.md)

## Board land

Matched on EC-SEAL1 and repeated here so the two houses share one number:

- Toe pad 0.30 × 0.70 mm
- Pad center 2.70 mm from the package center
- Exposed-pad land 3.10 × 3.10 mm, with a 3×3 array of 0.30 mm vias, 1.00 mm pitch, tented on the bottom
- Paste on the exposed pad is 60% of the land, four windows, so the package does not float

## Die

- Standard-cell die, pad ring only. No full-custom analog other than the foundry’s qualified 3.3 V digital I/O and a 1.2 V core regulator from their library
- Target die 2.0 × 2.0 mm is enough for this gate count. Do not grow the die to add a processor
- XI is a fail-safe 3.3 V CMOS input. Do not add a Pierce oscillator
- ZEROIZE and RST_N are asynchronous inputs into the synthesized reset tree

## Test

- Stuck-at on the schedule: 1000 rising edges on CF_IN produce one MINT pulse and a UART record whose `n` is 1 and whose `W` increased by 1000. The vector is [tb/tb_schedule.v](tb/tb_schedule.v) and the passing executable spec is [../../tools/check_schedule.py](../../tools/check_schedule.py)
- Provision: shift a ROM, observe CAL_LOCKED rise, observe that PROV_MISO never toggles with the ROM bits
- Zeroize: a high on ZEROIZE while CS is idle produces two `5C` bytes on QS_MOSI and then QS_RST_N stays low
- No vector reads a key, because this die does not hold one

## What the foundry still does

Place, route, DRC, LVS, and GDSII, on the process they are already qualified for, using [constraints/ec_mint1.sdc](constraints/ec_mint1.sdc). That is mechanical closure. Changing the schedule, adding a CPU, or connecting the radio to the signer SPI is a different part, and it is a reject.
