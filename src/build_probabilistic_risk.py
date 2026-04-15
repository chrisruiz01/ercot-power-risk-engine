import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# Define what a "bad outcome" is
SPIKE_THRESHOLD = 200  # you can adjust later

df["is_spike"] = df["price"] > SPIKE_THRESHOLD

# Bin load
df["load_bin"] = pd.cut(df["ercot_load"], bins=30)

# Compute spike probability per bin
risk_curve = df.groupby("load_bin").agg(
    load_mid=("ercot_load", "mean"),
    spike_prob=("is_spike", "mean"),
    avg_price=("price", "mean"),
    count=("price", "count")
).reset_index()

# Drop low-sample bins (important)
risk_curve = risk_curve[risk_curve["count"] > 50]

print(risk_curve.tail(10))

def risk_based_decision(prob):
    if prob > 0.20:
        return "HEDGE"
    elif prob > 0.05:
        return "WATCH / PARTIAL HEDGE"
    else:
        return "NO HEDGE"

risk_curve["decision"] = risk_curve["spike_prob"].apply(risk_based_decision)

print("\nDecision table:")
print(risk_curve[["load_mid", "spike_prob", "decision"]].tail(10))