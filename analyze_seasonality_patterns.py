import pandas as pd
import numpy as np
from collections import Counter

def analyze_seasonality_patterns():
    """Analyze seasonality patterns in the Excel data to understand range complexity"""
    
    # Load the data
    FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
    
    try:
        df = pd.read_excel(FILE_PATH)
        print(f"Loaded data: {len(df)} rows, {len(df.columns)} columns")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    
    # Check if seasonality column exists
    seasonality_col = 'Seasonality (by semicolon)'
    if seasonality_col not in df.columns:
        print(f"Column '{seasonality_col}' not found!")
        print("Available columns containing 'season':")
        season_cols = [col for col in df.columns if 'season' in col.lower()]
        print(season_cols)
        return
    
    print(f"\nAnalyzing '{seasonality_col}' column...")
    
    # Get non-null seasonality values
    seasonality_data = df[seasonality_col].dropna()
    print(f"Total non-null seasonality entries: {len(seasonality_data)}")
    
    # Count unique patterns
    unique_patterns = seasonality_data.unique()
    print(f"Unique seasonality patterns: {len(unique_patterns)}")
    
    # Analyze range counts
    range_counts = {}
    patterns_by_range_count = {}
    
    for pattern in unique_patterns:
        pattern_str = str(pattern).strip()
        
        if pattern_str.upper() == 'YR':
            range_count = 0  # Year-round
            range_counts[0] = range_counts.get(0, 0) + 1
            if 0 not in patterns_by_range_count:
                patterns_by_range_count[0] = []
            patterns_by_range_count[0].append(pattern_str)
        else:
            # Count semicolon-separated ranges
            ranges = [r.strip() for r in pattern_str.split(';') if r.strip()]
            range_count = len(ranges)
            range_counts[range_count] = range_counts.get(range_count, 0) + 1
            
            if range_count not in patterns_by_range_count:
                patterns_by_range_count[range_count] = []
            patterns_by_range_count[range_count].append(pattern_str)
    
    # Print range count analysis
    print(f"\nRange Count Analysis:")
    print("-" * 40)
    for count in sorted(range_counts.keys()):
        num_patterns = range_counts[count]
        if count == 0:
            print(f"Year-round (YR): {num_patterns} patterns")
        else:
            print(f"{count} range{'s' if count != 1 else ''}: {num_patterns} patterns")
    
    # Show examples for each range count
    print(f"\nExample Patterns by Range Count:")
    print("-" * 50)
    
    for count in sorted(patterns_by_range_count.keys()):
        patterns = patterns_by_range_count[count]
        print(f"\n{count} Range{'s' if count != 1 else ''} ({len(patterns)} unique patterns):")
        
        # Show first 5 examples
        examples = patterns[:5]
        for i, pattern in enumerate(examples, 1):
            print(f"  {i}. '{pattern}'")
        
        if len(patterns) > 5:
            print(f"  ... and {len(patterns) - 5} more")
    
    # Check for the longest patterns
    max_ranges = max(range_counts.keys())
    print(f"\nMaximum number of ranges found: {max_ranges}")
    
    if max_ranges > 2:
        print(f"\nProducts with {max_ranges} ranges:")
        long_patterns = patterns_by_range_count[max_ranges]
        for pattern in long_patterns:
            print(f"  '{pattern}'")
    
    # Count actual product occurrences (not just unique patterns)
    print(f"\nActual Product Distribution:")
    print("-" * 35)
    
    product_range_counts = {}
    for pattern in seasonality_data:
        pattern_str = str(pattern).strip()
        
        if pattern_str.upper() == 'YR':
            range_count = 0
        else:
            ranges = [r.strip() for r in pattern_str.split(';') if r.strip()]
            range_count = len(ranges)
        
        product_range_counts[range_count] = product_range_counts.get(range_count, 0) + 1
    
    total_products = sum(product_range_counts.values())
    for count in sorted(product_range_counts.keys()):
        num_products = product_range_counts[count]
        percentage = (num_products / total_products) * 100
        if count == 0:
            print(f"Year-round (YR): {num_products} products ({percentage:.1f}%)")
        else:
            print(f"{count} range{'s' if count != 1 else ''}: {num_products} products ({percentage:.1f}%)")
    
    # Recommendation
    print(f"\nRECOMMENDATION:")
    print("-" * 20)
    
    if max_ranges <= 2:
        print("✓ Current 2-range database design is sufficient")
        print("  All seasonality patterns can be captured")
    elif max_ranges == 3:
        multi_range_products = product_range_counts.get(3, 0)
        multi_range_pct = (multi_range_products / total_products) * 100
        print(f"⚠ {multi_range_products} products ({multi_range_pct:.1f}%) have 3 ranges")
        print("  Consider adding a 3rd range to the database schema")
        print("  OR accept that these products will have incomplete seasonality data")
    else:
        print(f"⚠ Found patterns with up to {max_ranges} ranges")
        print("  This is quite complex - consider alternative approaches")
    
    print(f"\nData saved to: data/seasonality_analysis.txt")
    
    # Save detailed analysis to file
    with open('data/seasonality_analysis.txt', 'w') as f:
        f.write("SEASONALITY PATTERN ANALYSIS\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Total products with seasonality: {len(seasonality_data)}\n")
        f.write(f"Unique patterns: {len(unique_patterns)}\n")
        f.write(f"Maximum ranges in a single product: {max_ranges}\n\n")
        
        f.write("RANGE COUNT DISTRIBUTION:\n")
        f.write("-" * 25 + "\n")
        for count in sorted(product_range_counts.keys()):
            num_products = product_range_counts[count]
            percentage = (num_products / total_products) * 100
            if count == 0:
                f.write(f"Year-round (YR): {num_products} products ({percentage:.1f}%)\n")
            else:
                f.write(f"{count} ranges: {num_products} products ({percentage:.1f}%)\n")
        
        f.write("\nALL UNIQUE PATTERNS:\n")
        f.write("-" * 20 + "\n")
        for count in sorted(patterns_by_range_count.keys()):
            patterns = patterns_by_range_count[count]
            f.write(f"\n{count} Range{'s' if count != 1 else ''}: {len(patterns)} patterns\n")
            for pattern in patterns:
                f.write(f"  '{pattern}'\n")

def main():
    """Main execution function"""
    try:
        analyze_seasonality_patterns()
        print(f"\nAnalysis complete!")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()