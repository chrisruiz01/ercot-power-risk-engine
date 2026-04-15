import pandas as pd

# Load historical merged data
df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# Rebuild risk curve (same as before)
df["is_spike"] = df["price"] > 200
df["load_bin"] = pd.cut(df["ercot_load"], bins=30)

risk_curve = df.groupby("load_bin").agg(
    load_mid=("ercot_load", "mean"),
    spike_prob=("is_spike", "mean"),
    count=("price", "count")
).reset_index()

risk_curve = risk_curve[risk_curve["count"] > 50]

# ---- SCENARIO INPUT ----
# You can change this
scenario_load = 78000

# Find closest load bin
risk_curve["diff"] = (risk_curve["load_mid"] - scenario_load).abs()
row = risk_curve.sort_values("diff").iloc[0]

prob = row["spike_prob"]

# Decision logic
def decision(prob):
    if prob >= 0.17:
        return "HEDGE"
    elif prob >= 0.10:
        return "WATCH / PARTIAL HEDGE"
    else:
        return "NO HEDGE"
        
print("Scenario Load:", scenario_load)
print("Estimated Spike Probability:", round(prob, 3))
print("Decision:", decision(prob))