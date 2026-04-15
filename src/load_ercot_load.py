from pathlib import Path
import pandas as pd

data_path = Path("data/raw")

all_dfs = []

for file in sorted(data_path.glob("Native_Load_*.xlsx")):
    print(f"Processing {file.name}")
        
    xls = pd.ExcelFile(file)
    sheet = xls.sheet_names[0]  # take the first sheet

    df = pd.read_excel(file, sheet_name=sheet, usecols=["Hour Ending", "ERCOT"])    
    
    df["source_file"] = file.name
    all_dfs.append(df)

load_df = pd.concat(all_dfs, ignore_index=True)

# Convert timestamp
# Split the Hour Ending text into date part and hour part
load_df["hour_ending_text"] = load_df["Hour Ending"].astype(str)

load_df["date_part"] = load_df["hour_ending_text"].str.split().str[0]
load_df["time_part"] = load_df["hour_ending_text"].str.split().str[1]

# Parse the date part
load_df["date_part"] = pd.to_datetime(load_df["date_part"], format="%m/%d/%Y")

# Extract hour number from HH:MM
load_df["hour_num"] = load_df["time_part"].str.split(":").str[0].astype(int)

# ERCOT hour ending:
# 01:00 means the hour ending at 1 AM
# 24:00 means midnight at the NEXT day
load_df["timestamp"] = load_df["date_part"] + pd.to_timedelta(load_df["hour_num"], unit="h")

# Clean up
load_df = load_df.rename(columns={"ERCOT": "ercot_load"})

# Keep clean columns
load_df = load_df[["timestamp", "ercot_load", "source_file"]].sort_values("timestamp")

# Save
output_path = Path("data/processed/ercot_load.csv")
load_df.to_csv(output_path, index=False)

print(f"Saved to {output_path}")
print(load_df.head())
print(load_df.tail())