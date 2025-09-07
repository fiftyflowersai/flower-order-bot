import pandas as pd
import numpy as np
import json
import re
from collections import Counter

# File path
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"

def load_data():
    """Load the Excel data"""
    try:
        df = pd.read_excel(FILE_PATH)
        print(f"Data loaded successfully: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def parse_month_day(date_str):
    """Convert 'May 28' to (5, 28)"""
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    try:
        parts = date_str.strip().lower().split()
        month_name = parts[0][:3]  # First 3 letters
        day = int(parts[1])
        return month_map[month_name], day
    except:
        return None, None

def validate_required_columns(df):
    """Check if all required columns exist"""
    print("=" * 60)
    print("1. REQUIRED COLUMNS VALIDATION")
    print("=" * 60)
    
    required_columns = [
        # Core identification
        'Product ID',
        'Variant ID',
        'Product name',
        'Variant price',
        
        # Chatbot variables
        'Seasonality (by semicolon)',
        'Colors (by semicolon)', 
        'attributes.Holiday Occasion',
        'attributes.DIY Level',
        
        # Product type columns
        'Group',
        'Subgroup',
        'Variant name',
        'attributes.Product Type - All Flowers',
        'attributes.Recipe metafield',
        'attributes.Description'
    ]
    
    missing_columns = []
    existing_columns = []
    
    for col in required_columns:
        if col in df.columns:
            existing_columns.append(col)
        else:
            missing_columns.append(col)
    
    print(f"Required columns found: {len(existing_columns)}/{len(required_columns)}")
    
    if missing_columns:
        print(f"\nMISSING COLUMNS ({len(missing_columns)}):")
        for col in missing_columns:
            print(f"  ❌ {col}")
        print("\n⚠️  WARNING: Missing columns will need to be handled in cleaning script")
    else:
        print("✅ All required columns found!")
    
    return existing_columns, missing_columns

def validate_unique_identifiers(df):
    """Validate Product ID + Variant ID creates unique identifiers"""
    print("\n" + "=" * 60)
    print("2. UNIQUE IDENTIFIER VALIDATION")
    print("=" * 60)
    
    if 'Product ID' not in df.columns or 'Variant ID' not in df.columns:
        print("❌ Cannot validate - missing Product ID or Variant ID columns")
        return False
    
    # Check for nulls in ID columns
    product_id_nulls = df['Product ID'].isnull().sum()
    variant_id_nulls = df['Variant ID'].isnull().sum()
    
    print(f"Product ID nulls: {product_id_nulls}")
    print(f"Variant ID nulls: {variant_id_nulls}")
    
    # Create composite unique ID
    df_temp = df.copy()
    df_temp['composite_id'] = df_temp['Product ID'].astype(str) + '_' + df_temp['Variant ID'].astype(str)
    
    total_rows = len(df_temp)
    unique_composite_ids = df_temp['composite_id'].nunique()
    duplicates = total_rows - unique_composite_ids
    
    print(f"Total rows: {total_rows}")
    print(f"Unique composite IDs: {unique_composite_ids}")
    print(f"Duplicate composite IDs: {duplicates}")
    
    if duplicates == 0:
        print("✅ Product ID + Variant ID creates unique identifiers!")
        return True
    else:
        print("❌ Duplicate composite IDs found - this will cause issues")
        
        # Show sample duplicates
        duplicate_ids = df_temp[df_temp['composite_id'].duplicated()]['composite_id'].head()
        print("\nSample duplicate IDs:")
        for dup_id in duplicate_ids:
            print(f"  {dup_id}")
        return False

def validate_missing_data(df):
    """Check missing data percentages for our target columns"""
    print("\n" + "=" * 60)
    print("3. MISSING DATA ANALYSIS")
    print("=" * 60)
    
    target_columns = [
        'Variant price',
        'Seasonality (by semicolon)',
        'Colors (by semicolon)',
        'attributes.Holiday Occasion', 
        'attributes.DIY Level',
        'Group',
        'Product name',
        'attributes.Description'
    ]
    
    available_columns = [col for col in target_columns if col in df.columns]
    
    print("Missing data percentages:")
    print("-" * 40)
    
    critical_missing = []
    
    for col in available_columns:
        missing_count = df[col].isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        
        status = "❌" if missing_pct > 50 else "⚠️" if missing_pct > 10 else "✅"
        print(f"{status} {col}: {missing_count:,} ({missing_pct:.1f}%)")
        
        if missing_pct > 50:
            critical_missing.append(col)
    
    if critical_missing:
        print(f"\n⚠️  HIGH MISSING DATA in: {', '.join(critical_missing)}")
        print("These columns may not be effective for filtering")
    else:
        print("\n✅ Missing data levels are acceptable")

def validate_seasonality_structure(df):
    """Validate seasonality date range patterns"""
    print("\n" + "=" * 60)
    print("4. SEASONALITY DATA STRUCTURE VALIDATION")
    print("=" * 60)
    
    if 'Seasonality (by semicolon)' not in df.columns:
        print("❌ Seasonality column not found")
        return False
    
    seasonality_col = df['Seasonality (by semicolon)'].dropna()
    unique_patterns = seasonality_col.unique()
    
    print(f"Total unique seasonality patterns: {len(unique_patterns)}")
    
    # Categorize patterns
    year_round = []
    simple_patterns = []
    multi_range_patterns = []
    year_boundary_single = []
    unparseable = []
    
    for pattern in unique_patterns:
        if pattern == 'YR':
            year_round.append(pattern)
        elif ';' in pattern:
            multi_range_patterns.append(pattern)
        elif ' - ' in pattern:
            # Single range - check if it crosses year boundary
            try:
                start_str, end_str = pattern.split(' - ')
                start_month, _ = parse_month_day(start_str)
                end_month, _ = parse_month_day(end_str)
                
                if start_month and end_month:
                    if start_month > end_month:  # Dec to Jan in single range
                        year_boundary_single.append(pattern)
                    else:
                        simple_patterns.append(pattern)
                else:
                    unparseable.append(pattern)
            except:
                unparseable.append(pattern)
        else:
            unparseable.append(pattern)
    
    print(f"\nPattern breakdown:")
    print(f"  Year-round (YR): {len(year_round)}")
    print(f"  Simple same-year ranges: {len(simple_patterns)}")
    print(f"  Multi-range patterns: {len(multi_range_patterns)}")
    print(f"  Year-boundary SINGLE ranges: {len(year_boundary_single)}")
    print(f"  Unparseable patterns: {len(unparseable)}")
    
    # Critical test: Are there year-boundary single ranges?
    if year_boundary_single:
        print(f"\n❌ CRITICAL ISSUE: Found {len(year_boundary_single)} year-boundary single ranges:")
        for pattern in year_boundary_single[:5]:
            print(f"     {pattern}")
        print("\n⚠️  Your date logic will need modification to handle these cases")
        return False
    else:
        print("\n✅ No year-boundary single ranges found!")
        print("✅ Your date range logic should work correctly")
    
    # Show samples
    print(f"\nSample patterns:")
    if simple_patterns:
        print(f"  Simple: {simple_patterns[0]}")
    if multi_range_patterns:
        print(f"  Multi-range: {multi_range_patterns[0]}")
    if unparseable:
        print(f"  Unparseable: {unparseable[0]}")
    
    return True

def validate_color_data(df):
    """Validate color data and categorization coverage"""
    print("\n" + "=" * 60)
    print("5. COLOR DATA VALIDATION")
    print("=" * 60)
    
    if 'Colors (by semicolon)' not in df.columns:
        print("❌ Colors column not found")
        return False
    
    # Extract all unique colors
    all_colors = []
    colors_series = df['Colors (by semicolon)'].dropna()
    
    for color_entry in colors_series:
        if ';' in str(color_entry):
            colors = [c.strip().lower() for c in str(color_entry).split(';') if c.strip()]
            all_colors.extend(colors)
        else:
            all_colors.append(str(color_entry).strip().lower())
    
    unique_colors = sorted(list(set(all_colors)))
    print(f"Found {len(unique_colors)} unique colors")
    
    # Load manual color mapping
    manual_color_categories = {
        "red": ["red", "true red", "burgundy", "cranberry", "wine red", "rust"],
        "pink": ["pink", "light pink", "hot pink", "true pink", "blush", "blush pink", 
                "fuchsia", "magenta", "coral", "dusty pink", "dusty rose", "mauve"],
        "white": ["white", "ivory", "clear", "natural", "champagne"],
        "yellow": ["yellow", "amber", "chartreuse", "gold", "pale yellow", "mustard yellow", "dark yellow"],
        "orange": ["orange", "peach", "sunset", "terracotta", "copper", "dark orange", "true orange"],
        "purple": ["purple", "lavender", "pinky lavender", "true purple", "dark purple"],
        "blue": ["blue", "soft blue", "light blue", "teal"],
        "green": ["green", "sage green", "emerald green", "forest green", "lime green", 
                 "light green updated", "true green"],
        "neutral": ["black", "gray", "silver", "brown", "bronze"],
        "mixed": ["farm mixes", "rainbow", "multicolor", "choose your colors"]
    }
    
    # Check coverage
    categorized_colors = []
    for category_colors in manual_color_categories.values():
        categorized_colors.extend(category_colors)
    
    uncategorized_colors = [c for c in unique_colors if c not in categorized_colors]
    
    print(f"Colors in manual mapping: {len(categorized_colors)}")
    print(f"Colors found in data: {len(unique_colors)}")
    print(f"Uncategorized colors: {len(uncategorized_colors)}")
    
    if uncategorized_colors:
        print(f"\n⚠️  UNCATEGORIZED COLORS ({len(uncategorized_colors)}):")
        for color in uncategorized_colors:
            print(f"     {color}")
        print("\n⚠️  These colors will not be assigned to boolean categories")
    else:
        print("\n✅ All colors are categorized!")
    
    # Show category distribution
    print(f"\nColor category sizes:")
    for category, colors in manual_color_categories.items():
        print(f"  {category}: {len(colors)} colors")
    
    return len(uncategorized_colors) == 0

def validate_data_types(df):
    """Validate data types for key columns"""
    print("\n" + "=" * 60)
    print("6. DATA TYPE VALIDATION")
    print("=" * 60)
    
    validations = []
    
    # Variant price should be numeric
    if 'Variant price' in df.columns:
        price_col = df['Variant price']
        numeric_count = pd.to_numeric(price_col, errors='coerce').notna().sum()
        total_non_null = price_col.notna().sum()
        
        if total_non_null > 0:
            numeric_pct = (numeric_count / total_non_null) * 100
            status = "✅" if numeric_pct > 95 else "⚠️"
            print(f"{status} Variant price: {numeric_pct:.1f}% numeric values")
            validations.append(numeric_pct > 95)
        else:
            print("❌ Variant price: All values are null")
            validations.append(False)
    
    # Check for encoding issues in text fields
    text_fields = ['Product name', 'attributes.Description', 'Group']
    available_text_fields = [col for col in text_fields if col in df.columns]
    
    encoding_issues = 0
    for col in available_text_fields:
        sample_values = df[col].dropna().head(100)
        for val in sample_values:
            if isinstance(val, str) and ('�' in val or len(val.encode('utf-8', errors='ignore')) != len(val.encode('utf-8'))):
                encoding_issues += 1
                break
    
    if encoding_issues == 0:
        print("✅ No encoding issues detected in text fields")
        validations.append(True)
    else:
        print(f"⚠️  Encoding issues detected in {encoding_issues} text fields")
        validations.append(False)
    
    return all(validations)

def generate_validation_summary():
    """Generate final validation summary"""
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    df = load_data()
    if df is None:
        print("❌ Cannot proceed - data loading failed")
        return False
    
    results = []
    
    try:
        existing_cols, missing_cols = validate_required_columns(df)
        results.append(len(missing_cols) == 0)
        
        unique_id_ok = validate_unique_identifiers(df)
        results.append(unique_id_ok)
        
        validate_missing_data(df)  # Informational only
        results.append(True)
        
        seasonality_ok = validate_seasonality_structure(df)
        results.append(seasonality_ok)
        
        color_ok = validate_color_data(df)
        results.append(color_ok)
        
        data_types_ok = validate_data_types(df)
        results.append(data_types_ok)
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False
    
    passed_tests = sum(results)
    total_tests = len(results)
    
    print(f"\nTEST RESULTS: {passed_tests}/{total_tests} passed")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("✅ Data is ready for cleaning!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} validations failed")
        print("❌ Address issues before proceeding to data cleaning")
        return False

def main():
    """Main validation execution"""
    print("PRE-CLEANING DATA VALIDATION")
    print("=" * 60)
    print("Validating data structure before cleaning process...")
    
    success = generate_validation_summary()
    
    print("\n" + "=" * 60)
    if success:
        print("NEXT STEP: Run the data cleaning script")
    else:
        print("NEXT STEP: Fix validation issues before cleaning")
    print("=" * 60)

if __name__ == "__main__":
    main()