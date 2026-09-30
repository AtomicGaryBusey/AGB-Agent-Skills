The main cost is that Postgres has to read every order from the last 30 days and sum them before it can sort. `ORDER BY SUM(total) ... LIMIT 50` can't use an index, because the sort key only exists after grouping. Whether an index or a rewrite helps depends mostly on how many rows fall in the 30-day window.

### 1. Covering index (try this first)

```sql
CREATE INDEX CONCURRENTLY orders_created_cust_total_idx
  ON orders (created_at) INCLUDE (customer_id, total);
VACUUM (ANALYZE) orders;   -- sets the visibility map so an index-only scan works
```

This lets Postgres do an **index-only scan** over just the 30-day range, without touching the table. If the window is a small share of the table (say 1–3M of 40M rows), this usually brings the query from about 9s to a few hundred ms.

- **Check that it's index-only:** `EXPLAIN (ANALYZE, BUFFERS)` should show `Index Only Scan` with `Heap Fetches` near 0. If heap fetches are high, autovacuum isn't keeping up on this table, so tune it (for example, lower `autovacuum_vacuum_scale_factor` for `orders`).
- **Order matters:** `(created_at, customer_id, total)` as plain key columns also works. `(customer_id, created_at)` does not, because the range filter has to be on the leading column.
- **BRIN option:** if rows are inserted roughly in `created_at` order, `CREATE INDEX ... USING brin (created_at)` is tiny and cheap to maintain. It still reads the heap, though, so the covering B-tree is usually faster for this query.

### 2. Settings to check in the plan

- **HashAggregate spilling:** if you see `Disk:` or `Batches: >1` on the HashAggregate, raise `work_mem` for this query, e.g. `SET LOCAL work_mem = '256MB'`.
- **Parallelism:** make sure it gets a parallel plan (`max_parallel_workers_per_gather` ≥ 2). Parallel index-only scans with partial aggregation work well here.

### 3. If the window is a large share of the table: pre-aggregate

If 30 days covers something like 20–30% of the table, you're still summing millions of rows on every run, and no index will make that truly fast. Keep a daily rollup instead:

```sql
CREATE TABLE customer_daily_totals (
  day date,
  customer_id bigint,
  total numeric,
  PRIMARY KEY (day, customer_id)
);

-- Refresh from cron/pg_cron, e.g. every few minutes for today plus a full backfill once:
INSERT INTO customer_daily_totals
SELECT created_at::date, customer_id, SUM(total)
FROM orders
WHERE created_at >= current_date
GROUP BY 1, 2
ON CONFLICT (day, customer_id) DO UPDATE SET total = EXCLUDED.total;
```

Then the query only touches about 30 small partitions of data:

```sql
SELECT customer_id, SUM(total)
FROM customer_daily_totals
WHERE day >= current_date - 30
GROUP BY customer_id
ORDER BY 2 DESC
LIMIT 50;
```

This usually runs in milliseconds. The catch is that the window becomes day-aligned rather than an exact rolling 30×24 hours. If you need the exact window, add a small live query on `orders` for the partial edge day. Other ways to get the same result are a materialized view refreshed on a schedule, or TimescaleDB continuous aggregates if you're already using TimescaleDB.

### 4. Longer term

If `orders` keeps growing, **range-partition it by `created_at`** (monthly). This query then only scans one or two partitions, and dropping or archiving old data becomes cheap.

**Recommendation:** add the covering index and vacuum, then run `EXPLAIN (ANALYZE, BUFFERS)`. If it's still over about 500ms, which usually means the window holds a large share of the rows, move to the daily rollup table. If you share the plan output and the row count for the 30-day window, I can say which case you're in.
