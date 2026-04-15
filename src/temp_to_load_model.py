import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])

# Fit simple polynomial (captures curve shape)
coeffs = np.polyfit(df["TMAX"], df["daily_peak_load"], deg=2)

print("Model coefficients:", coeffs)

def predict_load(temp):
    return coeffs[0]*temp**2 + coeffs[1]*temp + coeffs[2]

# Test a few temps
test_temps = [70, 80, 90, 100]

print("\nTest predictions:")
for t in test_temps:
    print(f"Temp {t} → Load {int(predict_load(t))}")