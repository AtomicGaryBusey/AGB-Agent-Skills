Since the query has to add up every order in the last 30 days, the key number is how many rows that window holds, not the table's 40M. An index can make reading those rows cheap. It can't skip the `SUM`/`GROUP BY` work, and the top-50 can't come from an index because it's ordered by a computed sum.

## 1. Check the plan first

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT customer_id, SUM(total) FROM orders
WHERE created_at >= now() - interval '30 days'
GROUP BY customer_id ORDER BY 2 DESC LIMIT 50;
```

At 9s, you're almost certainly getting a `Seq Scan` on `orders`. Also look for a HashAggregate that reports `Disk Usage` or `Batches: >1`. That means the aggregation is spilling to disk.

## 2. Add a covering index (usually the biggest single improvement)

```sql
CREATE INDEX CONCURRENTLY orders_created_at_cov
  ON orders (created_at) INCLUDE (customer_id, total);
VACUUM (ANALYZE) orders;  -- visibility map needed for index-only scans
```

- `created_at` goes first because it's the range filter. `INCLUDE` puts the other two columns in the index, so Postgres can do an **Index Only Scan** of just the 30-day slice without visiting the table.
- An index on `(customer_id, created_at)` is the wrong order here. It would still scan the whole index.
- If 30 days is about 5–10% of the table, expect this to drop from roughly 9s to a few hundred ms up to about 1s. If the window is a large share of the table, the planner will ignore the index, and you need option 4.
- If the table gets heavy updates, index-only scans degrade until the next vacuum. Tune autovacuum for this table so it runs often enough.

## 3. Cheap tuning to go with it

```sql
SET work_mem = '256MB';                    -- per session/role; keeps the hash agg in memory
SET max_parallel_workers_per_gather = 4;   -- parallel index-only scan + partial aggregate
```

## 4. If it has to be consistently fast (under 50 ms): pre-aggregate

Keep a daily rollup table so the query reads about 30 × (active customers) rows instead of millions of orders:

```sql
CREATE TABLE customer_daily_totals (
  customer_id bigint,
  day         date,
  total       numeric,
  PRIMARY KEY (day, customer_id)
);

-- maintain via trigger, or a job that re-aggregates today + yesterday every few minutes:
INSERT INTO customer_daily_totals
SELECT customer_id, created_at::date, SUM(total)
FROM orders
WHERE created_at >= current_date - 1
GROUP BY 1, 2
ON CONFLICT (day, customer_id) DO UPDATE SET total = EXCLUDED.total;

-- query:
SELECT customer_id, SUM(total)
FROM customer_daily_totals
WHERE day >= current_date - 30
GROUP BY customer_id ORDER BY 2 DESC LIMIT 50;
```

This uses day boundaries, not `now() - 30 days` to the second. If exact precision matters, add the partial first day from `orders` using the index from option 2.

A simpler option is a `MATERIALIZED VIEW` of the query itself, refreshed with `REFRESH MATERIALIZED VIEW CONCURRENTLY` on a schedule. That works if a few minutes of staleness is fine.

## 5. Longer term, if the table keeps growing

Partition `orders` by month on `created_at`. The query then only touches one or two partitions, and dropping or archiving old data gets cheap. If rows are append-only and `created_at` follows insert order, a `BRIN` index on `created_at` is a small, cheap alternative. It lets Postgres skip old blocks, but it won't give you index-only scans.

**Recommendation:** add the covering index from option 2 and raise `work_mem`, then check the new plan. If it's still too slow, or this query runs on a dashboard or hot path, build the daily rollup from option 4.
