A plain index can't fully fix this. `ORDER BY SUM(total) ... LIMIT 50` needs every customer's 30-day total before Postgres can pick the top 50, so it always aggregates the whole window. What you can control is how cheaply it reads those rows. Nine seconds almost certainly means a sequential scan of all 40M rows.

Run this first to confirm:

```sql
EXPLAIN (ANALYZE, BUFFERS) <your query>;
```

## 1. Covering index (try this first)

```sql
CREATE INDEX CONCURRENTLY orders_created_cust_total_idx
  ON orders (created_at) INCLUDE (customer_id, total);
VACUUM (ANALYZE) orders;   -- sets the visibility map so index-only scans work
```

- Postgres can then do an **index-only scan** over just the last 30 days and never touch the heap.
- If 30 days is about 2–3% of the table (say 1M rows), expect roughly 9s → 200–500ms.
- `created_at` must be the **leading** column. `(customer_id, created_at)` would be the wrong order for this query.
- Keep autovacuum aggressive on this table. Otherwise the visibility map goes stale, and "index-only" scans end up reading the heap anyway. Check the `Heap Fetches` line in EXPLAIN.
- If the plan shows the HashAggregate spilling to disk ("Disk Usage" / batches > 1), raise `work_mem` for this query:

```sql
SET LOCAL work_mem = '256MB';
```

**Cheaper alternative if the table is append-only and rows are inserted roughly in `created_at` order:**

```sql
CREATE INDEX ON orders USING brin (created_at);
```

This index is tiny and skips old blocks well, but it still reads the heap for the rows it keeps.

## 2. Partition by month on `created_at`

For a 40M-row, time-series-shaped table this is a good long-term change. Partition pruning means the query only touches 1–2 partitions, and dropping old data becomes cheap.

## 3. Pre-aggregate (the real fix for a dashboard or hot path)

If this query runs often, stop scanning raw orders:

```sql
CREATE TABLE customer_daily_totals (
  day         date,
  customer_id bigint,
  total       numeric,
  PRIMARY KEY (day, customer_id)
);
-- maintain via trigger, or a periodic job:
-- INSERT ... SELECT created_at::date, customer_id, SUM(total) ... ON CONFLICT DO UPDATE
```

```sql
SELECT customer_id, SUM(total)
FROM customer_daily_totals
WHERE day >= current_date - 30
GROUP BY customer_id
ORDER BY 2 DESC
LIMIT 50;
```

That's about 30 × (active customers per day) rows instead of millions, so it typically runs in milliseconds. The catch is that you lose partial-day precision at the window edge. If you need exact results, add today's raw rows on top. A materialized view refreshed every few minutes works too if slightly stale results are OK.

## Recommendation

Add the covering index and vacuum, then check EXPLAIN. If that's fast enough, you're done. If this backs a frequently hit page, or the 30-day window holds many millions of rows, go straight to the rollup table.
