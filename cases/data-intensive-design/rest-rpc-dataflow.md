---
type: analysis
title: 'REST, RPC, and service dataflow'
description: 'A network call is not a local call. REST treats that honestly. RPC inherits the encoding’s compatibility rules. Discover, balance, then version the API for a long time.'
tags: [data-intensive-design, encoding, rest, rpc, grpc, service-mesh]
---

# REST, RPC, and service dataflow

**See also:** [chapter overview](encoding-overview.md) · [microservices](distributed-vs-single-node.md#microservices-and-serverless) · [Protocol Buffers](protobuf-schema-evolution.md) · [Avro](avro-schema-evolution.md) · [JSON Schema](textual-and-language-encodings.md#json-schema) · [request routing](request-routing.md) · [references](encoding-references.md)

Processes on a network most often split into clients and servers. The
server exposes an API — a **service**. The web is the familiar case:
browsers `GET` HTML/CSS/JS and `POST` form data over a shared stack
(HTTP, URLs, TLS). Native apps and in-browser JavaScript use the same
transport for application-specific JSON APIs.

Services resemble databases (clients submit and query data) but they
do **not** expose a general query language. The API admits only the
inputs and outputs the service’s business logic allows
([30](encoding-references.md)). That encapsulation is the point.

A service-oriented / [microservices](distributed-vs-single-node.md#microservices-and-serverless)
goal is independent deployability: one team owns one service and
releases often without coordinating every neighbor. Old and new
servers and clients therefore run at once. The encoding of the API
must stay compatible across versions. Compatible APIs are what make
internal migrations of data, services, or whole systems possible.

## Web services

When HTTP is the transport, the service is a **web service** — used
on the public internet and inside private networks:

- A client on a user’s device calling your backend.
- One service calling another in the same organization.
- One organization calling another (payments, OAuth, public APIs).

**REST** builds on HTTP ([31](encoding-references.md),
[32](encoding-references.md)): URLs name resources; HTTP handles cache
control, auth, and content-type negotiation. An API that follows those
principles is RESTful.

Clients still need to know the endpoint and the payload shape. Teams
document that with an IDL. The two common ones:

- **OpenAPI** (Swagger, [33](encoding-references.md)) for JSON web
  services.
- **Protocol Buffers** for gRPC.

A minimal OpenAPI definition:

```yaml
openapi: 3.0.0
info:
  title: Ping, Pong
  version: 1.0.0
servers:
  - url: http://localhost:8080
paths:
  /ping:
    get:
      summary: Given a ping, returns a pong message
      responses:
        '200':
          description: A pong
          content:
            application/json:
              schema:
                type: object
                properties:
                  message:
                    type: string
                    example: Pong!
```

Frameworks (Spring Boot, FastAPI, gRPC) own routing, metrics, caching,
auth. FastAPI writes the server in code and generates the IDL; gRPC
writes the IDL first and generates stubs. Both generate client SDKs.
IDL tools also generate docs, check schema-change compatibility, and
offer a query GUI.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Ping, Pong", version="1.0.0")

class PongResponse(BaseModel):
    message: str = "Pong!"

@app.get("/ping", response_model=PongResponse,
         summary="Given a ping, returns a pong message")
async def ping():
    return PongResponse()
```

## The problems with remote procedure calls

Web services are the latest of a long line. EJB and Java RMI are
Java-only. DCOM is Microsoft-only. CORBA is complex and has no
compatibility story ([34](encoding-references.md)). SOAP / WS-* aimed
at vendor interoperability and drowned in complexity
([35](encoding-references.md), [36](encoding-references.md),
[37](encoding-references.md)).

All of them rest on **RPC** (1970s, [38](encoding-references.md)): make
a network request look like a local function call (**location
transparency**). Convenient, and fundamentally flawed
([39](encoding-references.md), [40](encoding-references.md)):

| Local call | Network request |
|---|---|
| Succeeds or fails from parameters you control | Lost, slow, or the remote machine is down — outside your control. Retry is normal |
| Returns, throws, or never returns | Also: **timeout**. You do not know whether the request arrived |
| Retry is just “call again” | The first request may have landed; retry duplicates work unless the protocol is **idempotent** ([41](encoding-references.md)) |
| Stable latency | Milliseconds on a good day, seconds when congested |
| Pass pointers to local objects | Encode everything as bytes. Fine for small immutables; ugly for large mutable graphs |
| One language, one type system | Two languages; JavaScript’s 2⁵³ number hole returns (see [textual encodings](textual-and-language-encodings.md)) |

There is no point making a remote service look like a local object.
Part of REST’s appeal is that it treats state transfer as a different
thing from a function call.

## Load balancers, service discovery, and service meshes

A client must know where the service lives — **service discovery**.
Hard-coding IP and port works until the server moves or overloads.

Several instances plus request spreading is **load balancing**
([42](encoding-references.md)):

| Approach | What it does | Limit |
|---|---|---|
| Hardware load balancer | Datacenter appliance; one VIP, many backends; fails over on connect error | Specialized kit |
| Software load balancer (NGINX, HAProxy) | Same idea on a standard machine | Still a hop you operate |
| DNS | Many A/AAAA records per name | Slow propagation, cached stale IPs |
| Service discovery (etcd, ZooKeeper) | Registry + heartbeat; client gets live endpoints and metadata (shard, datacenter) | You run a coordination service |
| Service mesh (Istio, Linkerd) | Sidecar or in-process proxy on *both* sides; mTLS and observability at the proxy | Operational complexity |

Kubernetes-heavy, highly dynamic estates often pick a mesh. Databases
and brokers often need their own balancers. Simpler deployments are
better served by a software load balancer.

## Data encoding and evolution for RPC

Clients and servers must deploy independently. Compared with
[databases](dataflow-databases.md) you can assume **servers upgrade
first, clients second**. That means backward compatibility on
*requests* and forward compatibility on *responses*.

The RPC scheme inherits the encoding’s rules:

- gRPC (protobuf) and Avro RPC follow those formats’ compatibility
  rules.
- RESTful APIs usually send JSON (or form/URI-encoded requests).
  Optional request parameters and new response fields are the usual
  compatible changes.

Cross-organization RPC is harder: you cannot force clients to upgrade.
Compatibility may need to last indefinitely. A breaking change often
means **multiple API versions** side by side.

There is no agreement on how a client names the version it wants
([43](encoding-references.md)). REST common practice: version in the
URL or in `Accept`. If clients have API keys, store the selected
version on the server and change it through an admin interface
([44](encoding-references.md)).

**Architect takeaway:** do not hide the network. Version the contract
(OpenAPI or protobuf), not the implementation. Assume old clients
forever when the API crosses an organizational boundary.
