import pandas as pd
import numpy as np

def check_csv_structure():
    """Check the structure of the cleaned CSV file"""
    
    # Load the CSV
    try:
        df = pd.read_csv('data/cleaned_flower_data.csv')
        print("CSV loaded successfully!")
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return
    
    print(f"\nCSV STRUCTURE ANALYSIS")
    print("=" * 50)
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")
    
    print(f"\nCOLUMN NAMES AND ORDER:")
    print("-" * 30)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")
    
    print(f"\nDATA TYPES:")
    print("-" * 15)
    for col in df.columns:
        dtype = df[col].dtype
        null_count = df[col].isna().sum()
        print(f"{col}: {dtype} (nulls: {null_count})")
    
    print(f"\nPROBLEMATIC COLUMNS ANALYSIS:")
    print("-" * 35)
    
    # Check for columns that might cause import issues
    for col in df.columns:
        if 'season_' in col and col != 'seasonality':
            # Check integer columns
            if df[col].dtype in ['float64', 'object']:
                non_null_values = df[col].dropna()
                if len(non_null_values) > 0:
                    print(f"\n{col}:")
                    print(f"  Type: {df[col].dtype}")
                    print(f"  Null count: {df[col].isna().sum()}")
                    print(f"  Sample non-null values: {non_null_values.head(3).tolist()}")
                    
                    # Check for non-integer values
                    if df[col].dtype == 'object':
                        unique_vals = df[col].dropna().unique()[:10]
                        print(f"  Unique values (first 10): {unique_vals}")
        
        elif col.startswith('has_') or col == 'is_year_round':
            # Check boolean columns
            unique_vals = df[col].unique()
            print(f"\n{col}:")
            print(f"  Type: {df[col].dtype}")
            print(f"  Unique values: {unique_vals}")
    
    print(f"\nEXPECTED POSTGRESQL COLUMN ORDER:")
    print("-" * 40)
    expected_columns = [
        'unique_id', 'product_name', 'variant_name', 'description_clean',
        'variant_price', 'group_category', 'subgroup_category', 
        'product_type_all_flowers', 'recipe_metafield', 'holiday_occasion',
        'diy_level', 'seasonality', 'season_start_month', 'season_start_day',
        'season_end_month', 'season_end_day', 'season_range_2_start_month',
        'season_range_2_start_day', 'season_range_2_end_month', 'season_range_2_end_day',
        'season_range_3_start_month', 'season_range_3_start_day', 
        'season_range_3_end_month', 'season_range_3_end_day', 'is_year_round',
        'colors_raw', 'non_color_options', 'has_red', 'has_pink', 'has_white',
        'has_yellow', 'has_orange', 'has_purple', 'has_blue', 'has_green'
    ]
    
    for i, col in enumerate(expected_columns, 1):
        print(f"{i:2d}. {col}")
    
    print(f"\nCOLUMN COMPARISON:")
    print("-" * 20)
    csv_columns = df.columns.tolist()
    
    if csv_columns == expected_columns:
        print("✅ CSV column order matches expected PostgreSQL order")
    else:
        print("❌ CSV column order does NOT match expected PostgreSQL order")
        
        # Show differences
        print("\nMissing from CSV:")
        for col in expected_columns:
            if col not in csv_columns:
                print(f"  - {col}")
        
        print("\nExtra in CSV:")
        for col in csv_columns:
            if col not in expected_columns:
                print(f"  + {col}")
        
        print("\nOrder differences:")
        for i, (csv_col, exp_col) in enumerate(zip(csv_columns, expected_columns[:len(csv_columns)])):
            if csv_col != exp_col:
                print(f"  Position {i+1}: CSV has '{csv_col}', expected '{exp_col}'")
    
    print(f"\nSAMPLE DATA (first 3 rows):")
    print("-" * 30)
    print(df.head(3).to_string())
    
    print(f"\nRECOMMENDATIONS:")
    print("-" * 20)
    
    # Check for common issues
    issues_found = []
    
    # Check data types
    for col in df.columns:
        if 'season_' in col and col != 'seasonality':
            if df[col].dtype not in ['int64', 'Int64']:
                issues_found.append(f"Column '{col}' is {df[col].dtype}, should be integer")
        elif col.startswith('has_') or col == 'is_year_round':
            if df[col].dtype != 'bool':
                issues_found.append(f"Column '{col}' is {df[col].dtype}, should be boolean")
    
    if issues_found:
        print("Issues found:")
        for issue in issues_found:
            print(f"  ⚠️ {issue}")
    else:
        print("✅ No obvious data type issues found")
    
    # Generate corrected CREATE TABLE statement
    print(f"\nCORRECTED CREATE TABLE STATEMENT:")
    print("-" * 40)
    print("Based on your CSV structure:")
    
    create_table = "CREATE TABLE flowers (\n"
    for i, col in enumerate(df.columns):
        if col == 'unique_id':
            col_def = f"    {col} VARCHAR(255) PRIMARY KEY"
        elif col == 'product_name':
            col_def = f"    {col} TEXT NOT NULL"
        elif col == 'variant_price':
            col_def = f"    {col} DECIMAL(10,2)"
        elif 'season_' in col and col != 'seasonality':
            col_def = f"    {col} INTEGER"
        elif col.startswith('has_') or col == 'is_year_round':
            col_def = f"    {col} BOOLEAN DEFAULT FALSE"
        else:
            col_def = f"    {col} TEXT"
        
        if i < len(df.columns) - 1:
            col_def += ","
        
        create_table += col_def + "\n"
    
    create_table += ");"
    print(create_table)

if __name__ == "__main__":
    check_csv_structure()