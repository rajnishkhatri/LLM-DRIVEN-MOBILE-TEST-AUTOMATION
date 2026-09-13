---
type: analysis
title: 'GraphQL'
description: 'GraphQL is a client query contract over any store, not a graph database. It lets the UI request a JSON shape; it deliberately forbids recursive and arbitrary search from untrusted clients.'
tags: [data-intensive-design, data-models, graphql, oltp, api]
---

# GraphQL

**See also:** [chapter overview](data-models-overview.md) · [graph models](graph-data-models.md) · [document model](relational-vs-document.md) · [references](data-models-references.md)

GraphQL is a query language that, by design, is much more **restrictive**
than Cypher, SPARQL, SQL, or Datalog. It is intended for **OLTP** queries:
its purpose is to let client software on a user’s device (mobile app or
JavaScript frontend) request a JSON document with a particular structure,
containing the fields necessary for rendering its UI.

GraphQL interfaces allow developers to change queries in client code
without changing server-side APIs. That flexibility has a cost.
Organizations that adopt GraphQL often need tooling to convert the queries
into requests to internal services, which commonly use REST or gRPC (a
later chapter). Authorization, rate limiting, and performance are
additional concerns ([64](data-models-references.md)).

The language is intentionally limited because GraphQL queries come from
**untrusted sources**. It does not allow anything that could be expensive
to execute; otherwise users could (perhaps unintentionally) cause a
denial-of-service by running lots of expensive queries. In particular,
GraphQL does **not** allow recursive queries (unlike Cypher, SPARQL, SQL,
or Datalog), and it does **not** allow arbitrary search conditions (like
“find people who were born in the US and are now living in Europe”),
unless the service owners specifically choose to offer that search.

## A group-chat example

How you might implement a group chat application like Discord or Slack.
The query requests all channels the user has access to, including the
channel name and the 50 most recent messages. For each message: timestamp,
content, and the sender’s name and profile picture URL. If a message is a
reply, also the name of that sender and the content of the replied-to
message (perhaps rendered in a smaller font above the reply).

```graphql
query ChatApp {
  channels {
    name
    recentMessages(latest: 50) {
      timestamp
      content
      sender {
        fullName
        imageUrl
      }
      replyTo {
        content
        sender {
          fullName
        }
      }
    }
  }
}
```

A possible response mirrors the structure of the query: exactly those
attributes that were requested, no more and no less. The server does not
need to know which attributes the client requires to render the UI; the
client requests what it needs. This query does not request a profile
picture for the `replyTo` sender; if the UI later includes that picture,
the client adds `imageUrl` with no server-side API change.

```json
{
  "data": {
    "channels": [
      {
        "name": "#general",
        "recentMessages": [
          {
            "timestamp": 1693143014,
            "content": "Hey! How are y'all doing?",
            "sender": {"fullName": "Aaliyah", "imageUrl": "https://..."},
            "replyTo": null
          },
          {
            "timestamp": 1693143024,
            "content": "Great! And you?",
            "sender": {"fullName": "Caleb", "imageUrl": "https://..."},
            "replyTo": {
              "content": "Hey! How are y'all doing?",
              "sender": {"fullName": "Aaliyah"}
            }
          }
        ]
      }
    ]
  }
}
```

The name and image URL of a message’s sender are embedded directly in the
message object. If the same user sends multiple messages, this information
is repeated. In principle you could reduce that duplication; GraphQL
accepts a larger response to make it simpler to render the UI from the
requested data.

`replyTo` is similar: the second message replies to the first, and the
content and sender name are duplicated under `replyTo`. You could return
the ID of the message being replied to, but then the client would have to
make an additional request if that ID were not among the 50 most recent
messages. Duplicating the content makes the data easier to work with.

The server’s database can store the data in a more
[normalized](relational-vs-document.md#normalization-denormalization-and-joins)
form and perform the joins to process a query. For example, store a
message with the sender’s user ID and the ID of the message it replies to;
on a query like the one above, resolve those IDs. Only joins **explicitly
declared in the GraphQL schema** can be requested by the client.

Even though the response looks similar to a document-database response,
and even though it has “graph” in its name, GraphQL can be implemented on
top of **any** type of database — relational, document, or graph.

**Architect takeaway:** GraphQL is an untrusted-client query contract, not
a graph store. Use it to let the UI pick a JSON shape without versioning a
REST resource for every screen. Do not confuse it with Cypher/SPARQL: it
cannot traverse arbitrary paths, and that restriction is the point.
