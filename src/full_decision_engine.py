import pandas as pd
import numpy as np

# load data
df = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])
merged = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# --- build temp → load model (quadratic + month) ---
df_temp = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])
df_temp["month"] = df_temp["DATE"].dt.month
df_temp["TMAX_sq"] = df_temp["TMAX"] ** 2

X = df_temp[["TMAX", "TMAX_sq", "month"]]
y = df_temp["daily_peak_load"]

from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X, y)

def predict_load(temp, month):
    input_df = pd.DataFrame({
        "TMAX": [temp],
        "TMAX_sq": [temp**2],
        "month": [month]
    })
    return model.predict(input_df)[0]

# --- build risk curve ---
merged["is_spike"] = merged["price"] > 200
merged["load_bin"] = pd.cut(merged["ercot_load"], bins=30)

risk_curve = merged.groupby("load_bin").agg(
    load_mid=("ercot_load", "mean"),
    spike_prob=("is_spike", "mean"),
    count=("price", "count")
).reset_index()

risk_curve = risk_curve[risk_curve["count"] > 50].copy()

# ensure sorted by load
risk_curve = risk_curve.sort_values("load_mid")

load_levels = risk_curve["load_mid"].values
spike_probs = risk_curve["spike_prob"].values

def get_prob(load):
    return float(np.interp(load, load_levels, spike_probs))
    
# --- decision policy ---
def decision(prob):
    if prob >= 0.17:
        return "HEDGE"
    elif prob >= 0.10:
        return "WATCH / PARTIAL HEDGE"
    else:
        return "NO HEDGE"

# --- SCENARIO ---
# scenario_temp = 97
# scenario_month = 7

# predicted_load = predict_load(scenario_temp, scenario_month)
# prob = get_prob(predicted_load)

# print("Scenario Temp:", scenario_temp)
# print("Scenario Month:", scenario_month)
# print("Predicted Load:", int(predicted_load))
# print("Spike Probability:", round(prob, 3))
# print("Decision:", decision(prob))

# --- TEMP SWEEP TEST ---
for temp in range(80, 106):
    predicted_load = predict_load(temp, 7)
    prob = get_prob(predicted_load)

    print(
        f"Temp: {temp}, "
        f"Load: {int(predicted_load)}, "
        f"Prob: {prob:.3f}, "
        f"Decision: {decision(prob)}"
    )

import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.plot(load_levels, spike_probs, marker="o")
plt.xlabel("ERCOT Load")
plt.ylabel("Spike Probability")
plt.title("Spike Probability vs ERCOT Load")
plt.grid(True)
plt.show()