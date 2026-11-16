"""Deck charts built from out/*.csv (run after run_part1.py, part2-4 scripts)."""
import pathlib, pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).parent; OUT = ROOT / "out"; FIG = OUT / "figs"; FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
TIER_C = {1: "#1b4f8a", 2: "#3f88c5", 3: "#f2a541", 4: "#d1495b"}

# 1. Headline: ARPDAU first30 vs last30, by tier and blended
t = pd.read_csv(OUT / "p2_by_tier.csv", header=[0, 1], index_col=0)
d = pd.read_csv(OUT / "p2_decomposition.csv", index_col=0).iloc[:, 0]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.35, 1]})
labels = ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "ALL\n(blended)"]
f30 = list(t["arpdau"]["first30"]) + [d["arpdau_first30"]]
l30 = list(t["arpdau"]["last30"]) + [d["arpdau_last30"]]
x = np.arange(5); w = .38
a1.bar(x - w/2, f30, w, color="#adb5bd", label="Jan 1–30")
b = a1.bar(x + w/2, l30, w, color=[TIER_C[1], TIER_C[2], TIER_C[3], TIER_C[4], "black"], label="Apr 1–30")
for i, (u, v) in enumerate(zip(f30, l30)):
    a1.text(i + w/2, v + .01, f"{v/u-1:+.0%}", ha="center", fontsize=10, fontweight="bold",
            color="#c0392b" if v < u else "#1e7d32")
a1.set_xticks(x, labels); a1.set_ylabel("ARPDAU (USD)"); a1.legend(frameon=False)
a1.set_title("Every tier's ARPDAU went UP — the blend went DOWN", loc="left", fontweight="bold")
m0, m1 = t["mix"]["first30"], t["mix"]["last30"]
bottom0 = bottom1 = 0
for tier in [1, 2, 3, 4]:
    a2.bar(0, m0[str(tier)] if str(tier) in m0 else m0[tier], bottom=bottom0, color=TIER_C[tier], width=.6)
    a2.bar(1, m1[str(tier)] if str(tier) in m1 else m1[tier], bottom=bottom1, color=TIER_C[tier], width=.6, label=f"Tier {tier}")
    v0 = m0.iloc[tier-1]; v1 = m1.iloc[tier-1]
    a2.text(0, bottom0 + v0/2, f"{v0:.0%}", ha="center", color="white", fontweight="bold")
    a2.text(1, bottom1 + v1/2, f"{v1:.0%}", ha="center", color="white", fontweight="bold")
    bottom0 += v0; bottom1 += v1
a2.set_xticks([0, 1], ["Jan 1–30", "Apr 1–30"]); a2.set_yticks([])
a2.set_title("Who the active players are\n(share of active player-days)", loc="left", fontweight="bold")
a2.legend(frameon=False, bbox_to_anchor=(1, 1), fontsize=9)
fig.tight_layout(); fig.savefig(FIG / "deck_arpdau.png", dpi=200); plt.close(fig)

# 2. Installs per week by tier (the campaign)
from duckdb import connect
con = connect(str(ROOT / "game.duckdb"), read_only=True)
inst = con.sql("""SELECT install_week wk, country_tier, count(*) n FROM player
                  WHERE install_date BETWEEN '2026-01-05' AND '2026-04-26' GROUP BY 1, 2 ORDER BY 1""").df()
pv = inst.pivot(index="wk", columns="country_tier", values="n")
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.stackplot(pv.index, *[pv[c] for c in pv.columns], colors=[TIER_C[c] for c in pv.columns], labels=[f"Tier {c}" for c in pv.columns])
ax.axvline(pd.Timestamp("2026-02-23"), color="k", ls=":"); ax.text(pd.Timestamp("2026-02-25"), 6000, "paid_video\nramp-up", fontsize=9)
ax.set_title("Weekly installs by country tier", loc="left", fontweight="bold"); ax.legend(frameon=False, loc="upper left", fontsize=9)
fig.tight_layout(); fig.savefig(FIG / "deck_installs.png", dpi=200); plt.close(fig)

# 3. Daily ad views vs DAU (anomaly)
ad = pd.read_csv(OUT / "1d2_daily_ads.csv", parse_dates=["dt"])
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.plot(ad.dt, ad.completed_views, color="#3f88c5", label="completed ad views")
ax.plot(ad.dt, ad.dau, color="#adb5bd", label="DAU")
ax.axvspan(pd.Timestamp("2026-03-05"), pd.Timestamp("2026-03-07"), color="#d1495b", alpha=.25)
ax.text(pd.Timestamp("2026-03-07"), ad.dau.max()*.9, "  Mar 5–6: no ad events\n  logged (DAU normal)", fontsize=9, color="#a8323e")
ax.set_title("Daily rewarded-ad views (after −8h clock fix)", loc="left", fontweight="bold"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(FIG / "deck_ads.png", dpi=200); plt.close(fig)

# 4. Retention heat table
r = pd.read_csv(OUT / "1b_retention.csv")
fig, ax = plt.subplots(figsize=(6.2, 5.2))
vals = r[["d1", "d7", "d14", "d30"]].values
ax.imshow(np.where(np.isnan(vals), np.nan, vals), cmap="Blues", vmin=0, vmax=.55, aspect="auto")
for i in range(vals.shape[0]):
    for j in range(4):
        ax.text(j, i, "—" if np.isnan(vals[i, j]) else f"{vals[i, j]:.0%}", ha="center", va="center", fontsize=8,
                color="white" if (not np.isnan(vals[i, j]) and vals[i, j] > .35) else "black")
ax.set_xticks(range(4), ["D1", "D7", "D14", "D30"])
ax.set_yticks(range(len(r)), [f"{w[:10]}  (n={n:,})" for w, n in zip(r.install_week, r.installs)], fontsize=8)
ax.set_title("Retention by install week\n'—' = not every player observable yet", fontsize=10)
fig.tight_layout(); fig.savefig(FIG / "deck_retention.png", dpi=200); plt.close(fig)
print("charts written to", FIG)
