import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])

plt.figure(figsize=(10,6))
plt.scatter(df["TMAX"], df["daily_peak_load"], s=10, alpha=0.4)

plt.xlabel("Daily Max Temperature (TMAX)")
plt.ylabel("Daily Peak ERCOT Load")
plt.title("Temperature vs Peak Load")

plt.tight_layout()
plt.show()