# References

Edition: doc-0.3. Peer-reviewed items and formal standards are the evidence base. Industry systems are prior art.

## Energy and economic activity

Stern, D. I. (2011). The role of energy in economic growth. *Annals of the New York Academy of Sciences*, 1219(1), 26–51. https://doi.org/10.1111/j.1749-6632.2010.05921.x

Energy constrains growth when it is scarce. Economies shift toward higher-quality carriers, especially electricity. Cited for the dependence claim, not as a forecast that a token will be the settlement currency.

## Proof-of-work electricity cost

de Vries, A. (2018). Bitcoin’s growing energy problem. *Joule*, 2(5), 801–805. https://doi.org/10.1016/j.joule.2018.04.016

Peer-reviewed commentary on electricity used to order Bitcoin transactions. Cited for the claim that proof-of-work mining is an electricity cost.

## Generation-minted units and prosumers

Mihaylov, M., Jurado, S., Avellana, N., Van Moffaert, K., de Abril, I. M., & Nowé, A. (2014). NRGcoin: Virtual currency for trading of renewable energy in smart grids. In *11th International Conference on the European Energy Market (EEM14)*. IEEE. https://doi.org/10.1109/EEM.2014.6861213

A unit minted for energy injected into the grid, priced on an exchange.

Parag, Y., & Sovacool, B. K. (2016). Electricity market design for the prosumer era. *Nature Energy*, 1, 16032. https://doi.org/10.1038/nenergy.2016.32

Prosumers both consume and produce. The paper sets out grid integration, peer-to-peer trade, and community groups as the market forms.

Mengelkamp, E., Gärttner, J., Rock, K., Kessler, S., Orsini, L., & Weinhardt, C. (2018). Designing microgrid energy markets: A case study: The Brooklyn Microgrid. *Applied Energy*, 210, 870–880. https://doi.org/10.1016/j.apenergy.2017.06.054

A ledger-operated local energy market, and the regulatory constraint on running one.

Andoni, M., Robu, V., Flynn, D., Abram, S., Geach, D., Jenkins, D., McCallum, P., & Peacock, A. (2019). Blockchain technology in the energy sector: A systematic review of challenges and opportunities. *Renewable and Sustainable Energy Reviews*, 100, 143–174. https://doi.org/10.1016/j.rser.2018.10.014

Review of about 140 energy-blockchain efforts.

## Regional electricity trade

Schweppe, F. C., Caramanis, M. C., Tabors, R. D., & Bohn, R. E. (1988). *Spot Pricing of Electricity*. Kluwer. https://doi.org/10.1007/978-1-4613-1683-1

Hogan, W. W. (1992). Contract networks for electric power transmission. *Journal of Regulatory Economics*, 4(3), 211–242. https://doi.org/10.1007/BF00133621

Tan, Z., Cheng, T., Liu, Y., & Zhong, H. (2022). Extensions of the locational marginal price theory in evolving power systems: A review. *IET Generation, Transmission & Distribution*. https://doi.org/10.1049/gtd2.12381

Locational price is the published form of regional electricity trade on Earth.

## Metering and hardware binding

International Electrotechnical Commission. (2020). *IEC 62053-22: Electricity metering equipment — Particular requirements — Static meters for AC active energy (classes 0.1S, 0.2S and 0.5S)*. Geneva: IEC.

International Organization of Legal Metrology. (2012). *OIML R 46-1/-2: Active electrical energy meters*. Paris: OIML.

WELMEC. *Guide 7.2: Software Guide* (Measuring Instruments Directive 2014/32/EU). Section on active electrical energy meters. https://www.welmec.org/welmec/documents/guides/7.2/2025/WELMEC_Guide_7.2_2025.pdf

Rincón, A. E. R., Melo Jr., W. S., Farias, C. M., & Carmo, L. F. R. C. (2021). Securing smart meters through physical properties of their components. *IEEE Transactions on Instrumentation and Measurement*, 70, 3000511. https://doi.org/10.1109/TIM.2020.3041098

The integral, the token schedule, and the sealed core are specified in [hardware-binding.md](hardware-binding.md). Public posting and the signature scheme are specified in [ledger-nonrepudiation.md](ledger-nonrepudiation.md).

## Post-quantum signatures

Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer. *SIAM Journal on Computing*, 26(5), 1484–1509. https://doi.org/10.1137/S0097539795293172

Grover, L. K. (1996). A fast quantum mechanical algorithm for database search. In *Proceedings of the 28th Annual ACM Symposium on Theory of Computing*, 212–219. https://doi.org/10.1145/237814.237866

NIST. (2024). *FIPS 204: Module-Lattice-Based Digital Signature Standard*. https://doi.org/10.6028/NIST.FIPS.204

NIST. (2024). *FIPS 205: Stateless Hash-Based Digital Signature Standard*. https://doi.org/10.6028/NIST.FIPS.205

## Meter burden

IEC 62052-11. Electricity metering equipment — General requirements, tests and test conditions. Voltage-circuit and current-circuit consumption.

Günther, R. (2021). Self-consumption in the current circuit. CLOU Global. https://clouglobal.com/self-consumption-in-the-current-circuit/

The cap and the schematic are in [meter-burden.md](meter-burden.md) and [schematics/mint-path.svg](schematics/mint-path.svg).

## Interplanetary links and local energy

Burleigh, S., Hooke, A., Torgerson, L., Fall, K., Cerf, V., Durst, B., & Scott, K. (2003). Delay-tolerant networking: An approach to interplanetary Internet. *IEEE Communications Magazine*, 41(6), 128–136. https://doi.org/10.1109/MCOM.2003.1204759

Metzger, P. T., Muscatello, A., Mueller, R. P., & Mantovani, J. (2013). Affordable, rapid bootstrapping of the space industry and solar system civilization. *Journal of Aerospace Engineering*, 26(1), 18–29. https://doi.org/10.1061/(ASCE)AS.1943-5525.0000236

Cited for local energy as a constraint on off-Earth industry, and for delay-tolerant links between regions.

## v0.0.1 hardware and software

Power Integrations. *LNK302/304-306 LinkSwitch-TN family datasheet*. Non-isolated off-line buck converter, 85–265 V ac.

Infineon (Cypress). *FM25V02A 256-Kbit (32K × 8) serial (SPI) F-RAM datasheet*. 2.0–3.6 V, 40 MHz, 10¹⁴ read/write cycles.

Texas Instruments. *LM2936 ultra-low quiescent current LDO voltage regulator datasheet*. 40 V input, 50 mA output.

Analog Devices (Maxim Integrated). *DS3645 secure supervisor with battery-backed key memory and tamper detection*. Cited as the class of part that closes open item O-1.

IEC 60664-1. Insulation coordination for equipment within low-voltage supply systems — Principles, requirements and tests. Creepage and clearance.

SEALSQ. (2025). *QS7001 Quantum Shield* product announcements: RISC-V secure microcontroller with hardware ML-DSA and ML-KEM. The pin map and SDK are under the vendor's NDA; see open item O-3.

Pope, G. *dilithium-py*: pure-Python ML-DSA (FIPS 204), used by the v0.0.1 devnet. https://github.com/GiacomoPope/dilithium-py

## Prior art for energy-backed units

SolarCoin Foundation. (2014). *SolarCoin*: a coin granted per verified MWh of solar generation.

Mihaylov, M., Jurado, S., Avellana, N., Van Moffaert, K., de Abril, I. M., & Nowé, A. (2014). NRGcoin: Virtual currency for trading of renewable energy in smart grids. Cited above.

S.A.F.E. e.V. *Open Charge Metering Format (OCMF)*: signed meter values for EV charging under German calibration law (Eichrecht).
