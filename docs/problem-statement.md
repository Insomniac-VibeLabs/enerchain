# Problem statement

Edition: doc-0.2 (2026-10-08).

## Plain language

The economy keeps score with money that is not energy. The machines that do the work run on energy. Enerchain is a proposal to keep one public score that increases when electrical energy is produced and delivered, and to let that score be traded. It is an open question, not a result.

## Technical statement

Settlement media in general use are liabilities: deposits, notes, and state obligations. They are not dimensioned in joules. Electricity, by contrast, is an input to computation, manufacturing, transport, and communications, and empirical growth studies find that energy scarcity constrains output more tightly than energy abundance does [Stern 2011].

Generation is already measured, but the measurement usually dies in a utility account or a certificate registry. Attribute certificates can be double-counted or mixed up with offsets if the registry rules are loose [Gillenwater 2008; Brander, Gillenwater, and Ascui 2018]. Ledger projects in the energy sector have proliferated without a shared evidence standard for the meter reading they settle [Andoni et al. 2019].

Enerchain’s problem statement is:

> Can issuance of a transferable unit be bound to evidenced electrical delivery, with public verification, without a single organization holding the right to declare delivery?

Binding issuance to delivery does not, by itself, make the unit a stable store of value, a means of retail payment, or a redeemable claim on a kilowatt-hour. Those are separate hypotheses and are not assumed here. The measurement-versus-price split is in [WHITEPAPER.md](../WHITEPAPER.md). The evidence gap is in [energy-verification.md](energy-verification.md).
