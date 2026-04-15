from pathlib import Path
import pandas as pd

# find the NOAA file
files = list(Path("data/raw").glob("*.csv"))

print("CSV files found:")
for f in files:
    print("-", f.name)

# pick the weather file manually by name if needed
weather_file = None
for f in files:
    if "daily" in f.name.lower() or "noaa" in f.name.lower() or "climate" in f.name.lower():
        weather_file = f
        break

if weather_file is None:
    raise FileNotFoundError("Could not identify the NOAA weather CSV in data/raw")

print(f"\nUsing weather file: {weather_file.name}")

df = pd.read_csv(weather_file)

print("\nOriginal columns:")
print(df.columns.tolist())

# keep only what we need
keep_cols = ["STATION", "NAME", "DATE", "TMAX", "TMIN"]
df = df[keep_cols].copy()

# filter for IAH station / Houston Intercontinental
df = df[
    (df["NAME"].str.contains("HOUSTON INTERCONTINENTAL", case=False, na=False))
].copy()

# convert types
df["DATE"] = pd.to_datetime(df["DATE"])
df["TMAX"] = pd.to_numeric(df["TMAX"], errors="coerce")
df["TMIN"] = pd.to_numeric(df["TMIN"], errors="coerce")

# sort
df = df.sort_values("DATE")

print("\nRows after filter:", len(df))
print("\nDate range:")
print(df["DATE"].min())
print(df["DATE"].max())

print("\nNulls:")
print(df[["DATE", "TMAX", "TMIN"]].isna().sum())

print("\nDuplicate dates:")
print(df["DATE"].duplicated().sum())

print("\nSample:")
print(df.head())

# save cleaned weather
output_path = Path("data/processed/weather_daily_iah.csv")
df.to_csv(output_path, index=False)
print(f"\nSaved to {output_path}")