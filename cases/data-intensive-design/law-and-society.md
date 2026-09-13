---
type: analysis
title: 'Data systems, law, and society'
description: 'Privacy law and ethics constrain data architecture: right to erasure vs immutable logs, data minimization vs speculative big data.'
tags: [data-intensive-design, trade-offs, privacy, gdpr, ethics]
---

# Data systems, law, and society

**See also:** [chapter overview](overview.md) · [systems of record and derived data](operational-vs-analytical.md#systems-of-record-and-derived-data) · [sharding for multitenancy](sharding-multitenancy.md) · [references](references.md)

The architecture of data systems is influenced not only by technical goals and
requirements, but also by the human needs of the organizations they support.
Increasingly, data systems engineers are realizing that serving the needs of
their own business is not enough; we also have a responsibility toward society
at large.

One particular concern is systems that store data about people and their
behavior. Since 2018, the **GDPR** has given residents of many European
countries greater control and legal rights over their personal data, and
similar privacy regulations have been adopted in various other countries and
states (including, for example, the **CCPA**). Regulations around AI, such as
the **EU AI Act**, place further restrictions on how personal data can be used.

Even in areas that are not directly subject to regulation, there is increasing
recognition of the effects that computer systems have on people and society.
Social media has changed how individuals consume news, which influences
political opinions and hence may affect the outcome of elections. Automated
systems increasingly make decisions that have profound consequences for
individuals: who should be given a loan or insurance coverage, who should be
invited to a job interview, or who should be suspected of a crime
([59](references.md)).

Everyone who works on such systems shares a responsibility for considering the
ethical impact of their decisions and ensuring that they comply with relevant
laws. Not everyone needs to become an expert in law and ethics, but a basic
awareness of legal and ethical principles is just as important as, say, some
foundational knowledge in distributed systems.

## Law as an architectural constraint

Legal considerations are influencing the very foundations of data system design
([60](references.md)). For example, the GDPR grants individuals the right to
have their data erased on request (sometimes known as the **right to be
forgotten**). However, many data systems rely on **immutable constructs** such
as append-only logs as part of their design. That creates engineering
questions, not just policy questions:

- How can we ensure deletion of some data in the middle of a file that is
  supposed to be immutable?
- How do we handle deletion of data that has been incorporated into
  [derived datasets](operational-vs-analytical.md#systems-of-record-and-derived-data)
  — for example, training data for ML models?

At present we don’t have clear guidelines on which particular technologies or
system architectures should be considered GDPR compliant. The regulation
deliberately does not mandate particular technologies, because these may
quickly change. Instead, the legal texts set out high-level principles that are
subject to interpretation. How to comply with privacy regulations has no simple
answer.

## Cost of storage is not just the bill

In general, we store data because we think that its value is greater than the
costs of storing it. The costs of storage extend beyond the bill you pay for
S3 or another service. The cost-benefit calculation should also take into
account:

- The risks of liability and reputational damage if the data were leaked or
  compromised by adversaries.
- The risk of legal costs and fines if storage and processing is found not to
  be compliant with the law ([50](references.md)).
- Compelled handover: governments or police forces might compel companies to
  hand over data. When data could reveal criminalized behaviors (e.g.
  homosexuality in several Middle Eastern and African countries, or seeking an
  abortion in several US states), storing that data creates real safety risks
  for users. Travel to an abortion clinic, for example, could be revealed by
  location data, or even by a log of the user’s IP addresses over time
  (approximate location).

Once all the risks are taken into account, it might be reasonable to decide
that some data is simply not worth storing, and that it should therefore be
deleted.

## Data minimization versus speculative “big data”

This principle of **data minimization** (sometimes known by the German term
*Datensparsamkeit*) runs counter to the “big data” philosophy of storing lots
of data speculatively in case it turns out to be useful in the future
([61](references.md)). Data minimization fits with the GDPR, which mandates
that personal data may be collected only for a specified, explicit purpose;
cannot later be used for any other purpose; and must not be kept for longer
than necessary for the purposes for which it was collected
([62](references.md)).

## Buyer-driven compliance

Businesses have also taken notice of privacy and safety concerns. Credit card
companies require payment processing businesses to adhere to strict **Payment
Card Industry (PCI)** standards. Processors undergo frequent evaluations from
independent auditors to verify continued compliance. Software vendors have also
seen increased scrutiny: many buyers now require vendors to comply with
**Service Organization Control (SOC) Type 2** standards, similarly verified by
third-party audits.

Generally, it is important to balance the needs of your business against the
needs of the people whose data you are collecting and processing.

**Architect takeaway:** treat erasure, purpose limitation, and data
minimization as architecture constraints, not a compliance pass after the
system is built. Immutability, derived copies, and speculative retention all
collide with those constraints — name the collision early.
