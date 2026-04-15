import pandas as pd
from sklearn.linear_model import LinearRegression

df = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])

# Add month number
df["month"] = df["DATE"].dt.month

# Features and target
X = df[["TMAX", "month"]]
y = df["daily_peak_load"]

model = LinearRegression()
model.fit(X, y)

print("Intercept:", model.intercept_)
print("Coefficients:")
for name, coef in zip(X.columns, model.coef_):
    print(f"  {name}: {coef}")

# Test a few scenarios
test = pd.DataFrame({
    "TMAX": [80, 90, 95, 100],
    "month": [7, 7, 7, 7]
})

test["predicted_load"] = model.predict(test)

print("\nTest predictions (July):")
print(test)