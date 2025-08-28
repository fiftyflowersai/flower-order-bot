import pandas as pd
import json

# Load your exported file
df = pd.read_excel("data/exported_themes.xlsx")

# Get the theme column
theme_col = "Metafield: custom.product_theme [list.single_line_text_field]"

print("=== THEME ANALYSIS SUMMARY ===\n")

# Total products
total_products = len(df)
print(f"Total products in export: {total_products:,}")

# Products with vs without themes
products_with_themes = df[theme_col].notna().sum()
products_without_themes = total_products - products_with_themes

print(f"Products WITH themes: {products_with_themes:,} ({products_with_themes/total_products*100:.1f}%)")
print(f"Products WITHOUT themes: {products_without_themes:,} ({products_without_themes/total_products*100:.1f}%)")

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

print(f"\nAll unique themes found: {len(all_themes)} total")
print("Themes:", sorted(list(all_themes)))

# Sample products with themes (first 10)
print(f"\nSample products with themes (showing first 10):")
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
print(f"\nMost common themes:")
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

print(f"\nAnalysis complete!")

# Cross-reference with other catalog
print(f"\n" + "="*60)
print("CROSS-REFERENCE WITH OTHER CATALOG")
print("="*60)

try:
    # Load the other catalog
    other_catalog = pd.read_excel("data/BloombrainCatalogwithprices.xlsx")
    print(f"Loaded other catalog: {len(other_catalog):,} products")
    
    # Get product names from themed products in current catalog
    themed_products = df[df[theme_col].notna()]
    current_themed_names = set(themed_products['Title'].dropna().str.strip().str.lower())
    
    # Get product names from other catalog
    other_product_names = set(other_catalog['Product name'].dropna().str.strip().str.lower())
    
    print(f"Products with themes in current catalog: {len(current_themed_names):,}")
    print(f"Products in other catalog: {len(other_product_names):,}")
    
    # Find matches (case-insensitive)
    matches = current_themed_names.intersection(other_product_names)
    
    print(f"\nMATCHES FOUND: {len(matches)} products")
    print(f"   That's {len(matches)/len(current_themed_names)*100:.1f}% of your themed products")
    
    if matches:
        print(f"\nSample matches (first 10):")
        sample_matches = list(matches)[:10]
        for i, match in enumerate(sample_matches, 1):
            # Find the original case version from current catalog
            original_themed = themed_products[themed_products['Title'].str.strip().str.lower() == match]['Title'].iloc[0]
            original_other = other_catalog[other_catalog['Product name'].str.strip().str.lower() == match]['Product name'].iloc[0]
            
            print(f"{i:2d}. Current: '{original_themed}'")
            print(f"     Other:   '{original_other}'")
            print()
    
    # Show non-matches for context
    non_matches = current_themed_names - other_product_names
    print(f"Themed products NOT in other catalog: {len(non_matches)}")
    
    if len(non_matches) > 0 and len(non_matches) <= 10:
        print(f"\n🔍 Products with themes that are unique to current catalog:")
        for name in list(non_matches):
            # Find original case
            original = themed_products[themed_products['Title'].str.strip().str.lower() == name]['Title'].iloc[0]
            print(f"   - '{original}'")
    elif len(non_matches) > 10:
        print(f"\nFirst 10 themed products unique to current catalog:")
        for name in list(non_matches)[:10]:
            # Find original case
            original = themed_products[themed_products['Title'].str.strip().str.lower() == name]['Title'].iloc[0]
            print(f"   - '{original}'")

except FileNotFoundError:
    print("Could not find 'data/BloombrainCatalogwithprices.xlsx'")
    print("   Make sure the file is in the data directory")
except KeyError as e:
    print(f"Column not found in other catalog: {e}")
    print("   Available columns:", other_catalog.columns.tolist())
except Exception as e:
    print(f"Error loading other catalog: {e}")

print(f"\nCross-reference analysis complete!")

# Check product type for themed products
print(f"\n" + "="*60)
print("PRODUCT TYPE ANALYSIS FOR THEMED PRODUCTS")
print("="*60)

# Get the product type column
product_type_col = "Metafield: custom.product_type_all_flowers [list.single_line_text_field]"

if product_type_col in df.columns:
    themed_products = df[df[theme_col].notna()]
    
    print(f"Analyzing product types for {len(themed_products)} themed products...")
    
    # Check product types
    product_types = themed_products[product_type_col].dropna()
    
    print(f"Themed products with product type data: {len(product_types)} out of {len(themed_products)}")
    
    # Count "Make This Look" products
    make_this_look_count = 0
    all_product_types = []
    
    for product_type_str in product_types:
        try:
            # Parse the JSON-like string to get individual product types
            product_type_list = json.loads(product_type_str)
            all_product_types.extend(product_type_list)
            
            # Check if "Make This Look" is in this product's types
            for ptype in product_type_list:
                if "make this look" in ptype.lower():
                    make_this_look_count += 1
                    break  # Count each product only once
        except (json.JSONDecodeError, TypeError):
            # Handle non-JSON entries
            if product_type_str and "make this look" in str(product_type_str).lower():
                make_this_look_count += 1
    
    print(f"\nRESULTS:")
    print(f"   'Make This Look' themed products: {make_this_look_count}")
    print(f"   Percentage of themed products: {make_this_look_count/len(themed_products)*100:.1f}%")
    
    # Show all unique product types found in themed products
    unique_types = list(set(all_product_types))
    print(f"\nAll product types found in themed products ({len(unique_types)} unique):")
    for ptype in sorted(unique_types):
        type_count = all_product_types.count(ptype)
        percentage = (type_count / len(product_types)) * 100
        print(f"   {ptype}: {type_count} ({percentage:.1f}%)")
    
    # Sample of Make This Look themed products
    if make_this_look_count > 0:
        print(f"\nSample 'Make This Look' themed products:")
        sample_count = 0
        for idx, row in themed_products.iterrows():
            if sample_count >= 5:  # Show first 5
                break
                
            product_type_str = row[product_type_col]
            if pd.notna(product_type_str):
                try:
                    product_type_list = json.loads(product_type_str)
                    is_make_this_look = any("make this look" in ptype.lower() for ptype in product_type_list)
                except (json.JSONDecodeError, TypeError):
                    is_make_this_look = "make this look" in str(product_type_str).lower()
                
                if is_make_this_look:
                    themes_raw = row[theme_col]
                    try:
                        themes = json.loads(themes_raw)
                        themes_str = ", ".join(themes)
                    except (json.JSONDecodeError, TypeError):
                        themes_str = str(themes_raw)
                    
                    print(f"   - {row['Title']}")
                    print(f"     Themes: {themes_str}")
                    sample_count += 1

else:
    print(f"Could not find product type column: {product_type_col}")
    print("Available columns with 'product' or 'type':")
    relevant_cols = [col for col in df.columns if 'product' in col.lower() or 'type' in col.lower()]
    for col in relevant_cols:
        print(f"   - {col}")

print(f"\nProduct type analysis complete!")