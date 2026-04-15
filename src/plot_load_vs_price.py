import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

print("Rows:", len(df))
print("Date range:", df["timestamp"].min(), "to", df["timestamp"].max())

plt.figure(figsize=(10, 6))
plt.scatter(df["ercot_load"], df["price"], s=8, alpha=0.35)
plt.xlabel("ERCOT Load")
plt.ylabel("HB_HOUSTON Price")
plt.title("ERCOT Load vs HB_HOUSTON Price")
plt.tight_layout()
plt.show()