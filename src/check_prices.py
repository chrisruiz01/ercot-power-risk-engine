import pandas as pd

prices = pd.read_csv("data/processed/hb_houston_prices.csv", parse_dates=["timestamp"])

print("Rows:", len(prices))
print("\nColumns:")
print(prices.columns.tolist())

print("\nDate range:")
print(prices["timestamp"].min())
print(prices["timestamp"].max())

print("\nNulls:")
print(prices.isna().sum())

print("\nDuplicate timestamps:")
print(prices["timestamp"].duplicated().sum())

print("\nTop 10 prices:")
print(prices.nlargest(10, "price")[["timestamp", "price"]])

print("\nBottom 10 prices:")
print(prices.nsmallest(10, "price")[["timestamp", "price"]])