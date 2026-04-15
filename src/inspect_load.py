from pathlib import Path
import pandas as pd

data_path = Path("data/raw")

# change this if needed once you see the exact filename
files = list(data_path.glob("*load*.xlsx")) + list(data_path.glob("*Load*.xlsx")) + list(data_path.glob("*load*.csv")) + list(data_path.glob("*Load*.csv"))

print("Matched files:")
for f in files:
    print("-", f.name)

if not files:
    print("No load file matched. Put the file in data/raw and tell me the filename.")
else:
    file = files[0]
    print(f"\nInspecting: {file.name}")

    if file.suffix.lower() == ".csv":
        df = pd.read_csv(file, nrows=5)
    else:
        xls = pd.ExcelFile(file)
        print("\nSheets:")
        print(xls.sheet_names)
        df = pd.read_excel(file, sheet_name=xls.sheet_names[0], nrows=5)

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nSample:")
    print(df.head())