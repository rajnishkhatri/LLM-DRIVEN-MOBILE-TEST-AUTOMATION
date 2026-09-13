---
type: analysis
title: 'Sharding for multitenancy'
description: 'SaaS tenants are self-contained datasets. One shard per tenant (or a group of small ones) buys isolation, cells, restore, and residency — until one tenant outgrows a node.'
tags: [data-intensive-design, sharding, multitenancy, cell-based, data-residency]
---

# Sharding for multitenancy

**See also:** [chapter overview](sharding-overview.md) · [law and society](law-and-society.md) · [embedded engines](log-structured-storage.md#embedded-storage-engines) · [schema flexibility](relational-vs-document.md#schema-flexibility-in-the-document-model) · [references](sharding-references.md)

SaaS products and cloud services are often **multitenant**: each
tenant is a customer. Several users may log in on one tenant; each
tenant’s dataset is self-contained. In an email-marketing service,
each business that signs up is typically a tenant — newsletter
sign-ups and delivery data stay separate from other businesses.

Sometimes [sharding](sharding-overview.md) implements that. Either
each tenant gets a shard, or several small tenants share a larger
one. Shards might be physically separate databases
([embedded storage engines](log-structured-storage.md#embedded-storage-engines))
or separately manageable portions of a larger logical database
([7](sharding-references.md)).

## Advantages

| Advantage | What you get |
|---|---|
| **Resource isolation** | An expensive tenant is less likely to starve others on a different shard. |
| **Permission isolation** | A bug in access control is less likely to leak one tenant’s data into another’s if the datasets are physically separate. |
| **Cell-based architecture** | Shard not only storage but application services. A **cell** groups services and storage for a set of tenants and runs largely independently. A fault stays in that cell ([8](sharding-references.md)). |
| **Per-tenant backup and restore** | Restore one tenant without touching others — useful after accidental delete or overwrite ([9](sharding-references.md)). |
| **Regulatory compliance** | GDPR and CCPA give people the right to access and delete personal data. One person per shard turns that into export and delete on that shard ([10](sharding-references.md)). See [law and society](law-and-society.md). |
| **Data residence** | A region-aware database can pin a tenant’s shard to a jurisdiction. |
| **Gradual schema rollout** | Roll [schema migrations](relational-vs-document.md#schema-flexibility-in-the-document-model) one tenant at a time. You catch problems before they hit everyone; doing it transactionally is hard ([11](sharding-references.md)). |

Cell-based architecture is the same isolation bet at a larger grain:
fault domain = set of tenants, not a single process.

## Challenges

1. **A tenant must fit on one node.** If one tenant is too big, you
   still have to shard *inside* that tenant — back to sharding for
   [scalability](sharding-overview.md) ([12](sharding-references.md)).
2. **Many small tenants.** One shard each is too much overhead. Group
   them, then you must move tenants as they grow.
3. **Cross-tenant features.** Joins across shards get harder the
   moment a product wants to connect data across tenants.

**Architect takeaway:** tenant-as-shard is an isolation and
compliance design, not a substitute for a partition key that scales.
Plan the path from “one tenant, one shard” to “one tenant, many
shards” before the first whale arrives.
