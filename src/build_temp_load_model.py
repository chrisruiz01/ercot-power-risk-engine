import pandas as pd
import matplotlib.pyplot as plt

# For now we simulate temp column later — structure first

df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# Create proxy temperature feature using hour-of-day pattern (temporary)
# (we will replace with NOAA next step)
df["hour"] = df["timestamp"].dt.hour

# Daily peak load
daily = (
    df.set_index("timestamp")
      .resample("D")["ercot_load"]
      .max()
      .reset_index()
      .rename(columns={"ercot_load": "daily_peak_load"})
)

# Add month (seasonality proxy)
daily["month"] = daily["timestamp"].dt.month

print(daily.head())