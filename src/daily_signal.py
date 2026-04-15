import pandas as pd

# --- load historical merged data ---
df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# --- build risk curve (same as before) ---
df["is_spike"] = df["price"] > 200
df["load_bin"] = pd.cut(df["ercot_load"], bins=30)

risk_curve = df.groupby("load_bin").agg(
    load_mid=("ercot_load", "mean"),
    spike_prob=("is_spike", "mean"),
    count=("price", "count")
).reset_index()

risk_curve = risk_curve[risk_curve["count"] > 50].copy()

# decision policy
def decision(prob):
    if prob >= 0.17:
        return "HEDGE"
    elif prob >= 0.10:
        return "WATCH / PARTIAL HEDGE"
    else:
        return "NO HEDGE"

# helper: map load -> spike probability
def get_prob(load):
    risk_curve["diff"] = (risk_curve["load_mid"] - load).abs()
    row = risk_curve.sort_values("diff").iloc[0]
    return float(row["spike_prob"])

# --- simple daily load proxy: use daily MAX load ---
daily = (
    df.set_index("timestamp")
      .resample("D")["ercot_load"]
      .max()
      .reset_index()
      .rename(columns={"ercot_load": "daily_peak_load"})
)

# compute risk + decision per day
daily["spike_prob"] = daily["daily_peak_load"].apply(get_prob)
daily["decision"] = daily["spike_prob"].apply(decision)

# show last 10 days
print(daily.tail(10))

# save
daily.to_csv("data/processed/daily_signal.csv", index=False)
print("\nSaved: data/processed/daily_signal.csv")