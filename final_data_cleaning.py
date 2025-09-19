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

def parse_month_day(date_str):
    """Convert 'May 28' to (5, 28)"""
    month_map = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    try:
        parts = date_str.strip().split()
        month_name = parts[0][:3].lower()
        day = int(parts[1])
        
        if month_name in month_map:
            return month_map[month_name], day
        else:
            print(f"Warning: Unknown month '{month_name}' in date '{date_str}'")
            return None, None
    except (IndexError, ValueError) as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return None, None

def parse_seasonality_to_numeric(seasonality_str):
    """Convert seasonality string to numeric columns
    
    Returns dict with:
    - season_start_month, season_start_day, season_end_month, season_end_day
    - season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day
    - is_year_round
    """
    result = {
        'season_start_month': None,
        'season_start_day': None,
        'season_end_month': None,
        'season_end_day': None,
        'season_range_2_start_month': None,
        'season_range_2_start_day': None,
        'season_range_2_end_month': None,
        'season_range_2_end_day': None,
        'season_range_3_start_month': None, 
        'season_range_3_start_day': None,
        'season_range_3_end_month': None,
        'season_range_3_end_day': None,
        'is_year_round': False
    }
    
    if pd.isna(seasonality_str) or seasonality_str == '':
        return result
    
    seasonality_str = str(seasonality_str).strip()
    
    # Handle year-round
    if seasonality_str.upper() == 'YR':
        result['is_year_round'] = True
        return result
    
    # Split by semicolon for multiple ranges
    ranges = [r.strip() for r in seasonality_str.split(';')]
    
    for i, range_str in enumerate(ranges):
        if ' - ' not in range_str:
            print(f"Warning: Invalid range format '{range_str}' in seasonality '{seasonality_str}'")
            continue
            
        try:
            start_str, end_str = range_str.split(' - ')
            start_month, start_day = parse_month_day(start_str.strip())
            end_month, end_day = parse_month_day(end_str.strip())
            
            if start_month is None or end_month is None:
                continue
                
            if i == 0:
                # First range
                result['season_start_month'] = start_month
                result['season_start_day'] = start_day
                result['season_end_month'] = end_month
                result['season_end_day'] = end_day
            elif i == 1:
                # Second range
                result['season_range_2_start_month'] = start_month
                result['season_range_2_start_day'] = start_day
                result['season_range_2_end_month'] = end_month
                result['season_range_2_end_day'] = end_day
            elif i == 2:
                # Third range
                result['season_range_3_start_month'] = start_month
                result['season_range_3_start_day'] = start_day
                result['season_range_3_end_month'] = end_month
                result['season_range_3_end_day'] = end_day
            else:
                print(f"Warning: More than 3 ranges found in seasonality '{seasonality_str}', ignoring additional ranges")
                
        except Exception as e:
            print(f"Warning: Error parsing range '{range_str}': {e}")
            continue
    
    return result

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
    
    # Check Variant status values
    if 'Variant status' in df.columns:
        print(f"\nVariant status values:")
        variant_status_counts = df['Variant status'].value_counts(dropna=False)
        print(variant_status_counts)
    else:
        print("\n'Variant status' column not found!")
        print("Available columns containing 'variant' and 'status':")
        variant_status_cols = [col for col in df.columns if 'variant' in col.lower() and 'status' in col.lower()]
        print(variant_status_cols)
    
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

def filter_active_products_and_variants(df):
    """Filter to keep only active products AND active variants"""
    print("\nFiltering for active products and variants...")
    initial_count = len(df)
    
    # Track filtering steps
    removed_by_product_status = 0
    removed_by_variant_status = 0
    
    # Filter by Product status
    if 'Product status' in df.columns:
        print(f"\nProduct status analysis:")
        status_counts = df['Product status'].value_counts(dropna=False)
        print(status_counts)
        
        unique_statuses = df['Product status'].unique()
        print(f"Unique product status values: {unique_statuses}")
        
        # Filter for active products
        if 'Active' in unique_statuses:
            before_filter = len(df)
            df = df[df['Product status'] == 'Active']
            removed_by_product_status = before_filter - len(df)
            print(f"Filtered to 'Active' products: {len(df)} (removed {removed_by_product_status})")
        elif 'active' in unique_statuses:
            before_filter = len(df)
            df = df[df['Product status'] == 'active']
            removed_by_product_status = before_filter - len(df)
            print(f"Filtered to 'active' products: {len(df)} (removed {removed_by_product_status})")
        else:
            print("Warning: No 'Active' status found in Product status. Keeping all products.")
    else:
        print("No 'Product status' column found. Skipping product status filtering.")
    
    # Filter by Variant status
    if 'Variant status' in df.columns:
        print(f"\nVariant status analysis:")
        variant_status_counts = df['Variant status'].value_counts(dropna=False)
        print(variant_status_counts)
        
        unique_variant_statuses = df['Variant status'].unique()
        print(f"Unique variant status values: {unique_variant_statuses}")
        
        # Filter for active variants
        if 'Active' in unique_variant_statuses:
            before_filter = len(df)
            df = df[df['Variant status'] == 'Active']
            removed_by_variant_status = before_filter - len(df)
            print(f"Filtered to 'Active' variants: {len(df)} (removed {removed_by_variant_status})")
        elif 'active' in unique_variant_statuses:
            before_filter = len(df)
            df = df[df['Variant status'] == 'active']
            removed_by_variant_status = before_filter - len(df)
            print(f"Filtered to 'active' variants: {len(df)} (removed {removed_by_variant_status})")
        else:
            print("Warning: No 'Active' status found in Variant status. Keeping all variants.")
    else:
        print("No 'Variant status' column found. Skipping variant status filtering.")
    
    # Summary of filtering
    total_removed = removed_by_product_status + removed_by_variant_status
    print(f"\nFiltering Summary:")
    print(f"  Initial rows: {initial_count}")
    print(f"  Removed by Product status: {removed_by_product_status}")
    print(f"  Removed by Variant status: {removed_by_variant_status}")
    print(f"  Final rows: {len(df)}")
    print(f"  Total removed: {total_removed}")
    
    return df

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
            
            # Process seasonality to numeric columns
            seasonality_col = 'Seasonality (by semicolon)' if 'Seasonality (by semicolon)' in new_row.index else None
            seasonality_data = parse_seasonality_to_numeric(new_row[seasonality_col] if seasonality_col else '')
            for col, val in seasonality_data.items():
                # Convert None to np.nan for proper CSV handling
                new_row[col] = val if val is not None else np.nan
            
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
        
        # Process seasonality to numeric columns
        seasonality_col = 'Seasonality (by semicolon)' if 'Seasonality (by semicolon)' in base_row.index else None
        seasonality_data = parse_seasonality_to_numeric(base_row[seasonality_col] if seasonality_col else '')
        for col, val in seasonality_data.items():
            base_row[col] = val
        
        result_rows.append(base_row)
    
    return result_rows

def test_seasonality_parsing(df):
    """Test the seasonality parsing on actual data"""
    print("\nTesting seasonality parsing...")
    
    if 'Seasonality (by semicolon)' not in df.columns:
        print("No seasonality column found for testing")
        return
    
    # Get unique seasonality values
    unique_seasonality = df['Seasonality (by semicolon)'].dropna().unique()
    print(f"Found {len(unique_seasonality)} unique seasonality patterns")
    
    # Test parsing on a few examples
    test_cases = unique_seasonality[:10]  # Test first 10
    
    for seasonality in test_cases:
        print(f"\nTesting: '{seasonality}'")
        result = parse_seasonality_to_numeric(seasonality)
        
        if result['is_year_round']:
            print("  → Year-round product")
        else:
            # Primary range
            if result['season_start_month']:
                print(f"  → Range 1: {result['season_start_month']}/{result['season_start_day']} - {result['season_end_month']}/{result['season_end_day']}")
            
            # Secondary range
            if result['season_range_2_start_month']:
                print(f"  → Range 2: {result['season_range_2_start_month']}/{result['season_range_2_start_day']} - {result['season_range_2_end_month']}/{result['season_range_2_end_day']}")

def clean_flower_data():
    """Main data cleaning function"""
    print("FINAL FLOWER DATA CLEANING WITH NUMERIC SEASONALITY")
    print("=" * 60)
    
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
    
    # Test seasonality parsing before processing
    test_seasonality_parsing(df)
    
    # Define comprehensive color keywords for option detection
    color_keywords = [
        'white', 'pink', 'purple', 'yellow', 'orange', 'lavender', 'cream', 'hot', 'light', 'dark', 
        'red', 'blue', 'green', 'tinted', 'burgundy', 'magenta', 'coral', 'peach', 'ivory', 'salmon',
        'bicolor', 'black', 'brown', 'bronze', 'silver', 'gold', 'gray', 'champagne'
    ]
    
    # Phase 2: Initial Data Preparation
    print("\nPhase 2: Initial Data Preparation")
    
    # Keep only essential columns that actually exist - UPDATED to include Variant status
    essential_columns = [
        'Product ID', 'Variant ID', 'Product name', 'Variant name', 'Group', 'Subgroup',
        'Variant price', 'Product status', 'Variant status', 'Colors (by semicolon)', 'Seasonality (by semicolon)',
        'attributes.Holiday Occasion', 'attributes.DIY Level', 'attributes.Product Type - All Flowers',
        'attributes.Recipe metafield', 'attributes.Description', 'Option value label'
    ]
    
    available_columns = [col for col in essential_columns if col in df.columns]
    missing_columns = [col for col in essential_columns if col not in df.columns]
    
    print(f"Keeping {len(available_columns)} essential columns")
    if missing_columns:
        print(f"Warning: Missing columns: {missing_columns}")
    
    df_clean = df[available_columns].copy()
    
    # UPDATED: Filter for active products AND active variants
    df_clean = filter_active_products_and_variants(df_clean)
    
    # If we have no data left, stop here with better error handling
    if len(df_clean) == 0:
        print("\nERROR: No data remaining after status filtering!")
        print("This suggests the Product/Variant status filtering is too restrictive.")
        print("Please check the actual values in your status columns.")
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
            
            # Process seasonality to numeric columns
            seasonality_col = 'Seasonality (by semicolon)' if 'Seasonality (by semicolon)' in row.index else None
            seasonality_data = parse_seasonality_to_numeric(row[seasonality_col] if seasonality_col else '')
            for col, val in seasonality_data.items():
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
        'Variant price': 'variant_price',
        'attributes.Holiday Occasion': 'holiday_occasion',
        'attributes.DIY Level': 'diy_level',
        'Seasonality (by semicolon)': 'seasonality',
        'attributes.Product Type - All Flowers': 'product_type_all_flowers',
        'attributes.Recipe metafield': 'recipe_metafield'
    }
    
    for old_col, new_col in column_mapping.items():
        if old_col in df_final.columns:
            df_final[new_col] = df_final[old_col]
    
    # Define final column order - UPDATED to include numeric seasonality columns with 3rd range
    final_columns = [
        # Identity & Display (4)
        'unique_id', 'product_name', 'variant_name', 'description_clean',
        
        # Core Raw Data (9) - keeping original seasonality for reference
        'variant_price', 'group_category', 'subgroup_category', 
        'product_type_all_flowers', 'recipe_metafield', 'holiday_occasion',
        'diy_level', 'colors_raw', 'seasonality',
        
        # Numeric Seasonality Columns (13) - now includes 3rd range
        'season_start_month', 'season_start_day', 'season_end_month', 'season_end_day',
        'season_range_2_start_month', 'season_range_2_start_day', 'season_range_2_end_month', 'season_range_2_end_day',
        'season_range_3_start_month', 'season_range_3_start_day', 'season_range_3_end_month', 'season_range_3_end_day',
        'is_year_round',
        
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
    
    # Check seasonality processing
    seasonality_check = {
        'year_round': df_final['is_year_round'].sum() if 'is_year_round' in df_final.columns else 0,
        'with_ranges': df_final['season_start_month'].count() if 'season_start_month' in df_final.columns else 0,
        'with_dual_ranges': df_final['season_range_2_start_month'].count() if 'season_range_2_start_month' in df_final.columns else 0
    }
    print(f"Seasonality processing: {seasonality_check}")
    
    # Phase 6: Post-process numeric columns for PostgreSQL compatibility
    print("\nPhase 6: Post-process for PostgreSQL compatibility")
    
    # Convert float columns with NaN to proper integer/boolean format for PostgreSQL
    numeric_columns = [
        'season_start_month', 'season_start_day', 'season_end_month', 'season_end_day',
        'season_range_2_start_month', 'season_range_2_start_day', 'season_range_2_end_month', 'season_range_2_end_day',
        'season_range_3_start_month', 'season_range_3_start_day', 'season_range_3_end_month', 'season_range_3_end_day'
    ]
    
    for col in numeric_columns:
        if col in df_final.columns:
            # Convert to nullable integer type for PostgreSQL
            df_final[col] = df_final[col].astype('Int64')  # Pandas nullable integer
    
    # Ensure boolean columns are proper boolean type
    boolean_columns = [col for col in df_final.columns if col.startswith('has_') or col == 'is_year_round']
    for col in boolean_columns:
        if col in df_final.columns:
            df_final[col] = df_final[col].astype(bool)
    
    print(f"Processed {len(numeric_columns)} numeric columns for PostgreSQL compatibility")
    print(f"Processed {len(boolean_columns)} boolean columns for PostgreSQL compatibility")
    
    # Phase 7: Output and Reporting
    print("\nPhase 7: Saving Results")
    
    # Save cleaned data
    df_final.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved cleaned data to {OUTPUT_PATH}")
    
    # Generate summary report
    create_cleaning_summary(df_final, len(df), duplicates_count, color_expansions)
    
    return df_final

def create_cleaning_summary(df, original_rows, duplicates_processed, color_expansions):
    """Create comprehensive cleaning summary"""
    summary = []
    summary.append("FINAL DATA CLEANING SUMMARY WITH NUMERIC SEASONALITY")
    summary.append("=" * 60)
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
    
    # Check seasonality processing
    if 'is_year_round' in df.columns:
        year_round = df['is_year_round'].sum()
        summary.append(f"Year-round products: {year_round}/{len(df)} ({year_round/len(df)*100:.1f}%)")
    
    if 'season_start_month' in df.columns:
        with_ranges = df['season_start_month'].count()
        summary.append(f"Products with date ranges: {with_ranges}/{len(df)} ({with_ranges/len(df)*100:.1f}%)")
    
    if 'season_range_3_start_month' in df.columns:
        triple_ranges = df['season_range_3_start_month'].count()
        summary.append(f"Products with triple ranges: {triple_ranges}/{len(df)} ({triple_ranges/len(df)*100:.1f}%)")
    
    summary.append("")
    summary.append("NEW NUMERIC SEASONALITY COLUMNS:")
    summary.append("-" * 40)
    summary.append("✓ season_start_month, season_start_day")
    summary.append("✓ season_end_month, season_end_day")
    summary.append("✓ season_range_2_start_month, season_range_2_start_day")
    summary.append("✓ season_range_2_end_month, season_range_2_end_day")
    summary.append("✓ season_range_3_start_month, season_range_3_start_day")
    summary.append("✓ season_range_3_end_month, season_range_3_end_day")
    summary.append("✓ is_year_round")
    
    summary.append("")
    summary.append("READY FOR:")
    summary.append("- PostgreSQL import with 3-range seasonality support")
    summary.append("- SQL-based date filtering using numeric comparisons")
    summary.append("- Chatbot filtering with direct SQL queries")
    summary.append("- High-performance date range queries")
    summary.append("- Complete seasonality coverage (no data loss)")
    
    # Save summary
    with open('data/final_cleaning_summary.txt', 'w') as f:
        f.write('\n'.join(summary))
    
    print(f"Summary saved to data/final_cleaning_summary.txt")
    
    # Print seasonality examples
    print("\nSeasonality Processing Examples:")
    print("-" * 40)
    
    # Show examples of processed seasonality data
    if 'seasonality' in df.columns:
        example_data = df[df['seasonality'].notna()].head(5)
        for idx, row in example_data.iterrows():
            original = row.get('seasonality', 'N/A')
            if row.get('is_year_round', False):
                processed = "Year-round"
            else:
                range1 = f"{row.get('season_start_month', 'N/A')}/{row.get('season_start_day', 'N/A')} - {row.get('season_end_month', 'N/A')}/{row.get('season_end_day', 'N/A')}"
                range2 = ""
                if pd.notna(row.get('season_range_2_start_month')):
                    range2 = f" + {row.get('season_range_2_start_month', 'N/A')}/{row.get('season_range_2_start_day', 'N/A')} - {row.get('season_range_2_end_month', 'N/A')}/{row.get('season_range_2_end_day', 'N/A')}"
                processed = range1 + range2
            
            print(f"'{original}' → {processed}")

def main():
    """Main execution function"""
    try:
        cleaned_df = clean_flower_data()
        
        if cleaned_df is not None:
            print("\n" + "=" * 60)
            print("DATA CLEANING WITH NUMERIC SEASONALITY COMPLETED!")
            print("=" * 60)
            print(f"Final dataset: {len(cleaned_df)} rows, {len(cleaned_df.columns)} columns")
            print("\nFiles created:")
            print("- data/cleaned_flower_data.csv")
            print("- data/final_cleaning_summary.txt")
            print("\nNew Features:")
            print("✓ Numeric seasonality columns for SQL date filtering")
            print("✓ Support for dual date ranges (year-boundary seasons)")
            print("✓ Year-round product identification")
            print("\nDataset is ready for PostgreSQL import with enhanced date filtering!")
        else:
            print("\n" + "=" * 60)
            print("DATA CLEANING FAILED!")
            print("=" * 60)
            print("Please check the debug output above to understand the issue.")
        
    except Exception as e:
        print(f"Error during data cleaning: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()