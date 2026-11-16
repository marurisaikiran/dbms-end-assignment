"""Run load + cleaning + Part 1 SQL; write each result to out/*.csv and print summaries.
Usage:  .venv/bin/python run_part1.py
"""
import pathlib, duckdb

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
con = duckdb.connect(str(ROOT / "game.duckdb"))


def query_file(name):
    """Return list of DataFrames, one per SELECT statement in the file.
    Comments are stripped before splitting on ';'."""
    sql = (ROOT / "sql" / name).read_text()
    sql = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
    out = []
    for s in sql.split(";"):
        body = s.strip()
        if body:
            out.append(con.sql(body).df())
    return out


if __name__ == "__main__":
    con.execute((ROOT / "sql" / "00_load.sql").read_text())
    con.execute((ROOT / "sql" / "01_clean.sql").read_text())

    (a,) = query_file("1a_daily_health.sql"); a.to_csv(OUT / "1a_daily_health.csv", index=False)
    (b,) = query_file("1b_retention.sql"); b.to_csv(OUT / "1b_retention.csv", index=False)
    c1, c2, c3 = query_file("1c_spenders.sql")
    c1.to_csv(OUT / "1c1_concentration.csv", index=False)
    c2.to_csv(OUT / "1c2_time_to_first_purchase.csv", index=False)
    c3.to_csv(OUT / "1c3_repeat_gap.csv", index=False)
    d1, d2 = query_file("1d_ads.sql")
    d1.to_csv(OUT / "1d1_cap_hits.csv", index=False)
    d2.to_csv(OUT / "1d2_daily_ads.csv", index=False)

    print("1a sample:\n", a.head(6).to_string(index=False))
    tot = a.groupby("platform")[["dau", "gross_revenue"]].sum(); print(tot)
    print("1b:\n", b.to_string(index=False))
    for df in (c1, c2, c3, d1):
        print(df.to_string(index=False), "\n")
