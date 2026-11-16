# DBMS Lab End-Sem — Player telemetry analysis

**Submission deck:** `DBMS_LAB_EndSem_Submission.pptx` (slides 1–8 = readout, the rest = appendix).

## How to run

Put the five CSVs in `csv/`, then:

```bash
python3 -m venv .venv && .venv/bin/pip install duckdb pandas scikit-learn statsmodels matplotlib python-pptx scipy
.venv/bin/python run_part1.py        # loads CSVs into game.duckdb, cleans, runs Part 1 SQL -> out/1*.csv
.venv/bin/python part2_arpdau.py     # Part 2(a) ARPDAU deep-dive -> out/p2_*
.venv/bin/python part3_channels.py   # Part 3 channel comparison  -> out/p3_*
.venv/bin/python part4_churn.py      # Part 4 churn model          -> out/p4_*
.venv/bin/python make_charts.py      # deck charts                 -> out/figs/
.venv/bin/python build_deck.py       # builds the .pptx
```

## Files

| File | What it does |
|---|---|
| `sql/00_load.sql` | Loads raw CSVs as `raw_*` tables |
| `sql/01_clean.sql` | Cleaning layer — every data-quality fix, commented |
| `sql/1a_daily_health.sql` | 1(a) DAU, gross revenue, ARPDAU, payer share by day × platform |
| `sql/1b_retention.sql` | 1(b) install-week retention grid (D1/7/14/30) with censoring rule |
| `sql/1c_spenders.sql` | 1(c) revenue concentration, time-to-first-purchase, repeat gap (LAG) |
| `sql/1d_ads.sql` | 1(d) cap-hit share by cap value, daily ad views |
| `part2_arpdau.py` | Shift-share decomposition of the ARPDAU drop |
| `part3_channels.py` | Naive vs adjusted channel comparison, robust CIs, MDE |
| `part4_churn.py` | Churn definition, out-of-time logistic regression, threshold economics |
| `out/` | Every number in the deck, as CSV |

## Data-quality issues (summary — full list on appendix slide A1)

1. **Duplicate purchase events** — 122 `purchase_id`s logged twice → keep earliest.
2. **Refunds** — 226 negative rows → excluded from gross revenue, netted in per-player revenue.
3. **Missing activity rows** — 17% of purchase days have no `player_day` row → active day = player_day ∪ purchase day.
4. **Ad clock 8 h ahead** — shifted −8 h; **ad logging outage 5–6 Mar** — excluded, not zero.
5. **Left-truncated players** — 16,000 installed before the window → excluded from since-install metrics.
6. **`original_device_id` unreliable** — not used to merge players.
7. **`currency_value` outliers** (up to 75.8M) — table not used for headline numbers.
