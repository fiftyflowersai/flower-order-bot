import pandas as pd

# Load your exported file
df = pd.read_excel("data/exported_themes.xlsx")

# Look at the first few rows and all column names
print("Columns in file:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

# Check if there's any column containing 'theme'
theme_cols = [col for col in df.columns if "theme" in str(col).lower()]
print("\nPossible theme columns:")
print(theme_cols)

# Check unique values in the theme column (if found)
if theme_cols:
    print("\nUnique theme values:")
    print(df[theme_cols[0]].dropna().unique())
