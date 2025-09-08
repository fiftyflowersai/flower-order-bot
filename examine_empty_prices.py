import pandas as pd

# ---------------------------
# 1. Load the raw Excel file
# ---------------------------
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
df = pd.read_excel(FILE_PATH)

# ---------------------------
# 2. Filter for active products with active variants and variant_price = 0
# ---------------------------
filtered_df = df[
    (df['Variant price'] == 0) &
    (df['Product status'].str.lower() == 'active') &
    (df['Variant status'].str.lower() == 'active')
]

# ---------------------------
# 3. Select only Product ID and Variant ID
# ---------------------------
result_df = filtered_df[['Product ID', 'Variant ID']]

# ---------------------------
# 4. Display results
# ---------------------------
print("Active products with active variants and variant price = 0:")
print(result_df)

# ---------------------------
# 5. Optional: export to CSV
# ---------------------------
result_df.to_csv("zero_price_active_variants.csv", index=False)
print("Results exported to zero_price_active_variants.csv")
