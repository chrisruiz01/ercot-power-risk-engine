import pandas as pd

df = pd.read_csv("data/processed/price_load_merged.csv", parse_dates=["timestamp"])

# Define thresholds based on your observation
def classify_regime(load):
    if load < 65000:
        return "normal"
    elif load < 75000:
        return "tight"
    else:
        return "stress"

df["regime"] = df["ercot_load"].apply(classify_regime)

# Define decision logic
def hedge_decision(regime):
    if regime == "stress":
        return "HEDGE"
    elif regime == "tight":
        return "WATCH / PARTIAL HEDGE"
    else:
        return "NO HEDGE"

df["decision"] = df["regime"].apply(hedge_decision)

# Check distribution
print(df["regime"].value_counts())
print("\nDecisions:")
print(df["decision"].value_counts())

# Show examples
print("\nSample decisions:")
print(df[["timestamp", "ercot_load", "price", "regime", "decision"]].tail(20))