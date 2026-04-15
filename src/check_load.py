import pandas as pd

load_df = pd.read_csv("data/processed/ercot_load.csv", parse_dates=["timestamp"])

print("Rows:", len(load_df))
print("\nDate range:")
print(load_df["timestamp"].min())
print(load_df["timestamp"].max())

print("\nNulls:")
print(load_df.isna().sum())

print("\nDuplicate timestamps:")
print(load_df["timestamp"].duplicated().sum())

print("\nTop 10 loads:")
print(load_df.nlargest(10, "ercot_load")[["timestamp", "ercot_load"]])