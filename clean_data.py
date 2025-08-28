import pandas as pd
import numpy as np
import re
from datetime import datetime
import json

# File paths
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
OUTPUT_PATH = "data/cleaned_flower_data.csv"

def load_and_analyze_missing_data():
    """Load data and identify columns to drop based on missing values"""
    df = pd.read_excel(FILE_PATH)
    
    # Calculate missing percentages
    missing_percentages = (df.isnull().sum() / len(df)) * 100
    
    # Identify columns to drop (>90% missing)
    columns_to_drop = missing_percentages[missing_percentages > 90].index.tolist()
    
    print(f"Columns to drop due to >90% missing values: {len(columns_to_drop)}")
    print("Sample columns being dropped:", columns_to_drop[:10])
    
    return df, columns_to_drop

def strip_html_tags(text):
    """Remove HTML tags from text"""
    if pd.isna(text):
        return text
    
    text = str(text)
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    # Replace HTML entities
    clean_text = clean_text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    # Clean up extra whitespace
    clean_text = ' '.join(clean_text.split())
    
    return clean_text

def split_semicolon_values(series, to_lowercase=True):
    """Split semicolon-separated values and return unique sorted list"""
    all_values = []
    
    for value in series.dropna():
        if pd.isna(value):
            continue
            
        value = str(value)
        if ';' in value:
            split_vals = [v.strip() for v in value.split(';') if v.strip()]
        else:
            split_vals = [value.strip()] if value.strip() else []
        
        if to_lowercase:
            split_vals = [v.lower() for v in split_vals]
            
        all_values.extend(split_vals)
    
    return sorted(list(set(all_values)))

def parse_seasonality_dates(seasonality_value):
    """Parse seasonality date ranges into structured format"""
    if pd.isna(seasonality_value) or seasonality_value == 'YR':
        return 'Year Round'
    
    # Handle cases like "Dec 15 - Dec 31;Jan 01 - Apr 20"
    date_ranges = []
    for range_part in str(seasonality_value).split(';'):
        range_part = range_part.strip()
        if ' - ' in range_part:
            try:
                start_date, end_date = range_part.split(' - ')
                date_ranges.append(f"{start_date.strip()} to {end_date.strip()}")
            except:
                date_ranges.append(range_part)
        else:
            date_ranges.append(range_part)
    
    return '; '.join(date_ranges)

def create_color_categories():
    """Define color categories for grouping similar colors"""
    color_categories = {
        'red': ['red', 'true red', 'burgundy', 'cranberry', 'maroon', 'crimson'],
        'pink': ['pink', 'light pink', 'hot pink', 'true pink', 'blush', 'fuchsia', 'magenta', 'coral'],
        'white': ['white', 'ivory', 'cream', 'off-white'],
        'yellow': ['yellow', 'golden', 'amber', 'chartreuse', 'lemon'],
        'orange': ['orange', 'peach', 'sunset', 'terracotta', 'apricot'],
        'purple': ['purple', 'lavender', 'pinky lavender', 'violet', 'plum'],
        'blue': ['blue', 'soft blue', 'navy', 'light blue'],
        'green': ['green', 'sage', 'mint', 'lime'],
        'brown': ['brown', 'bronze', 'chocolate', 'tan'],
        'mixed': ['farm mixes', 'rainbow', 'multicolor', 'assorted']
    }
    return color_categories

def categorize_colors(color_list, color_categories):
    """Categorize colors into color families"""
    if not color_list:
        return []
    
    categories = set()
    
    for color in color_list:
        color_lower = color.lower().strip()
        
        # Find which category this color belongs to
        for category, colors in color_categories.items():
            if any(cat_color in color_lower for cat_color in colors):
                categories.add(category)
                break
        else:
            # If no category found, add as-is
            categories.add(color_lower)
    
    return sorted(list(categories))

def clean_data():
    """Main data cleaning function"""
    print("Starting data cleaning process...")
    
    # Load data and identify columns to drop
    df, columns_to_drop = load_and_analyze_missing_data()
    
    # Drop columns with excessive missing values
    df_clean = df.drop(columns=columns_to_drop)
    print(f"Dropped {len(columns_to_drop)} columns with >90% missing values")
    print(f"Remaining columns: {len(df_clean.columns)}")
    
    # Define core columns for the chatbot (based on EDA findings)
    core_columns = [
        'Product ID',
        'Product name',
        'Group',
        'Variant price',
        'Seasonality (by semicolon)',
        'Colors (by semicolon)',
        'attributes.Recipe description',
        'attributes.DIY Level',
        'attributes.Holiday Occasion',
        'attributes.Description',
        'attributes.Product Type',
        'attributes.Product Type - All Flowers',
        'attributes.Recipe metafield',
        'attributes.Expected Vase Life',
        'attributes.Stems Per Bunch',
        'attributes.Average Stem Length',
        'attributes.Color Description'
    ]
    
    # Keep only columns that exist in the dataset
    available_core_columns = [col for col in core_columns if col in df_clean.columns]
    print(f"Core columns available: {len(available_core_columns)}")
    
    # Start with core columns and add any other important ones
    df_core = df_clean[available_core_columns].copy()
    
    # Clean HTML tags from text columns
    html_columns = [
        'attributes.Recipe description',
        'attributes.Description'
    ]
    
    for col in html_columns:
        if col in df_core.columns:
            print(f"Cleaning HTML tags from {col}...")
            df_core[col] = df_core[col].apply(strip_html_tags)
    
    # Process semicolon-separated columns
    print("Processing semicolon-separated values...")
    
    # Colors processing
    if 'Colors (by semicolon)' in df_core.columns:
        print("Processing colors...")
        # Get unique colors
        unique_colors = split_semicolon_values(df_core['Colors (by semicolon)'], to_lowercase=True)
        print(f"Found {len(unique_colors)} unique colors")
        
        # Create color categories
        color_categories = create_color_categories()
        
        # Add normalized colors column
        df_core['colors_list'] = df_core['Colors (by semicolon)'].apply(
            lambda x: [c.strip().lower() for c in str(x).split(';')] if pd.notna(x) else []
        )
        
        # Add color categories column
        df_core['color_categories'] = df_core['colors_list'].apply(
            lambda x: categorize_colors(x, color_categories)
        )
        
        # Save color mapping for reference
        color_mapping = {
            'unique_colors': unique_colors,
            'color_categories': color_categories
        }
        with open('data/color_mapping.json', 'w') as f:
            json.dump(color_mapping, f, indent=2)
    
    # Holiday occasions processing
    if 'attributes.Holiday Occasion' in df_core.columns:
        print("Processing holiday occasions...")
        unique_occasions = split_semicolon_values(df_core['attributes.Holiday Occasion'], to_lowercase=True)
        print(f"Found {len(unique_occasions)} unique occasions")
        
        df_core['holiday_occasions_list'] = df_core['attributes.Holiday Occasion'].apply(
            lambda x: [c.strip().lower() for c in str(x).split(';')] if pd.notna(x) else []
        )
        
        # Save occasions for reference
        with open('data/holiday_occasions.json', 'w') as f:
            json.dump(unique_occasions, f, indent=2)
    
    # DIY Level processing (normalize to lowercase for filtering)
    if 'attributes.DIY Level' in df_core.columns:
        df_core['diy_level_normalized'] = df_core['attributes.DIY Level'].str.lower().str.strip()
    
    # Seasonality processing
    if 'Seasonality (by semicolon)' in df_core.columns:
        print("Processing seasonality data...")
        df_core['seasonality_parsed'] = df_core['Seasonality (by semicolon)'].apply(parse_seasonality_dates)
    
    # Group processing (normalize for filtering)
    if 'Group' in df_core.columns:
        df_core['group_normalized'] = df_core['Group'].str.lower().str.strip()
    
    # Product Type processing
    if 'attributes.Product Type - All Flowers' in df_core.columns:
        unique_product_types = split_semicolon_values(df_core['attributes.Product Type - All Flowers'], to_lowercase=True)
        print(f"Found {len(unique_product_types)} unique product types")
        
        df_core['product_types_list'] = df_core['attributes.Product Type - All Flowers'].apply(
            lambda x: [c.strip().lower() for c in str(x).split(';')] if pd.notna(x) else []
        )
        
        with open('data/product_types.json', 'w') as f:
            json.dump(unique_product_types, f, indent=2)
    
    # Create price categories for easier filtering
    if 'Variant price' in df_core.columns:
        df_core['price_category'] = pd.cut(
            df_core['Variant price'],
            bins=[0, 50, 100, 200, 500, 1000, float('inf')],
            labels=['under_50', '50_100', '100_200', '200_500', '500_1000', 'over_1000']
        )
    
    # Add derived columns for chatbot filtering
    # Create searchable text column
    text_columns = ['Product name', 'attributes.Description', 'attributes.Recipe description']
    existing_text_columns = [col for col in text_columns if col in df_core.columns]
    
    if existing_text_columns:
        df_core['searchable_text'] = df_core[existing_text_columns].fillna('').agg(' '.join, axis=1)
        df_core['searchable_text'] = df_core['searchable_text'].str.lower()
    
    # Remove rows with missing critical data
    critical_columns = ['Product ID', 'Product name', 'Variant price']
    existing_critical = [col for col in critical_columns if col in df_core.columns]
    
    initial_rows = len(df_core)
    df_core = df_core.dropna(subset=existing_critical)
    final_rows = len(df_core)
    print(f"Removed {initial_rows - final_rows} rows with missing critical data")
    
    # Save cleaned data
    df_core.to_csv(OUTPUT_PATH, index=False)
    print(f"Cleaned data saved to {OUTPUT_PATH}")
    print(f"Final dataset: {len(df_core)} rows, {len(df_core.columns)} columns")
    
    # Generate summary report
    create_cleaning_summary(df_core, unique_colors if 'Colors (by semicolon)' in df_core.columns else [],
                          unique_occasions if 'attributes.Holiday Occasion' in df_core.columns else [])
    
    return df_core

def create_cleaning_summary(df, unique_colors, unique_occasions):
    """Create a summary report of the cleaning process"""
    summary = []
    summary.append("DATA CLEANING SUMMARY REPORT")
    summary.append("=" * 50)
    
    summary.append(f"Final dataset size: {len(df)} rows, {len(df.columns)} columns")
    summary.append("")
    
    summary.append("KEY VARIABLES FOR CHATBOT:")
    summary.append("-" * 30)
    
    # Budget (Price)
    if 'Variant price' in df.columns:
        price_stats = df['Variant price'].describe()
        summary.append(f"BUDGET (Variant price):")
        summary.append(f"  - Available for {df['Variant price'].count()} products ({df['Variant price'].count()/len(df)*100:.1f}%)")
        summary.append(f"  - Price range: ${price_stats['min']:.2f} - ${price_stats['max']:.2f}")
        summary.append(f"  - Average price: ${price_stats['mean']:.2f}")
        summary.append("")
    
    # Event Type (Holiday Occasions)
    if unique_occasions:
        summary.append(f"EVENT TYPE (Holiday Occasions): {len(unique_occasions)} unique occasions")
        summary.append(f"  - Sample occasions: {', '.join(unique_occasions[:8])}")
        if len(unique_occasions) > 8:
            summary.append(f"  - And {len(unique_occasions) - 8} more...")
        summary.append("")
    
    # Colors
    if unique_colors:
        summary.append(f"COLORS: {len(unique_colors)} unique colors")
        summary.append(f"  - Sample colors: {', '.join(unique_colors[:10])}")
        if len(unique_colors) > 10:
            summary.append(f"  - And {len(unique_colors) - 10} more...")
        summary.append("")
    
    # DIY Level (Effort)
    if 'attributes.DIY Level' in df.columns:
        diy_counts = df['attributes.DIY Level'].value_counts()
        summary.append("EFFORT LEVEL (DIY Level):")
        for level, count in diy_counts.items():
            summary.append(f"  - {level}: {count} products ({count/len(df)*100:.1f}%)")
        summary.append("")
    
    # Product Groups
    if 'Group' in df.columns:
        group_counts = df['Group'].value_counts().head(10)
        summary.append("TOP PRODUCT GROUPS:")
        for group, count in group_counts.items():
            summary.append(f"  - {group}: {count} products")
        summary.append("")
    
    summary.append("FILES CREATED:")
    summary.append("-" * 20)
    summary.append("- cleaned_flower_data.csv: Main cleaned dataset")
    summary.append("- color_mapping.json: Color categories and mappings")
    summary.append("- holiday_occasions.json: List of all occasions")
    summary.append("- product_types.json: List of all product types")
    
    # Write summary to file
    with open('data/cleaning_summary.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(summary))
    
    print("Cleaning summary saved to data/cleaning_summary.txt")

def main():
    """Main execution function"""
    # Create data directory if it doesn't exist
    import os
    os.makedirs('data', exist_ok=True)
    
    try:
        cleaned_df = clean_data()
        print("\nData cleaning completed successfully!")
        print("\nIntended use:")
        print("1. Review the cleaning_summary.txt for an overview")
        print("2. Check the JSON files for color and occasion mappings")
        print("3. Use cleaned_flower_data.csv for your chatbot database")
        
    except Exception as e:
        print(f"Error during data cleaning: {e}")
        raise

if __name__ == "__main__":
    main()