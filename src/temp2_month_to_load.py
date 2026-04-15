import pandas as pd
from sklearn.linear_model import LinearRegression

df = pd.read_csv("data/processed/weather_load_merged.csv", parse_dates=["DATE"])

df["month"] = df["DATE"].dt.month
df["TMAX_sq"] = df["TMAX"] ** 2

X = df[["TMAX", "TMAX_sq", "month"]]
y = df["daily_peak_load"]

model = LinearRegression()
model.fit(X, y)

print("Intercept:", model.intercept_)
print("Coefficients:")
for name, coef in zip(X.columns, model.coef_):
    print(f"  {name}: {coef}")

test = pd.DataFrame({
    "TMAX": [80, 90, 95, 100],
    "month": [7, 7, 7, 7]
})
test["TMAX_sq"] = test["TMAX"] ** 2
test["predicted_load"] = model.predict(test[["TMAX", "TMAX_sq", "month"]])

print("\nTest predictions (July):")
print(test[["TMAX", "month", "predicted_load"]])