import pandas as pd
xl = pd.ExcelFile('aidsvu_combined_2014_2023_FULL.xlsx')
for sheet in ['MSA_Panel', 'State_Panel', 'Stratum_Aggregates']:
    df = pd.read_excel(xl, sheet_name=sheet)
    print(f"\n=== {sheet} (shape {df.shape}) ===")
    print("Columns:", df.columns.tolist())
    print(df.head(3).to_string())