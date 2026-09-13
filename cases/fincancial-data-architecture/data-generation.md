---
type: reference
title: 'Financial data generation mechanisms'
description: 'Markets generate data from trading, payments, issuance, corporate actions, lending, filings, and more. One equity buy leaves records on broker, venue, and clearing systems.'
tags: [financial-data-architecture, generation, trade-lifecycle, orders]
---

# Financial data generation mechanisms

**See also:** [ecosystem](data-ecosystem.md) · [finance basics](finance-basics.md) · [sources](data-sources.md) · [reference data](reference-data.md)

The ecosystem is complex because many *kinds* of economic activity generate data, not because one table is wide.

## Mechanisms

| Mechanism | What it generates |
|---|---|
| **Trading** | Buy/sell execution for stocks, bonds, derivatives on exchanges and OTC |
| **Payments and transactions** | Retail purchases, bank transfers, corporate payments, settlements |
| **FX markets** | Spot, forward, and swap currency conversions |
| **Securities issuance** | New stocks and bonds (IPOs, debt offerings) plus identifiers and terms |
| **Corporate actions** | Mergers, dividends, stock splits, buybacks |
| **Lending and credit** | Loans, mortgages, credit lines — approval and disbursement |
| **Financing** | Capital raised through debt or equity |
| **Regulatory and compliance filings** | Mandatory reports (e.g. SEC, Basel III) |
| **Macroeconomic and policy** | Central-bank rates, fiscal policy, economic reports |
| **Investment and asset management** | Portfolio allocation, funds, PE/VC, acquisitions, private markets |
| **Speculation and hedging** | Derivatives and other instruments used to take or offset risk |
| **Insurance and risk** | Underwriting, claims, actuarial assessments |
| **Messaging and communication** | Trade instructions, confirmations, announcements via SWIFT, FIX, ISO 20022 |
| **Operational instructions and reconciliations** | Settlement instructions, affirmations, back-office reconciliation |

## Trade lifecycle: a security purchase

One share purchase is enough to see why “the trade table” is a lie. Production systems add compliance checks, audit trails, instrument identifiers, and legal-entity data on top of the fields below.

### 1. Order placement

The investor instructs a broker. The broker records the order.

| Field | Meaning |
|---|---|
| OrderID | Unique identifier for this order |
| AccountID | Investor’s brokerage account |
| TickerSymbol | e.g. AAPL |
| OrderType | Market, Limit, Stop |
| OrderQuantity | Number of shares |
| OrderSide | Buy or Sell |
| Price | Set only for Limit or Stop |
| OrderTimestamp | When the order was placed |
| OrderStatus | Initial: New, Open |

**Order types:** a **market** order executes immediately at the best available price. A **limit** order executes only at the specified price or better. A **stop** becomes a market order once a stop price is reached (limit losses or lock profits).

### 2. Order routing

The broker chooses a venue and records the hop.

| Field | Meaning |
|---|---|
| OrderID | Same order |
| RoutingDestination | Venue identifier |
| RoutingTimestamp | When it was sent |
| RoutingStatus | Sent, Acknowledged |

### 3. Order matching

The venue matches a compatible sell order.

| Field | Meaning |
|---|---|
| MatchID | Successful match |
| MatchingBuyOrderID | Originating buy order |
| MatchingSellOrderID | Corresponding sell order |
| MatchTimestamp | When matched |
| MatchQuantity | Shares in *this* match (partial fills exist) |
| MatchPrice | Match price |

The source table labelled both order-id columns `MatchingBuyOrderID`. The second is the sell-side link; the name above is corrected for use.

### 4. Trade execution

The match becomes an execution. The exchange records fees and the fill.

| Field | Meaning |
|---|---|
| MatchID | Link back to the match |
| ExecutionID | This fill |
| ExecutedQuantity | Shares actually bought |
| ExecutionTimestamp | When executed |
| ExecutedPrice | Fill price |
| ExchangeFees | Venue fees |

### 5. Trade confirmation

The broker confirms to the investor.

| Field | Meaning |
|---|---|
| ConfirmationID | This confirmation |
| ExecutionID | Link to the fill |
| ConfirmationTimestamp | When sent |
| ConfirmedQuantity / ConfirmedPrice | What the client is told |
| TotalAmount | Including fees |
| SettlementDate | When ownership and funds will officially exchange |

### 6. Clearing and settlement

Clearinghouses and settlement providers sit in the middle.

| Field | Meaning |
|---|---|
| ClearinghouseID | Which clearinghouse |
| SettlementInstructionID | This instruction |
| SettlementDate | Official settlement date |
| SettledQuantity / SettledAmount | What actually settled |
| BeneficiaryAccount | Buyer’s account (funds debited) |
| PayerAccount | Seller side of the cash movement |
| SettlementStatus | Pending, Completed |

The source dump reused a “date of official exchange” gloss on `PayerAccount`. Treat that as a source slip; the field is an account identifier, not a date.

### 7. Position update

The brokerage book updates the holding.

| Field | Meaning |
|---|---|
| AccountID | Brokerage account |
| PositionID | This holding |
| TickerSymbol | Shares held |
| QuantityHeld | New total |
| AverageCostBasis | Average price paid (tax and tracking) |
| LatestUpdateTimestamp | When the position changed |

## Why this matters

Even this simplified path writes distinct records on the broker, the venue, and the clearing/settlement stack. Each participant stores a facet: order, routing, match, execution, confirmation, settlement, position. Identifiers (`OrderID`, `MatchID`, `ExecutionID`, `SettlementInstructionID`, `PositionID`) are the join keys — and they are not the same key.

**Architect takeaway:** design for a *trail* across systems, not a single “trade” aggregate. Preserve the identifiers at each hop. Partial fills, routing, and settlement status are first-class states. See [integration](integration-aggregation.md) and [reference data](reference-data.md) for the join problem this creates.
