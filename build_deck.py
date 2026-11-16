"""Build the submission deck (readout = 8 slides, then appendix) from out/ results."""
import pathlib, pandas as pd
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT = pathlib.Path(__file__).parent; OUT = ROOT / "out"; FIG = OUT / "figs"
NAVY, RED, GREY, GREEN = RGBColor(0x1b, 0x2a, 0x41), RGBColor(0xc0, 0x39, 0x2b), RGBColor(0x55, 0x5b, 0x63), RGBColor(0x1e, 0x7d, 0x32)

prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]


def slide(title, kicker=None, appendix=False):
    s = prs.slides.add_slide(BLANK)
    if kicker:
        tb = s.shapes.add_textbox(Inches(.5), Inches(.25), Inches(12.3), Inches(.35)).text_frame
        tb.text = kicker; p = tb.paragraphs[0]; p.font.size = Pt(12); p.font.bold = True
        p.font.color.rgb = GREY if appendix else RED
    tb = s.shapes.add_textbox(Inches(.5), Inches(.55), Inches(12.3), Inches(.9)).text_frame; tb.word_wrap = True
    tb.text = title
    for p in tb.paragraphs:
        p.font.size = Pt(26 if not appendix else 22); p.font.bold = True; p.font.color.rgb = NAVY
    return s


def bullets(s, items, left=.5, top=1.6, width=12.3, height=5.5, size=15):
    tf = s.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height)).text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        lvl = 0
        if isinstance(it, tuple):
            lvl, it = it
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ("• " if lvl == 0 else "– ") + it; p.level = lvl
        p.font.size = Pt(size - 2 * lvl); p.space_after = Pt(6); p.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    return tf


def pic(s, name, left, top, width=None, height=None):
    kw = {}
    if width: kw["width"] = Inches(width)
    if height: kw["height"] = Inches(height)
    s.shapes.add_picture(str(FIG / name), Inches(left), Inches(top), **kw)


def table(s, df, left, top, width, height, size=11, fmt=None):
    rows, cols = df.shape[0] + 1, df.shape[1]
    t = s.shapes.add_table(rows, cols, Inches(left), Inches(top), Inches(width), Inches(height)).table
    for j, c in enumerate(df.columns):
        cell = t.cell(0, j); cell.text = str(c)
        cell.text_frame.paragraphs[0].font.size = Pt(size); cell.text_frame.paragraphs[0].font.bold = True
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            cell = t.cell(i, j)
            cell.text = (fmt(v) if fmt else ("" if pd.isna(v) else f"{v:,.3f}" if isinstance(v, float) else str(v)))
            cell.text_frame.paragraphs[0].font.size = Pt(size)
    return t


def note(s, text, top=6.85):
    tf = s.shapes.add_textbox(Inches(.5), Inches(top), Inches(12.3), Inches(.5)).text_frame; tf.word_wrap = True
    tf.text = text; tf.paragraphs[0].font.size = Pt(11); tf.paragraphs[0].font.italic = True; tf.paragraphs[0].font.color.rgb = GREY


from types import SimpleNamespace
dec = SimpleNamespace(**pd.read_csv(OUT / "p2_decomposition.csv", index_col=0).iloc[:, 0].to_dict())
adj = pd.read_csv(OUT / "p3_adjusted.csv")
m4 = SimpleNamespace(**pd.read_csv(OUT / "p4_metrics.csv", index_col=0).iloc[:, 0].to_dict())

# =========================== READOUT (8 slides) ===========================
s = slide("Nothing broke: ARPDAU fell because we bought cheaper players.\nRevenue nearly tripled.", "READOUT · for the Product Director")
bullets(s, [
    f"ARPDAU fell {dec.pct_change:.0%} (Jan 1–30 vs Apr 1–30), but it rose in every country tier (+2% to +12%). "
    f"At January's tier mix, April ARPDAU would be {dec.pct_change_mix_held:+.1%}.",
    "Cause: a paid_video campaign that ramped from 23 Feb bought mostly Tier-4 players (India, Egypt, Indonesia, Philippines, Vietnam). "
    "Tier 4 went from 18% to 46% of active player-days.",
    f"Revenue in the 30-day period went from ${dec.revenue_first30/1000:,.0f}k to ${dec.revenue_last30/1000:,.0f}k. The campaign added revenue. Whether it added PROFIT depends on its cost, which is not in this data.",
    "Channels do not differ in player quality once you compare like with like (same tier, platform, install week). Where you buy matters; which ad network you buy through barely does.",
    "Recommendations: (1) retire blended ARPDAU as a health KPI and use tier-mix-adjusted ARPDAU; "
    "(2) judge Tier-4 buying on CPI vs ~$1.10 of 30-day revenue per install; (3) target churn offers only at the top risk decile, and only if the offer is cheap.",
], size=16)

s = slide("Every tier's ARPDAU went up. The average went down because the mix changed.", "1 · WHAT HAPPENED TO ARPDAU")
pic(s, "deck_arpdau.png", .4, 1.45, width=12.5)
note(s, f"Shift-share: within-tier rate effect +${dec.rate_effect:.3f}, mix effect −${-dec.mix_effect:.3f} per DAU. Simpson's paradox. Sale-day spikes cancel out over 30-day windows (two sales in each).", top=6.65)

s = slide("The campaign is worth running only if a Tier-4 install costs less than ~$1.10", "2 · IS THE CAMPAIGN PAYING FOR ITSELF?")
pic(s, "deck_installs.png", .4, 1.5, width=6.6)
pb = pd.read_csv(OUT / "p2_rev30_per_install.csv").pivot(index="country_tier", columns="acquisition_channel", values="rev30_per_install").reset_index()
pb.columns = ["Tier", "organic", "paid_social", "paid_video"]
table(s, pb, 7.3, 1.6, 5.6, 1.8, size=12, fmt=lambda v: f"{v:,.2f}" if isinstance(v, float) else str(v))
bullets(s, [
    "Table: net revenue per install in the first 30 days (USD), installs observed ≥ 30 days.",
    "Tier-4 installs return ~$1.10 in 30 days vs ~$3.50 for Tier 1. Retention is the same (D7 ≈ 25%).",
    "Missing input: CPI by tier × channel. With 30-day payback, buy Tier 4 only below ~$1.10 CPI. With 90-day payback the bar is ~$2.24 (January installs: 90-day revenue ≈ 2.0× 30-day in every tier).",
    "The studio goal is more revenue WITHOUT more marketing spend. A campaign that triples installs almost certainly raised spend, so finance must confirm it was in budget.",
], left=7.3, top=3.6, width=5.7, height=3.3, size=13)

s = slide("Channels deliver the same players once you compare like with like", "3 · ACQUISITION CHANNELS")
pic(s, "p3_channels.png", .4, 1.45, width=7.4)
pv = adj[(adj.metric == "rev30") & (adj.channel == "paid_video")].iloc[0]
d7v = adj[(adj.metric == "d7") & (adj.channel == "paid_video")].iloc[0]
bullets(s, [
    "Naive view (window revenue per player): paid_video looks 60% worse. That's an artefact: its players are newer (30 vs 59 days observed) and 75% Tier 4.",
    f"Like-for-like 30-day revenue: paid_video {pv.diff_vs_organic:+.2f} USD vs organic (95% CI {pv.ci_lo:+.2f} to {pv.ci_hi:+.2f}, p={pv.p_value:.2f}). Not significant.",
    f"D7 retention: paid channels ~1 pt lower ({d7v.diff_vs_organic*100:+.1f} pt, CI {d7v.ci_lo*100:+.1f} to {d7v.ci_hi*100:+.1f}). Probably real but tiny, at the edge of what this sample detects (MDE ≈ 1.2 pt).",
    "Not big enough to move budget between channels. Move budget between countries/tiers based on CPI.",
], left=8.0, top=1.5, width=5.0, height=5.3, size=13)

s = slide("A churn model can find the riskiest players, but offers only pay if they are cheap", "4 · RE-ENGAGEMENT TARGETING")
pic(s, "p4_churn.png", .4, 1.45, width=7.6)
bullets(s, [
    "Churn = no activity in the next 14 days for a player active in the last 7. A 14-day silence is in the top 10% of gaps between play days.",
    f"Logistic regression, tested on April snapshots it never saw: AUC {m4.roc_auc:.2f} (best simple rule {m4.baseline_rule_auc_active28:.2f}). Top decile lapses at 46% vs 19% base rate.",
    "Caveat: most lapsers come back on their own (86% within 45 days), so an offer's real value is only the extra returns it causes.",
    "Rule: target if P(churn) ≥ cost ÷ (uplift × value). Value is about $1.11 per active player-month. Cash offers don't pay, in-game currency offers can.",
], left=8.2, top=1.5, width=4.9, height=5.3, size=13)

s = slide("Rewarded ads: the daily cap is almost never the constraint", "5 · AD ENGAGEMENT")
pic(s, "deck_ads.png", .4, 1.5, width=7.2)
cap = pd.read_csv(OUT / "1d1_cap_hits.csv")
bullets(s, [
    f"Only {cap.loc[cap.cap==5,'share_hit_cap'].iloc[0]:.1%} of ad-watching player-days hit a cap of 5, and {cap.loc[cap.cap==8,'share_hit_cap'].iloc[0]:.1%} hit a cap of 8.",
    "Cap-5 and cap-8 player-days average the same 1.35 completed views. Raising the cap would not add views.",
    "To the product team: demand, not the cap, limits ad views. Better placements and rewards are the lever. The 5/8 split looks like an experiment and it shows no effect.",
    "Data: ad clock was 8 h ahead (fixed), and Mar 5–6 had no ad events at all while players were active, a logging outage. Excluded, not counted as zero. Ask engineering for a backfill.",
], left=7.8, top=1.5, width=5.2, height=5.3, size=13)

s = slide("What I'm confident about and what I'm not", "6 · UNCERTAINTY")
bullets(s, [
    "Confident: the ARPDAU drop is a mix effect. It holds by tier, by platform and by channel, and the timing matches the campaign to the week.",
    "Confident: channel differences in revenue are within noise. 37k installs give ±$0.30 per install, about 12% of the mean.",
    "Not known: campaign cost (CPI). That decides if the campaign was good. Ad revenue sits in finance, so Tier-4 players may be worth more than IAP alone shows.",
    "Not known: offer uplift. The churn model ranks risk, it doesn't say who an offer would save. That needs a holdout test.",
    "Data caveats: ~17% of purchase days have no activity row (activity log under-counts). The device-link field is unreliable. Refunds and duplicate purchase events were removed.",
], size=16)

s = slide("Recommendations", "7 · WHAT TO DO")
bullets(s, [
    "Change the KPI: report tier-mix-adjusted ARPDAU and total revenue next to blended ARPDAU, so a UA campaign isn't read as monetisation breaking.",
    "Get CPI by tier × channel from UA/finance this week. Keep buying Tier 4 only where CPI < 30-day revenue/install (~$1.10), or the 90-day equivalent once observable.",
    "Don't reallocate between paid_social and paid_video on quality. Decide on cost.",
    "Leave the ad cap alone. Test placements/rewards instead, and fix the ad logging gap.",
    "Churn offers: 4-week randomised holdout on the top two risk deciles (≈14% of actives) with an in-game-currency offer, to measure real uplift before spending cash.",
], size=17)

s = slide("Scope: what I did, what I dropped, and why", "8 · TRIAGE")
bullets(s, [
    "Done: Part 1 (all four SQL sets plus data-quality note), Part 2(a) ARPDAU deep dive, Part 3 channel comparison, Part 4 churn model, this readout.",
    "Not done: Part 2(b) sales (the brief asks for one of the two), Part 4b install-value model (optional).",
    "Why 4b is hard: a 90-day label needs installs on or before 30 Jan, about 9,800 players, almost all from before the campaign (Tier 4 = 18%). A model trained on them would be scored on today's 75%-Tier-4 installs it never saw.",
    "With another week: (a) measure how sale purchases shift timing vs add demand (pre/post-sale dips per payer); (b) a 4b model trained on rev30 and scaled up; (c) a survival model of lapse instead of a fixed 14-day label.",
], size=16)

# =========================== APPENDIX ===========================
s = slide("A1 · Data quality: issues found and how each was handled", "APPENDIX", appendix=True)
bullets(s, [
    "Duplicate purchase events: 122 purchase_ids appear twice (same device, pack, amount, hours apart). Kept the earliest. Gross revenue would be ~1% too high otherwise.",
    "Refunds: 226 negative rows with their own id, 224 matching an earlier purchase. Gross revenue excludes them, revenue per player uses net. Total refunds $3,250.",
    "Activity rows missing: 17% of purchase days have no player_day row for that device, evenly across hours and months, so not a time-zone issue. Active day = player_day ∪ purchase day. Otherwise the payer share has payers missing from its own denominator.",
    "Ad clock +8 h: ad timestamps run 14:00→07:59 while all other tables run 06:00→23:59, and 7,732 rows fall on 1 May. Shifted −8 h.",
    "Ad logging outage on Mar 5–6: zero ad rows while DAU is normal. Excluded from ad rates and churn features, not treated as zero.",
    "Late events clamped to 23:59:56 local (185 ad rows share a timestamp). Not duplicates, so kept.",
    "Left-truncation: 16,000 players installed before the window. Excluded from anything measured since install (retention, time to first purchase, channel quality).",
    "original_device_id is unreliable: in half the links the 'original' installed after the device it supposedly precedes, countries differ, and both stay active. Not used to merge players.",
    "currency_spend.currency_value has absurd outliers (up to 75.8M against balances near 2k). Not used for any headline number.",
], size=12)

a1 = pd.read_csv(OUT / "1a_daily_health.csv")
s = slide("A2 · Part 1(a) Daily health by platform (summary of the 240-row daily table)", "APPENDIX · 1(a)", appendix=True)
summ = a1.assign(m=pd.to_datetime(a1.dt).dt.strftime("%Y-%m")).groupby(["m", "platform"]).apply(
    lambda g: pd.Series({"avg DAU": round(g.dau.mean()), "gross rev $": round(g.gross_revenue.sum()),
                         "ARPDAU $": round(g.gross_revenue.sum() / g.dau.sum(), 3),
                         "payer share": f"{(g.payer_share * g.dau).sum() / g.dau.sum():.2%}"})).reset_index()
summ.columns = ["month", "platform", "avg DAU", "gross rev $", "ARPDAU $", "payer share"]
table(s, summ, .5, 1.5, 8, 3.6, size=11, fmt=lambda v: f"{v:,}" if isinstance(v, (int,)) else str(v))
bullets(s, [
    "Full daily table: out/1a_daily_health.csv. SQL: sql/1a_daily_health.sql.",
    "Totals check: DAU-days 669,864 = rows in active_day. Gross $217,593 = sum of de-duplicated positive purchases.",
    "Revenue is aggregated per day before joining to DAU, so no fan-out.",
    "iOS ARPDAU ($0.50) is 2× Android ($0.25), and its payer share is 3.5% vs 1.7%.",
    "ARPDAU spikes every second Thursday/Friday (14-day sale cycle).",
], left=8.8, top=1.5, width=4.3, height=5, size=12)

s = slide("A3 · Part 1(b) Retention cohorts", "APPENDIX · 1(b)", appendix=True)
pic(s, "deck_retention.png", .5, 1.4, height=5.6)
bullets(s, [
    "Population: players installed in the window. Day N = active exactly on install date + N.",
    "Rule for recent cohorts: a cell is blank unless every player in that cohort has reached day N by 30 Apr. A partly observed cell would count players who haven't had the chance to return as churned, which biases it down.",
    "Retention is flat across cohorts (D1 ≈ 47%, D7 ≈ 25%, D30 ≈ 14%), including the campaign cohorts. Tier-4 players are not worse players, just lower spenders.",
    "Point retention is low because people play intermittently (about 1 day in 7). 89% of January installs were still active at some point in April.",
], left=7.0, top=1.5, width=6.0, height=5.4, size=13)

c1 = pd.read_csv(OUT / "1c1_concentration.csv"); c2 = pd.read_csv(OUT / "1c2_time_to_first_purchase.csv"); c3 = pd.read_csv(OUT / "1c3_repeat_gap.csv")
s = slide("A4 · Part 1(c) Spender behaviour", "APPENDIX · 1(c)", appendix=True)
table(s, c1, .5, 1.5, 6.2, 1.0, size=11)
c2b = c2.assign(bucket=c2.bucket.str[2:], share_of_installs=(c2.share_of_installs * 100).round(2).astype(str) + "%")
table(s, c2b, .5, 2.9, 6.2, 2.8, size=11, fmt=lambda v: f"{v:,}" if isinstance(v, int) else str(v))
table(s, c3, .5, 6.0, 12.3, .7, size=11)
bullets(s, [
    "Concentration ranks net revenue per player. Among payers: top 1% = 9%, top 10% = 48%, top 50% = 90% of revenue. Among all players, the top 1% = 40%, because 86% of players pay nothing.",
    "Time to first purchase: in-window installs with ≥30 days observed. 12% pay within 30 days, and of those, about 27% pay in the first 3 days. Pre-window installs are excluded because their true first purchase may predate the data.",
    "Repeat gap (LAG window function, de-duplicated purchases): median 15 days, which matches the 14-day sale cadence. Payers wait for the sale.",
], left=7.0, top=1.5, width=6.0, height=4.4, size=12)

s = slide("A5 · Part 1(d) Ads detail", "APPENDIX · 1(d)", appendix=True)
table(s, cap.fillna("all"), .5, 1.5, 6, 1.3, size=12, fmt=lambda v: f"{v:,}" if isinstance(v, int) else str(v))
bullets(s, [
    "A player-day hits the cap when its highest ad_daily_count ≥ ad_daily_cap. The cap never changes within a player-day (checked). The count includes started and abandoned ads, not only completions.",
    "Completed views per DAU rise slowly from 0.75 to 0.87 (Jan→Apr) and track app versions (4.6.1 → 4.8.1), so newer builds show more ad prompts. Worth confirming with the client team.",
    "reward_amount is in-game currency given away, a cost to the economy. There is no ad revenue in this data.",
    "Action on the outage: backfill from the ad network's own logs (they bill on it, so they have it). Until then, exclude the days.",
], left=.5, top=3.1, width=12.3, height=3.8, size=13)

s = slide("A6 · Part 2(a) method and checks", "APPENDIX · 2(a)", appendix=True)
t2 = pd.read_csv(OUT / "p2_by_tier.csv", header=[0, 1], index_col=0)
tt = pd.DataFrame({"tier": [1, 2, 3, 4], "mix Jan": t2["mix"]["first30"].values, "mix Apr": t2["mix"]["last30"].values,
                   "ARPDAU Jan": t2["arpdau"]["first30"].values, "ARPDAU Apr": t2["arpdau"]["last30"].values})
table(s, tt, .5, 1.5, 6.5, 1.8, size=12)
bullets(s, [
    "Windows: 1–30 Jan vs 1–30 Apr (30 days each, two sale cycles each, so sales don't bias the comparison).",
    f"Overall ${dec.arpdau_first30:.3f} → ${dec.arpdau_last30:.3f} ({dec.pct_change:.1%}). At Jan mix: ${dec.last30_at_first30_mix:.3f} ({dec.pct_change_mix_held:+.1%}).",
    "The same pattern holds by channel (organic and paid_social ARPDAU up, paid_video's blend down as its mix moves to Tier 4) and by platform (Android share 64% → 73%).",
    "Within-tier pay rates also rose (Tier 1 3.55% → 3.91%). Monetisation got slightly better.",
    "Tempting wrong answers: 'monetisation broke' (no tier fell), and 'the April app version hurt spending' (rates rose under 4.8.x).",
    "Country-level trends were not used. Per the brief, they're too noisy.",
], left=7.3, top=1.5, width=5.8, height=5.4, size=12)

s = slide("A7 · Part 3 detail", "APPENDIX · 3", appendix=True)
nv = pd.read_csv(OUT / "p3_naive.csv")
table(s, nv, .5, 1.5, 6.3, 1.3, size=11)
adj_show = adj.assign(**{c: adj[c].round(3) for c in ["diff_vs_organic", "ci_lo", "ci_hi", "p_value", "organic_baseline"]})
table(s, adj_show, .5, 3.1, 7.5, 1.9, size=10)
bullets(s, [
    "Metrics. Engagement: D7 retention = active on install date + 7 (installs ≤ 23 Apr). Revenue: rev30 = net USD in days 0–29 (installs ≤ 31 Mar).",
    "Model: OLS / linear probability with tier, platform and install-week fixed effects, HC1 robust standard errors.",
    "The naive table is the misleading comparison: different observation time and tier mix.",
    "To call a difference real, not an artefact, you need: randomised or geo-matched buying (same country and week across channels), attribution audit (organic may include unattributed paid), and enough power (rev30's detectable gap is ±$0.36 today. Halving it needs ~4× the installs).",
    "4 tests at α = 0.05: after a Bonferroni correction none are significant, so the D7 gap stays 'real but unproven'.",
], left=8.2, top=1.5, width=4.9, height=5.4, size=12)

seg = pd.read_csv(OUT / "p4_segments.csv"); thr = pd.read_csv(OUT / "p4_thresholds.csv")
s = slide("A8 · Part 4 setup, evaluation, results, use", "APPENDIX · 4", appendix=True)
bullets(s, [
    "Setup: weekly snapshots T. Population = players with ≥1 active day in [T−6, T]. Label = no active day in [T+1, T+14]. Features use data ≤ T only: tenure, days since last play, active days 7/28, sessions, playtime, level and level gain, purchases, ads per day (outage-aware), spend events, tier, platform, channel.",
    "Exclusions: none by segment. Snapshots after 16 Apr can't be labelled. Snapshots are spaced so train labels end before test features begin.",
    "Split: out-of-time. Train = 8 snapshots 1 Feb–22 Mar (157k rows). Test = 5 and 12 Apr (69k rows). A random split would leak, since the same player appears in neighbouring weeks.",
    f"Metrics: ROC-AUC {m4.roc_auc:.3f} (ranking), PR-AUC {m4.pr_auc:.3f} vs base {m4.test_base_rate:.3f} (useful when positives are rare), decile calibration. They don't measure whether an offer changes behaviour.",
    "Works worse for: new players (<14 days, AUC 0.66, little history) and payers (0.69). Older players lapse more (32%).",
    "Biggest signals: fewer sessions this week, lower level, less playtime and ad use → higher risk. Longer tenure → higher risk.",
], left=.5, top=1.4, width=6.4, height=5.6, size=11)
table(s, thr.iloc[::2][["threshold", "share_targeted", "precision", "recall", "wasted_offers", "profit_V1", "profit_V5"]], 7.1, 1.5, 6.0, 3.2, size=10)
bullets(s, [
    "Profit = uplift × V × lapsers reached − cost × offers sent (illustrative: cost $0.25, uplift 10%, V in $).",
    "Break-even threshold p* = cost ÷ (uplift × V). With V ≈ $1.11/month, cash offers lose money at every threshold. Near-zero-cost currency offers pay at p ≥ 0.4–0.5 (top 5–8%).",
], left=7.1, top=4.9, width=6.0, height=2.0, size=11)

s = slide("A9 · Dead ends and what I'd do with another week", "APPENDIX", appendix=True)
bullets(s, [
    "Dead end: the first DuckDB DISTINCT on ad_view looked like 185 duplicates. They were real events clamped to end of day, so I kept them.",
    "Dead end: merging devices via original_device_id. The links fail basic consistency checks, so I dropped the idea.",
    "Dead end: weekly ARPDAU trend lines are dominated by the biweekly sale cycle, so I moved to matched 30-day windows.",
    "Next week: sale analysis 2(b), testing whether non-sale days before a sale dip (pull-forward) per payer, and whether total spend per payer rises with sale frequency.",
    "Next week: a hazard/survival lapse model, an offer-uplift experiment design with power calculation, and a 4b install-value model trained on rev30 and reweighted to the current tier mix.",
    "Ask finance for ad revenue by country tier. Tier-4 players watch ads too, so their full value is above IAP-only numbers.",
], size=15)

prs.save(ROOT / "DBMS_LAB_EndSem_Submission.pptx")
print("slides:", len(prs.slides))
