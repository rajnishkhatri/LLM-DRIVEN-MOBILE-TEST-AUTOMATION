---
type: reference
title: 'Finance basics'
description: 'Asset, instrument, and security are nested terms. An order is an instruction, a trade is the exchange, a transaction is the record. Clearing confirms; settlement transfers.'
tags: [financial-data-architecture, finance, instruments, markets]
---

# Finance basics

**See also:** [introduction](introduction.md) · [generation / trade lifecycle](data-generation.md) · [sources](data-sources.md) · [reference data](reference-data.md)

This is the vocabulary the rest of the bundle uses. It is for architects and engineers, not a substitute for a markets textbook.

## Assets, instruments, and securities

| Term | Meaning | Examples |
|---|---|---|
| **Financial asset** | Intangible thing that holds monetary value — cash held, ownership, or a contract that pays later | Shares, bonds, loans, cash, derivatives |
| **Financial instrument** | A *contract* that creates a financial asset for one party and a financial liability for another. Value follows rules the buyer and seller agreed | Bonds, stocks, swaps, options, loans |
| **Financial security** | A *subset* of instruments that are tradable on an exchange or off-exchange and have a market value. Ownership (equity) or a creditor relationship (debt) | Stocks, bonds |

Some instruments (loans, private contracts) are not easily tradable. **Securitisation** pools them and sells shares of the pool so they become securities.

## Bonds and fixed income

A **bond** is a debt instrument: the buyer lends money to a company or government for a defined term at a fixed or variable rate. Bonds are generally treated as less risky than stocks.

**Fixed income** is the broader class: bonds, certificates of deposit (CDs), preferred stocks — anything that aims at predictable income. All bonds are fixed-income instruments; not all fixed-income instruments are bonds.

## Derivatives

A **derivative** derives its value from an underlying (stock, bond, currency, index, commodity). Uses: hedging (reduce risk), speculation (bet on price), arbitrage (exploit price differences).

| Kind | Contract |
|---|---|
| **Option** | Right, not obligation, to buy or sell at a strike price on or before a date |
| **Future** | Obligation to buy or sell at a set price on a future date |
| **Swap** | Exchange one cash-flow type for another (e.g. fixed rate for floating) |

Derivatives are usually the hardest instrument class to model: they depend on underlyings, have many contract shapes, and need sophisticated pricing.

## Indices and funds

An **index** is a statistical measure of a group of assets (S&P 500, Dow Jones Industrial Average). Portfolios use indices as benchmarks: beat the index or lag it.

A **fund** pools money from many investors into a portfolio run by a manager.

| Kind | Shape |
|---|---|
| **Mutual fund** | Diversified portfolio of stocks, bonds, or other securities |
| **ETF** | Like a mutual fund, but trades on an exchange like a stock |
| **Hedge fund** | Typically more complex, less regulated; sophisticated strategies |

## Order, trade, and transaction

Buy 10 shares of GOOGL at market:

| Term | What happened |
|---|---|
| **Order** | Instruction to the broker: “buy 10 GOOGL at the current market price” |
| **Trade** | Broker finds a seller; shares and money change hands |
| **Transaction** | The *record* of that trade — quantity, price, date, time |

Architects often collapse these three. Do not. Order state, execution state, and the booked record live on different systems and have different identifiers. See the [trade lifecycle](data-generation.md#trade-lifecycle-a-security-purchase).

## Exchanges, OTC, clearing, and settlement

**Securities exchanges** are regulated marketplaces (NYSE, Nasdaq, LSE, CME). They give a transparent venue for matching.

Many trades never hit an exchange. **Over-the-counter (OTC)** is a direct deal between parties — used for customised or less standardised instruments.

| Term | Role |
|---|---|
| **Clearing** | Confirm what was bought/sold, price, quantity; manage risk between agreement and final exchange |
| **Settlement** | Transfer the asset to the buyer and the funds to the seller. Completes the transaction |

**Architect takeaway:** model the contract and the lifecycle, not “a row called trade.” Instrument vs security, order vs execution vs booking, and exchange vs OTC each imply different identifiers, venues, and downstream systems.
