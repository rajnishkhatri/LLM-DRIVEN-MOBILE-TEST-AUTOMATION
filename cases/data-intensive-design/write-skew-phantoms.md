---
type: analysis
title: 'Write skew and phantoms'
description: 'Two transactions read the same fact, write different objects, and break an invariant. Snapshot isolation does not see it. Phantoms are writes that change another transaction’s search. Serializability, or a lock you can actually attach.'
tags: [data-intensive-design, transactions, write-skew, phantom, isolation]
---

# Write skew and phantoms

**See also:** [chapter overview](transactions-overview.md) · [lost updates](lost-updates.md) · [snapshot isolation](snapshot-isolation.md) · [serializability](serializability.md) · [conflict resolution](conflict-resolution.md) · [references](transactions-references.md)

Dirty writes and [lost updates](lost-updates.md) are two
transactions writing the **same** object. That is not the whole
list.

Hospital on-call ([55](transactions-references.md),
[56](transactions-references.md)): at least one doctor must remain.
Aaliyah and Bryce are both on shift, both unwell, both click “go
off call” at once (Figure 8-8). Each transaction, under
[snapshot isolation](snapshot-isolation.md), sees two doctors on
call, concludes it is safe, and updates **its own** row. Both
commit. Zero doctors.

## Characterizing write skew

Not a dirty write, not a lost update — two objects. If the
transactions had run serially, the second would have been
refused. The bug is concurrency.

Write skew **generalizes** lost update: both transactions read
the same objects, then each writes *some* of them (possibly
different ones). Same object → dirty write or lost update,
depending on timing.

Prevention is narrower:

| Tool | Helps write skew? |
|---|---|
| Atomic single-object ops | No — several objects |
| Automatic lost-update detection (PG repeatable read, Oracle serializable, SQL Server snapshot, MySQL RR) | No ([30](transactions-references.md)) |
| Uniqueness / FK / check on one row | Only if the invariant fits one row |
| Multi-object constraint (trigger, materialized view) | Rarely built-in ([12](transactions-references.md); [ACID consistency](acid.md#consistency)) |
| `SELECT … FOR UPDATE` on the rows you read | Yes, if those rows exist |
| [Serializable isolation](serializability.md) | Yes |

Doctors, with a lock:

```sql
BEGIN TRANSACTION;
SELECT * FROM doctors
  WHERE on_call = true AND shift_id = 1234
  FOR UPDATE;
UPDATE doctors SET on_call = false
  WHERE name = 'Aaliyah' AND shift_id = 1234;
COMMIT;
```

## More shapes

Once you look, write skew is common:

**Meeting room** ([57](transactions-references.md)). Check for
overlap, then insert. Snapshot isolation lets two users both see
“free” and both insert.

```sql
SELECT COUNT(*) FROM bookings
  WHERE room_id = 123
    AND end_time > '2025-01-01 12:00'
    AND start_time < '2025-01-01 13:00';
-- if zero:
INSERT INTO bookings (room_id, start_time, end_time, user_id)
  VALUES (123, '2025-01-01 12:00', '2025-01-01 13:00', 666);
```

**Multiplayer game.** `FOR UPDATE` on one figure stops a lost
update on that figure. Two figures onto one square is write skew.
A uniqueness constraint on the square may save you; otherwise
not.

**Username.** Check-then-insert is unsafe under snapshot
isolation. A **uniqueness constraint** aborts the second
transaction. Use it.

**Double-spend.** Insert a tentative spend, sum the account,
require a positive total. Two concurrent inserts can both see a
safe sum and together go negative.

The meeting-room case is the same invariant as
[conflict resolution](conflict-resolution.md#types-of-conflict)
on two leaders — there the “fix” is a later chapter; here it is
serializability or a lock.

## Phantoms

The pattern:

1. `SELECT` checks a condition (two doctors, no overlapping
   booking, square empty, name free, balance positive).
2. Application decides from that result.
3. `INSERT` / `UPDATE` / `DELETE` and commit.
4. That write **changes the result of step 1**.

Order can flip: write first, then select, then abort or commit.

Doctors: the row in step 3 was in the step-1 result, so
`FOR UPDATE` has something to lock. The other four examples
check for **absence** and then **insert** a match. Step 1
returns no rows. `FOR UPDATE` locks nothing
([58](transactions-references.md)).

A write that changes another transaction’s search result is a
**phantom** ([4](transactions-references.md)). Snapshot isolation
hides phantoms from **read-only** queries. In read/write
transactions they become write skew. ORM SQL is prone to this
([52](transactions-references.md), [53](transactions-references.md)).

## Materializing conflicts

If there is no row to lock, invent one. Room bookings: a table
of (room, 15-minute slot) for the next six months. `FOR UPDATE`
those slots, then insert the booking as before. The extra table
holds locks, not the booking.

That is **materializing conflicts**: turn a phantom into a lock
on concrete rows ([14](transactions-references.md)). Ugly — the
concurrency mechanism leaks into the data model — and easy to
get wrong. Last resort. Prefer serializable isolation.

**Architect takeaway:** check-then-act on a search condition is
write skew unless you lock the *set* the search depends on, or
you run serializable. Uniqueness constraints are the cheap fix
when the invariant is “this key is taken.” Absence of rows is
the hard case.
