import pandas as pd

prices = pd.read_csv("data/processed/hb_houston_prices.csv", parse_dates=["timestamp"])
load_df = pd.read_csv("data/processed/ercot_load.csv", parse_dates=["timestamp"])

# Keep only what we need
prices = prices[["timestamp", "price", "Repeated Hour Flag"]].copy()
load_df = load_df[["timestamp", "ercot_load"]].copy()

# First attempt: direct merge on timestamp
merged = prices.merge(load_df, on="timestamp", how="inner")

print("Direct merge rows:", len(merged))
print("Direct merge date range:")
print(merged["timestamp"].min())
print(merged["timestamp"].max())

print("\nNulls after direct merge:")
print(merged.isna().sum())

print("\nSample:")
print(merged.head())

merged.to_csv("data/processed/price_load_merged.csv", index=False)
print("\nSaved: data/processed/price_load_merged.csv")