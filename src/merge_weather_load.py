import pandas as pd

# load weather
weather = pd.read_csv("data/processed/weather_daily_iah.csv", parse_dates=["DATE"])

# load daily peak load
load_df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

daily_load = (
    load_df.set_index("timestamp")
           .resample("D")["ercot_load"]
           .max()
           .reset_index()
           .rename(columns={"timestamp": "DATE", "ercot_load": "daily_peak_load"})
)

# merge
merged = weather.merge(daily_load, on="DATE", how="inner")

print("Rows:", len(merged))
print("\nDate range:")
print(merged["DATE"].min(), "to", merged["DATE"].max())

print("\nSample:")
print(merged.head())

merged.to_csv("data/processed/weather_load_merged.csv", index=False)
print("\nSaved: data/processed/weather_load_merged.csv")