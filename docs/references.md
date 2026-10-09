# References

Edition: doc-0.2. Sources below are real. Peer-reviewed items and formal standards are the evidence base. Named industry systems are prior art only.

## Energy and economic activity

Stern, D. I. (2011). The role of energy in economic growth. *Annals of the New York Academy of Sciences*, 1219(1), 26–51. https://doi.org/10.1111/j.1749-6632.2010.05921.x

Stern reviews mainstream, resource, and ecological growth models. Energy constrains growth when it is scarce; the constraint weakens when energy is abundant and when the economy shifts toward higher-quality carriers, especially electricity. Enerchain uses this as support for treating electricity as an economically relevant measured quantity, not as proof that a token minted per kilowatt-hour is a stable currency.

## Wholesale electricity price is already local

Schweppe, F. C., Caramanis, M. C., Tabors, R. D., & Bohn, R. E. (1988). *Spot Pricing of Electricity*. Kluwer. https://doi.org/10.1007/978-1-4613-1683-1

Hogan, W. W. (1992). Contract networks for electric power transmission. *Journal of Regulatory Economics*, 4(3), 211–242. https://doi.org/10.1007/BF00133621

Tan, Z., Cheng, T., Liu, Y., & Zhong, H. (2022). Extensions of the locational marginal price theory in evolving power systems: A review. *IET Generation, Transmission & Distribution*. https://doi.org/10.1049/gtd2.12381

Locational marginal price is the marginal cost of serving one more megawatt-hour at a given node and interval, including generation cost and congestion. The same physical megawatt-hour does not have one price across a network. This is the published basis for Enerchain’s split between universal measurement and regional value.

## Proof-of-work energy cost

de Vries, A. (2018). Bitcoin’s growing energy problem. *Joule*, 2(5), 801–805. https://doi.org/10.1016/j.joule.2018.04.016

Peer-reviewed commentary on the electricity used to order Bitcoin transactions. Cited only for the contrast Enerchain draws with proof of work. Nakamoto’s 2008 Bitcoin paper is a primary design document, not a peer-reviewed energy study, and is not used as evidence here.

## Generation-minted and peer-to-peer energy ledgers

Mihaylov, M., Jurado, S., Avellana, N., Van Moffaert, K., de Abril, I. M., & Nowé, A. (2014). NRGcoin: Virtual currency for trading of renewable energy in smart grids. In *11th International Conference on the European Energy Market (EEM14)*. IEEE. https://doi.org/10.1109/EEM.2014.6861213

NRGcoin is the closest peer-reviewed predecessor: a unit minted for energy injected into a grid, rather than for hash computation, with a separate currency market for the unit’s price. Enerchain is not an implementation of NRGcoin. The paper shows the issuance idea has already been stated and that validation of injection remains part of the design.

Mengelkamp, E., Gärttner, J., Rock, K., Kessler, S., Orsini, L., & Weinhardt, C. (2018). Designing microgrid energy markets: A case study: The Brooklyn Microgrid. *Applied Energy*, 210, 870–880. https://doi.org/10.1016/j.apenergy.2017.06.054

Derives seven components of a microgrid market and finds that regulation blocked a full peer-to-peer market in that case. Cited for market design and for the regulatory constraint.

Andoni, M., Robu, V., Flynn, D., Abram, S., Geach, D., Jenkins, D., McCallum, P., & Peacock, A. (2019). Blockchain technology in the energy sector: A systematic review of challenges and opportunities. *Renewable and Sustainable Energy Reviews*, 100, 143–174. https://doi.org/10.1016/j.rser.2018.10.014

Systematic review of about 140 energy-blockchain efforts. Reports the pattern Enerchain has to design against: ledger experiments outrun settlement with meters, system operators, and law.

## Attribute certificates and double counting

Gillenwater, M. (2008). Redefining RECs—Part 1: Untangling attributes and offsets. *Energy Policy*, 36(6), 2109–2119. https://doi.org/10.1016/j.enpol.2008.02.036

Brander, M., Gillenwater, M., & Ascui, F. (2018). Creative accounting: A critical perspective on the market-based method for reporting purchased electricity (scope 2) emissions. *Energy Policy*, 112, 29–33. https://doi.org/10.1016/j.enpol.2017.09.051

Renewable energy certificates separate a generation attribute from the electrons. Using the same megawatt-hour once as a certificate and again as a minted currency, or once in two registries, is a known accounting failure. Enerchain must define exclusivity before issuance.

## Meter integrity

McLaughlin, S., Podkuiko, D., & McDaniel, P. (2010). Energy theft in the advanced metering infrastructure. In *Critical Information Infrastructures Security (CRITIS 2009)*, LNCS 6027. Springer. https://doi.org/10.1007/978-3-642-14379-3_15

Documents tampering of usage data at the sensor, in the meter, and in transit. Generation-claim fraud is the mirror image of the theft cases they describe.

International Electrotechnical Commission. (2020). *IEC 62053-22: Electricity metering equipment — Particular requirements — Static meters for AC active energy (classes 0.1S, 0.2S and 0.5S)*. Geneva: IEC.

Accuracy class is a standards fact about active-energy meters. It is not, by itself, a tamper proof.

## Interplanetary communications and industry

Burleigh, S., Hooke, A., Torgerson, L., Fall, K., Cerf, V., Durst, B., & Scott, K. (2003). Delay-tolerant networking: An approach to interplanetary Internet. *IEEE Communications Magazine*, 41(6), 128–136. https://doi.org/10.1109/MCOM.2003.1204759

Earth–Mars one-way light time ranges from a little over 3 minutes to about 22 minutes. Synchronous consensus across that gap is not available. Any interplanetary Enerchain settlement has to be delay-tolerant.

Metzger, P. T., Muscatello, A., Mueller, R. P., & Mantovani, J. (2013). Affordable, rapid bootstrapping of the space industry and solar system civilization. *Journal of Aerospace Engineering*, 26(1), 18–29. https://doi.org/10.1061/(ASCE)AS.1943-5525.0000236

Peer-reviewed argument that a space industry is constrained by landed mass and local energy and materials. Cited only to ground the claim that off-Earth settlements would be energy-constrained. It is not evidence for an interplanetary currency.

## Prior art, not evidence

SolarCoin (2014– ). A volunteer registry that has granted tokens against claimed solar generation, historically on the order of 1 token per megawatt-hour. Not peer-reviewed. Included because public commentary has reported that the token price did not cover the cost of the generation it claimed to reward. That is a warning about issuance without a bid for the token, not a result to copy.
