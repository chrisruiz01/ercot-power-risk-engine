from pathlib import Path
import pandas as pd

# Path to raw data
data_path = Path("data/raw")

# Columns we care about
usecols = [
    "Delivery Date",
    "Hour Ending",
    "Repeated Hour Flag",
    "Settlement Point",
    "Settlement Point Price"
]

all_dfs = []

for file in data_path.glob("*.xlsx"):
    print(f"Processing {file.name}")
    
    xls = pd.ExcelFile(file)
    
    for sheet in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet, usecols=usecols)
        
        # Filter for HB_HOUSTON
        df = df[df["Settlement Point"] == "HB_HOUSTON"].copy()
        
        df["source_file"] = file.name
        df["source_sheet"] = sheet
        
        all_dfs.append(df)

# Combine everything
prices = pd.concat(all_dfs, ignore_index=True)

# Convert date
prices["Delivery Date"] = pd.to_datetime(prices["Delivery Date"])

# Convert Hour Ending → numeric hour
prices["hour"] = prices["Hour Ending"].str.split(":").str[0].astype(int)

# Create timestamp (hour beginning)
prices["timestamp"] = (
    prices["Delivery Date"] + pd.to_timedelta(prices["hour"] - 1, unit="h")
)

# Rename price column
prices = prices.rename(columns={
    "Settlement Point Price": "price"
})

# Keep only key columns
prices = prices[[
    "timestamp",
    "price",
    "Repeated Hour Flag",
    "source_file",
    "source_sheet"
]].sort_values("timestamp")

# Save cleaned output
output_path = Path("data/processed/hb_houston_prices.csv")
prices.to_csv(output_path, index=False)

print(f"Saved to {output_path}")
print(prices.head())