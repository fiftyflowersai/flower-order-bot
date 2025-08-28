import pandas as pd
import json

# Load your exported file
df = pd.read_excel("data/exported_themes.xlsx")

# Get the theme column
theme_col = "Metafield: custom.product_theme [list.single_line_text_field]"

print("=== THEME ANALYSIS SUMMARY ===\n")

# Total products
total_products = len(df)
print(f"📊 Total products in export: {total_products:,}")

# Products with vs without themes
products_with_themes = df[theme_col].notna().sum()
products_without_themes = total_products - products_with_themes

print(f"✅ Products WITH themes: {products_with_themes:,} ({products_with_themes/total_products*100:.1f}%)")
print(f"❌ Products WITHOUT themes: {products_without_themes:,} ({products_without_themes/total_products*100:.1f}%)")

# Extract all unique themes
all_themes = set()
theme_data = df[theme_col].dropna()

for theme_list_str in theme_data:
    try:
        # Parse the JSON-like string to get individual themes
        theme_list = json.loads(theme_list_str)
        all_themes.update(theme_list)
    except (json.JSONDecodeError, TypeError):
        # Skip any problematic entries
        continue

print(f"\n🎨 All unique themes found: {len(all_themes)} total")
print("Themes:", sorted(list(all_themes)))

# Sample products with themes (first 10)
print(f"\n📋 Sample products with themes (showing first 10):")
print("-" * 60)

sample_products = df[df[theme_col].notna()][['ID', 'Title', theme_col]].head(10)

for idx, row in sample_products.iterrows():
    product_id = row['ID']
    title = row['Title']
    themes_raw = row[theme_col]
    
    try:
        themes = json.loads(themes_raw)
        themes_str = ", ".join(themes)
    except (json.JSONDecodeError, TypeError):
        themes_str = str(themes_raw)
    
    print(f"ID: {product_id}")
    print(f"Title: {title}")
    print(f"Themes: {themes_str}")
    print("-" * 40)

# Most common themes
print(f"\n📈 Most common themes:")
theme_counts = {}
for theme_list_str in theme_data:
    try:
        theme_list = json.loads(theme_list_str)
        for theme in theme_list:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
    except (json.JSONDecodeError, TypeError):
        continue

# Sort by count and show top 10
top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]
for theme, count in top_themes:
    percentage = (count / products_with_themes) * 100
    print(f"  {theme}: {count} products ({percentage:.1f}%)")

print(f"\n✨ Analysis complete!")