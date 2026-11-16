-- 1(a) Daily health by platform.
-- DAU        = distinct devices in active_day (player_day ∪ purchase days)
-- Gross rev  = sum of positive (non-refund), de-duplicated purchases
-- ARPDAU     = gross revenue / DAU
-- Payer share= distinct purchasing devices that day / DAU
-- Revenue is aggregated per day BEFORE joining to DAU so purchases never
-- fan out across activity rows.
WITH dau AS (
  SELECT a.dt, p.platform, count(DISTINCT a.device_id) AS dau
  FROM active_day a JOIN player p USING (device_id)
  GROUP BY ALL
), rev AS (
  SELECT pc.dt, p.platform,
         sum(pc.usd_amount)             AS gross_revenue,
         count(DISTINCT pc.device_id)   AS payers
  FROM purchase_clean pc JOIN player p USING (device_id)
  WHERE NOT pc.is_refund
  GROUP BY ALL
)
SELECT d.dt, d.platform, d.dau,
       round(coalesce(r.gross_revenue, 0), 2)                    AS gross_revenue,
       round(coalesce(r.gross_revenue, 0) / d.dau, 4)            AS arpdau,
       round(coalesce(r.payers, 0) / d.dau, 4)                   AS payer_share
FROM dau d LEFT JOIN rev r USING (dt, platform)
ORDER BY d.dt, d.platform;
