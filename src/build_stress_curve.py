import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# Create load bins
df["load_bin"] = pd.cut(df["ercot_load"], bins=30)

# Aggregate statistics per bin
agg = df.groupby("load_bin").agg(
    load_mid=("ercot_load", "mean"),
    price_median=("price", "median"),
    price_p90=("price", lambda x: np.percentile(x, 90)),
    price_p99=("price", lambda x: np.percentile(x, 99)),
    count=("price", "count")
).reset_index()

# Plot
plt.figure(figsize=(10, 6))

plt.plot(agg["load_mid"], agg["price_median"], label="Median Price")
plt.plot(agg["load_mid"], agg["price_p90"], label="P90 Price")
plt.plot(agg["load_mid"], agg["price_p99"], label="P99 Price")

plt.xlabel("ERCOT Load")
plt.ylabel("Price")
plt.title("ERCOT Stress Curve (Load vs Price Distribution)")
plt.legend()
plt.tight_layout()
plt.show()

print(agg.tail(10))