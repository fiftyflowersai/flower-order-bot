import pandas as pd
import numpy as np
import re
import json
import os
from collections import defaultdict

# File paths
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
OUTPUT_PATH = "data/cleaned_flower_data.csv"
COLOR_MAPPING_PATH = "data/color_mapping.json"

def load_color_mapping():
    """Load the manual color mapping for boolean column creation"""
    try:
        with open(COLOR_MAPPING_PATH, 'r') as f:
            color_mapping = json.load(f)
        print(f"Loaded color mapping with {len(color_mapping['color_categories'])} categories")
        return color_mapping
    except FileNotFoundError:
        print(f"Warning: {COLOR_MAPPING_PATH} not found. Using default color mapping.")
        # Fallback color mapping
        return {
            "color_categories": {
                "red": ["red", "true red", "burgundy", "cranberry", "wine red", "rust"],
                "pink": ["pink", "light pink", "hot pink", "true pink", "blush", "blush pink", 
                        "fuchsia", "magenta", "coral", "dusty pink", "dusty rose", "mauve"],
                "white": ["white", "ivory", "clear", "natural", "champagne"],
                "yellow": ["yellow", "amber", "chartreuse", "gold", "pale yellow", "mustard yellow", "dark yellow"],
                "orange": ["orange", "peach", "sunset", "terracotta", "copper", "dark orange", "true orange"],
                "purple": ["purple", "lavender", "pinky lavender", "true purple", "dark purple"],
                "blue": ["blue", "soft blue", "light blue", "teal"],
                "green": ["green", "sage green", "emerald green", "forest green", "lime green", 
                         "light green updated", "true green"]
            }
        }

def debug_data_structure(df):
    """Debug the data structure to understand what we're working with"""
    print("\nDEBUG: Data Structure Analysis")
    print("-" * 40)
    print(f"Total rows: {len(df)}")
    print(f"Total columns: {len(df.columns)}")
    
    # Check Product status values
    if 'Product status' in df.columns:
        print(f"\nProduct status values:")
        status_counts = df['Product status'].value_counts(dropna=False)
        print(status_counts)
    else:
        print("\n'Product status' column not found!")
        print("Available columns containing 'status':")
        status_cols = [col for col in df.columns if 'status' in col.lower()]
        print(status_cols)
    
    # Check for critical columns
    critical_columns = ['Product ID', 'Variant ID', 'Product name', 'Variant price']
    print(f"\nCritical columns check:")
    for col in critical_columns:
        if col in df.columns:
            non_null = df[col].count()
            print(f"✓ {col}: {non_null}/{len(df)} non-null values")
        else:
            print(f"✗ {col}: NOT FOUND")
            # Look for similar columns
            similar = [c for c in df.columns if col.lower().replace(' ', '') in c.lower().replace(' ', '')]
            if similar:
                print(f"   Similar columns found: {similar}")
    
    # Show first few column names
    print(f"\nFirst 20 columns:")
    for i, col in enumerate(df.columns[:20]):
        print(f"{i+1:2d}. {col}")
    
    if len(df.columns) > 20:
        print(f"... and {len(df.columns) - 20} more columns")

def strip_html_tags(text):
    """Remove HTML tags from text"""
    if pd.isna(text):
        return text
    
    text = str(text)
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    # Replace HTML entities
    clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    clean_text = clean_text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&#39;', "'")
    # Clean up extra whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

def split_semicolon_values(value):
    """Split semicolon-separated values and return clean list"""
    if pd.isna(value):
        return []
    
    value = str(value).strip()
    if not value or value.lower() == 'nan':
        return []
    
    if ';' in value:
        return [v.strip().lower() for v in value.split(';') if v.strip()]
    else:
        return [value.strip().lower()] if value.strip() else []

def is_color_option(option_label, color_keywords):
    """Check if an option label contains color information"""
    if pd.isna(option_label):
        return False
    
    label_lower = str(option_label).lower()
    return any(keyword in label_lower for keyword in color_keywords)

def create_color_booleans(colors_list, color_mapping):
    """Create boolean columns based on color list and mapping"""
    booleans = {
        'has_red': False, 'has_pink': False, 'has_white': False,
        'has_yellow': False, 'has_orange': False, 'has_purple': False,
        'has_blue': False, 'has_green': False
    }
    
    for color in colors_list:
        color_lower = color.lower().strip()
        for category, color_list in color_mapping['color_categories'].items():
            if color_lower in color_list:
                booleans[f'has_{category}'] = True
    
    return booleans

def process_duplicate_group(group_df, color_keywords, color_mapping):
    """Process a group of duplicate rows (same composite ID)"""
    # Get option labels for this group
    option_labels = group_df['Option value label'].dropna().unique() if 'Option value label' in group_df.columns else []
    
    # Separate color and non-color options
    color_options = []
    non_color_options = []
    
    for label in option_labels:
        if is_color_option(label, color_keywords):
            color_options.append(str(label))
        else:
            non_color_options.append(str(label))
    
    result_rows = []
    
    if color_options:
        # Expand into separate rows for each color option
        print(f"  Expanding {len(color_options)} color options for {group_df['Product name'].iloc[0][:50]}...")
        
        for i, color_option in enumerate(color_options):
            # Create a copy of the first row as base
            new_row = group_df.iloc[0].copy()
            
            # Update unique identifier
            base_id = f"{new_row['Product ID']}_{new_row['Variant ID']}"
            new_row['unique_id'] = f"{base_id}_color_{i+1}"
            
            # Update product name to include color
            new_row['product_name'] = f"{new_row['Product name']} - {color_option}"
            
            # Update colors field - add option color to existing colors
            colors_col = 'Colors (by semicolon)' if 'Colors (by semicolon)' in new_row.index else None
            existing_colors = split_semicolon_values(new_row[colors_col] if colors_col else '')
            option_color_clean = color_option.lower().strip()
            if option_color_clean not in existing_colors:
                existing_colors.append(option_color_clean)
            new_row['colors_raw'] = ';'.join(existing_colors)
            
            # Store non-color options if any
            new_row['non_color_options'] = ';'.join(non_color_options) if non_color_options else ''
            
            # Create color boolean columns
            color_bools = create_color_booleans(existing_colors, color_mapping)
            for col, val in color_bools.items():
                new_row[col] = val
            
            result_rows.append(new_row)
    
    else:
        # No color options - keep single row with aggregated non-color options
        base_row = group_df.iloc[0].copy()
        base_id = f"{base_row['Product ID']}_{base_row['Variant ID']}"
        base_row['unique_id'] = base_id
        base_row['product_name'] = base_row['Product name']
        
        # Store non-color options
        base_row['non_color_options'] = ';'.join(non_color_options) if non_color_options else ''
        
        # Process colors normally
        colors_col = 'Colors (by semicolon)' if 'Colors (by semicolon)' in base_row.index else None
        existing_colors = split_semicolon_values(base_row[colors_col] if colors_col else '')
        base_row['colors_raw'] = ';'.join(existing_colors)
        
        # Create color boolean columns
        color_bools = create_color_booleans(existing_colors, color_mapping)
        for col, val in color_bools.items():
            base_row[col] = val
        
        result_rows.append(base_row)
    
    return result_rows

def clean_flower_data():
    """Main data cleaning function"""
    print("FINAL FLOWER DATA CLEANING")
    print("=" * 50)
    
    # Phase 1: Setup and Validation
    print("\nPhase 1: Setup and Validation")
    os.makedirs('data', exist_ok=True)
    
    try:
        df = pd.read_excel(FILE_PATH)
        print(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"Error loading data: {e}")
        return None
    
    # DEBUG: Analyze data structure
    debug_data_structure(df)
    
    color_mapping = load_color_mapping()
    
    # Define comprehensive color keywords for option detection
    color_keywords = [
        'white', 'pink', 'purple', 'yellow', 'orange', 'lavender', 'cream', 'hot', 'light', 'dark', 
        'red', 'blue', 'green', 'tinted', 'burgundy', 'magenta', 'coral', 'peach', 'ivory', 'salmon',
        'bicolor', 'black', 'brown', 'bronze', 'silver', 'gold', 'gray', 'champagne'
    ]
    
    # Phase 2: Initial Data Preparation
    print("\nPhase 2: Initial Data Preparation")
    
    # Keep only essential columns that actually exist
    essential_columns = [
        'Product ID', 'Variant ID', 'Product name', 'Variant name', 'Group', 'Subgroup',
        'Variant price', 'Product status', 'Colors (by semicolon)', 'Seasonality (by semicolon)',
        'attributes.Holiday Occasion', 'attributes.DIY Level', 'attributes.Product Type - All Flowers',
        'attributes.Recipe metafield', 'attributes.Description', 'Option value label'
    ]
    
    available_columns = [col for col in essential_columns if col in df.columns]
    missing_columns = [col for col in essential_columns if col not in df.columns]
    
    print(f"Keeping {len(available_columns)} essential columns")
    if missing_columns:
        print(f"Warning: Missing columns: {missing_columns}")
    
    df_clean = df[available_columns].copy()
    
    # FIXED: Handle Product status filtering more carefully
    if 'Product status' in df_clean.columns:
        print(f"\nProduct status analysis:")
        status_counts = df_clean['Product status'].value_counts(dropna=False)
        print(status_counts)
        
        # Check what status values we actually have
        unique_statuses = df_clean['Product status'].unique()
        print(f"Unique status values: {unique_statuses}")
        
        # Try different filtering approaches
        if 'Active' in unique_statuses:
            initial_count = len(df_clean)
            df_clean = df_clean[df_clean['Product status'] == 'Active']
            print(f"Filtered to 'Active' products: {len(df_clean)} (removed {initial_count - len(df_clean)})")
        elif 'active' in unique_statuses:
            initial_count = len(df_clean)
            df_clean = df_clean[df_clean['Product status'] == 'active']
            print(f"Filtered to 'active' products: {len(df_clean)} (removed {initial_count - len(df_clean)})")
        else:
            # If no clear 'Active' status, skip filtering and warn
            print("Warning: No 'Active' status found. Keeping all products.")
            print("Consider manually checking what status values indicate active products.")
    else:
        print("No 'Product status' column found. Keeping all products.")
    
    # If we have no data left, stop here with better error handling
    if len(df_clean) == 0:
        print("\nERROR: No data remaining after filtering!")
        print("This suggests the Product status filtering is too restrictive.")
        print("Please check the actual values in your Product status column.")
        return None
    
    # Remove rows missing critical data
    critical_columns = ['Product ID', 'Variant ID', 'Product name']
    existing_critical = [col for col in critical_columns if col in df_clean.columns]
    
    initial_rows = len(df_clean)
    df_clean = df_clean.dropna(subset=existing_critical)
    final_rows = len(df_clean)
    print(f"Removed {initial_rows - final_rows} rows with missing critical data")
    
    # If we still have no data, stop here
    if len(df_clean) == 0:
        print("\nERROR: No data remaining after removing rows with missing critical data!")
        return None
    
    # Clean HTML from description
    if 'attributes.Description' in df_clean.columns:
        print("Cleaning HTML from descriptions...")
        df_clean['description_clean'] = df_clean['attributes.Description'].apply(strip_html_tags)
    else:
        df_clean['description_clean'] = ''
    
    # Phase 3: Handle Duplicate Composite IDs
    print("\nPhase 3: Handle Duplicate Composite IDs")
    
    # Create composite ID
    df_clean['composite_id'] = df_clean['Product ID'].astype(str) + '_' + df_clean['Variant ID'].astype(str)
    
    # Group by composite ID
    grouped = df_clean.groupby('composite_id')
    
    duplicates_count = 0
    singles_count = 0
    color_expansions = 0
    
    print("Processing duplicate groups...")
    all_processed_rows = []
    
    for composite_id, group in grouped:
        if len(group) > 1:
            # Handle duplicates
            duplicates_count += 1
            processed_rows = process_duplicate_group(group, color_keywords, color_mapping)
            color_expansions += len(processed_rows) - 1  # Subtract 1 for original
            all_processed_rows.extend(processed_rows)
        else:
            # Single row - process normally
            singles_count += 1
            row = group.iloc[0].copy()
            row['unique_id'] = composite_id
            row['product_name'] = row['Product name']
            row['non_color_options'] = ''
            
            # Process colors
            colors_col = 'Colors (by semicolon)' if 'Colors (by semicolon)' in row.index else None
            existing_colors = split_semicolon_values(row[colors_col] if colors_col else '')
            row['colors_raw'] = ';'.join(existing_colors)
            
            # Create color boolean columns
            color_bools = create_color_booleans(existing_colors, color_mapping)
            for col, val in color_bools.items():
                row[col] = val
            
            all_processed_rows.append(row)
    
    print(f"Processed {duplicates_count} duplicate groups and {singles_count} single products")
    print(f"Created {color_expansions} additional rows from color expansions")
    
    # Convert back to DataFrame
    if not all_processed_rows:
        print("\nERROR: No processed rows to convert to DataFrame!")
        return None
        
    df_final = pd.DataFrame(all_processed_rows)
    
    # Phase 4: Clean and Rename Columns
    print("\nPhase 4: Final Column Setup")
    
    # Column renaming
    column_mapping = {
        'Group': 'group_category',
        'Subgroup': 'subgroup_category', 
        'Variant name': 'variant_name',
        'attributes.Holiday Occasion': 'holiday_occasion',
        'attributes.DIY Level': 'diy_level',
        'Seasonality (by semicolon)': 'seasonality',
        'attributes.Product Type - All Flowers': 'product_type_all_flowers',
        'attributes.Recipe metafield': 'recipe_metafield'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df_final.columns:
            df_final[new_col] = df_final[old_col]
    
    # Define final column order
    final_columns = [
        # Identity & Display (4)
        'unique_id', 'product_name', 'variant_name', 'description_clean',
        
        # Core Raw Data (8)
        'variant_price', 'group_category', 'subgroup_category', 
        'product_type_all_flowers', 'recipe_metafield', 'holiday_occasion',
        'diy_level', 'colors_raw', 'seasonality',
        
        # Non-color options (1)
        'non_color_options',
        
        # Color Boolean Columns (8)
        'has_red', 'has_pink', 'has_white', 'has_yellow',
        'has_orange', 'has_purple', 'has_blue', 'has_green'
    ]
    
    # Keep only final columns that exist
    available_final_columns = [col for col in final_columns if col in df_final.columns]
    df_final = df_final[available_final_columns]
    
    print(f"Final dataset: {len(df_final)} rows, {len(df_final.columns)} columns")
    
    # Phase 5: Final Validation
    print("\nPhase 5: Final Validation")
    
    # Check unique IDs
    if 'unique_id' in df_final.columns:
        unique_ids = df_final['unique_id'].nunique()
        total_rows = len(df_final)
        
        if unique_ids == total_rows:
            print("✓ All unique_id values are unique")
        else:
            print(f"⚠ Warning: {total_rows - unique_ids} duplicate unique_id values")
    else:
        print("⚠ Warning: unique_id column not found in final dataset")
    
    # Check color boolean coverage
    color_columns = [col for col in df_final.columns if col.startswith('has_')]
    if color_columns:
        products_with_colors = df_final[color_columns].any(axis=1).sum()
        print(f"Products with color categories: {products_with_colors}/{len(df_final)}")
    
    # Phase 6: Output and Reporting
    print("\nPhase 6: Saving Results")
    
    # Save cleaned data
    df_final.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved cleaned data to {OUTPUT_PATH}")
    
    # Generate summary report
    create_cleaning_summary(df_final, len(df), duplicates_count, color_expansions)
    
    return df_final

def create_cleaning_summary(df, original_rows, duplicates_processed, color_expansions):
    """Create comprehensive cleaning summary"""
    summary = []
    summary.append("FINAL DATA CLEANING SUMMARY")
    summary.append("=" * 50)
    summary.append("")
    summary.append(f"Original rows: {original_rows}")
    summary.append(f"Final rows: {len(df)}")
    summary.append(f"Duplicate groups processed: {duplicates_processed}")
    summary.append(f"Color expansions created: {color_expansions}")
    summary.append(f"Final columns: {len(df.columns)}")
    summary.append("")
    
    summary.append("COLUMN BREAKDOWN:")
    summary.append("-" * 30)
    for col in df.columns:
        non_null = df[col].count()
        pct = (non_null / len(df)) * 100
        summary.append(f"{col}: {non_null}/{len(df)} ({pct:.1f}%)")
    
    summary.append("")
    summary.append("DATA QUALITY CHECKS:")
    summary.append("-" * 30)
    
    # Check unique IDs
    if 'unique_id' in df.columns:
        unique_ids = df['unique_id'].nunique()
        summary.append(f"Unique IDs: {unique_ids}/{len(df)} ({'✓' if unique_ids == len(df) else '⚠'})")
    
    # Check color coverage
    color_cols = [col for col in df.columns if col.startswith('has_')]
    if color_cols:
        with_colors = df[color_cols].any(axis=1).sum()
        summary.append(f"Products with colors: {with_colors}/{len(df)} ({with_colors/len(df)*100:.1f}%)")
    
    # Check price coverage
    if 'variant_price' in df.columns:
        with_price = df['variant_price'].count()
        summary.append(f"Products with prices: {with_price}/{len(df)} ({with_price/len(df)*100:.1f}%)")
    
    summary.append("")
    summary.append("READY FOR:")
    summary.append("- PostgreSQL import")
    summary.append("- Chatbot filtering and recommendations")
    summary.append("- SQL queries with boolean color columns")
    
    # Save summary
    with open('data/final_cleaning_summary.txt', 'w') as f:
        f.write('\n'.join(summary))
    
    print(f"Summary saved to data/final_cleaning_summary.txt")

def main():
    """Main execution function"""
    try:
        cleaned_df = clean_flower_data()
        
        if cleaned_df is not None:
            print("\n" + "=" * 50)
            print("DATA CLEANING COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print(f"Final dataset: {len(cleaned_df)} rows, {len(cleaned_df.columns)} columns")
            print("\nFiles created:")
            print("- data/cleaned_flower_data.csv")
            print("- data/final_cleaning_summary.txt")
            print("\nDataset is ready for PostgreSQL import and chatbot implementation!")
        else:
            print("\n" + "=" * 50)
            print("DATA CLEANING FAILED!")
            print("=" * 50)
            print("Please check the debug output above to understand the issue.")
        
    except Exception as e:
        print(f"Error during data cleaning: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()