import pandas as pd
import numpy as np
from collections import Counter
import re

# File path
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"

def load_data():
    """Load the Excel data"""
    try:
        df = pd.read_excel(FILE_PATH)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def analyze_data_size(df):
    """Analyze basic data dimensions"""
    report = []
    report.append("="*50)
    report.append("DATA SIZE ANALYSIS")
    report.append("="*50)
    report.append(f"Total rows: {len(df)}")
    report.append(f"Total columns: {len(df.columns)}")
    report.append(f"Data shape: {df.shape}")
    report.append("\n")
    return report

def create_missing_values_report(df):
    """Create missing values CSV and return summary for report"""
    missing_data = []
    report = []
    
    for column in df.columns:
        missing_count = df[column].isnull().sum()
        missing_percent = (missing_count / len(df)) * 100
        missing_data.append({
            'Column': column,
            'Missing Count': missing_count,
            'Missing %': missing_percent
        })
    
    # Create DataFrame and save to CSV
    missing_df = pd.DataFrame(missing_data)
    missing_df = missing_df.sort_values('Missing %', ascending=False)
    missing_df.to_csv('all_missing_values.csv', index=False)
    
    report.append("="*50)
    report.append("MISSING VALUES ANALYSIS")
    report.append("="*50)
    report.append("Missing values report saved to 'all_missing_values.csv'")
    report.append("\nTop 10 columns with most missing values:")
    for i, row in missing_df.head(10).iterrows():
        report.append(f"{row['Column']}: {row['Missing Count']} ({row['Missing %']:.2f}%)")
    report.append("\n")
    
    return report

def get_unique_sample_values(series, max_samples=10):
    """Get unique sample values from a series, avoiding repetition"""
    # Remove null values
    non_null_values = series.dropna()
    
    if len(non_null_values) == 0:
        return ["No non-null values"]
    
    unique_values = non_null_values.unique()
    
    # If we have fewer unique values than max_samples, return all
    if len(unique_values) <= max_samples:
        return unique_values.tolist()
    
    # Otherwise, return a sample of unique values
    return unique_values[:max_samples].tolist()

def analyze_columns_of_interest(df):
    """Analyze the columns we're most interested in"""
    columns_of_interest = [
        'Product name', 'Group', 'Variant price', 'Seasonality (by semicolon)', 
        'Colors (by semicolon)', 'attributes.Recipe description', 'attributes.DIY Level', 
        'attributes.Holiday Occasion', 'attributes.Description'
    ]
    
    report = []
    report.append("="*50)
    report.append("COLUMNS OF INTEREST ANALYSIS")
    report.append("="*50)
    
    available_columns = [col for col in columns_of_interest if col in df.columns]
    missing_columns = [col for col in columns_of_interest if col not in df.columns]
    
    if missing_columns:
        report.append(f"WARNING: These columns are not found in the dataset: {missing_columns}")
        report.append("")
    
    for column in available_columns:
        report.append(f"Column: {column}")
        report.append("-" * (len(column) + 8))
        
        # Basic stats
        total_values = len(df[column])
        non_null_count = df[column].count()
        null_count = df[column].isnull().sum()
        null_percentage = (null_count / total_values) * 100
        
        report.append(f"Total values: {total_values}")
        report.append(f"Non-null values: {non_null_count}")
        report.append(f"Null values: {null_count} ({null_percentage:.2f}%)")
        
        if non_null_count > 0:
            # Get sample values
            sample_values = get_unique_sample_values(df[column])
            report.append(f"Sample unique values ({len(sample_values)} shown):")
            for i, value in enumerate(sample_values, 1):
                # Truncate very long values for readability
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                report.append(f"  {i}. {value_str}")
        
        report.append("")
    
    return report

def analyze_all_columns(df):
    """Get overview of all columns"""
    report = []
    report.append("="*50)
    report.append("ALL COLUMNS OVERVIEW")
    report.append("="*50)
    
    for column in df.columns:
        non_null_count = df[column].count()
        data_type = str(df[column].dtype)
        unique_count = df[column].nunique()
        
        report.append(f"{column}:")
        report.append(f"  Data type: {data_type}")
        report.append(f"  Non-null count: {non_null_count}")
        report.append(f"  Unique values: {unique_count}")
        report.append("")
    
    return report

def count_unique_values_basic(df):
    """Count unique values for each column"""
    report = []
    report.append("="*50)
    report.append("UNIQUE VALUES COUNT (BASIC)")
    report.append("="*50)
    
    unique_counts = []
    for column in df.columns:
        unique_count = df[column].nunique()
        unique_counts.append({'Column': column, 'Unique_Count': unique_count})
    
    unique_df = pd.DataFrame(unique_counts).sort_values('Unique_Count', ascending=False)
    
    report.append("Top columns by unique value count:")
    for i, row in unique_df.head(15).iterrows():
        report.append(f"{row['Column']}: {row['Unique_Count']} unique values")
    
    report.append("\nColumns with very few unique values (potential categories):")
    for i, row in unique_df.tail(10).iterrows():
        if row['Unique_Count'] > 0:  # Skip completely empty columns
            report.append(f"{row['Column']}: {row['Unique_Count']} unique values")
    
    report.append("")
    return report

def analyze_semicolon_separated_columns(df):
    """Analyze columns that contain semicolon-separated values"""
    semicolon_columns = []
    
    # Find columns that likely contain semicolon-separated values
    for column in df.columns:
        if df[column].dtype == 'object':
            # Check if any non-null values contain semicolons
            sample_with_semicolons = df[column].dropna().astype(str).str.contains(';').any()
            if sample_with_semicolons:
                semicolon_columns.append(column)
    
    if not semicolon_columns:
        return ["No columns with semicolon-separated values found.\n"]
    
    report = []
    report.append("="*50)
    report.append("SEMICOLON-SEPARATED VALUES ANALYSIS")
    report.append("="*50)
    
    for column in semicolon_columns:
        report.append(f"Column: {column}")
        report.append("-" * (len(column) + 8))
        
        # Get all values and split by semicolon
        all_values = df[column].dropna().astype(str)
        split_values = []
        
        for value in all_values:
            if ';' in value:
                split_values.extend([v.strip() for v in value.split(';') if v.strip()])
            else:
                split_values.append(value.strip())
        
        unique_split_values = list(set(split_values))
        basic_unique_count = df[column].nunique()
        
        report.append(f"Basic unique count: {basic_unique_count}")
        report.append(f"Unique values after splitting by semicolon: {len(unique_split_values)}")
        
        # Show sample of unique split values
        sample_split = unique_split_values[:15] if len(unique_split_values) > 15 else unique_split_values
        report.append(f"Sample unique split values ({len(sample_split)} shown):")
        for i, value in enumerate(sample_split, 1):
            report.append(f"  {i}. {value}")
        
        report.append("")
    
    return report

def detect_html_tags(df):
    """Detect columns that might contain HTML tags"""
    report = []
    html_columns = []
    
    for column in df.columns:
        if df[column].dtype == 'object':
            # Check for HTML tags in non-null values
            sample_values = df[column].dropna().astype(str)
            has_html = sample_values.str.contains(r'<[^>]+>', regex=True).any()
            
            if has_html:
                html_columns.append(column)
                # Count how many entries have HTML tags
                html_count = sample_values.str.contains(r'<[^>]+>', regex=True).sum()
                html_percentage = (html_count / len(sample_values)) * 100
                
                # Get sample of values with HTML tags
                html_samples = sample_values[sample_values.str.contains(r'<[^>]+>', regex=True)].head(3).tolist()
                
                report.append(f"Column '{column}' contains HTML tags:")
                report.append(f"  {html_count} entries ({html_percentage:.2f}%) contain HTML tags")
                report.append("  Sample values with HTML:")
                for i, sample in enumerate(html_samples, 1):
                    sample_truncated = sample[:150] + "..." if len(sample) > 150 else sample
                    report.append(f"    {i}. {sample_truncated}")
                report.append("")
    
    if html_columns:
        report.insert(0, "="*50)
        report.insert(1, "HTML TAGS DETECTION")
        report.insert(2, "="*50)
        report.append("")
    else:
        report = ["No HTML tags detected in any columns.\n"]
    
    return report

def main():
    """Main function to run the EDA report"""
    print("Starting EDA report generation...")
    
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Initialize report
    full_report = []
    full_report.append("FLOWER PRODUCT DATA - EDA REPORT")
    full_report.append("")
    
    # Run all analyses
    full_report.extend(analyze_data_size(df))
    full_report.extend(create_missing_values_report(df))
    full_report.extend(analyze_columns_of_interest(df))
    full_report.extend(count_unique_values_basic(df))
    full_report.extend(analyze_semicolon_separated_columns(df))
    full_report.extend(detect_html_tags(df))
    full_report.extend(analyze_all_columns(df))
    
    # Write report to file
    with open('eda_report.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(full_report))
    
    print("EDA report completed!")
    print("Files generated:")
    print("- eda_report.txt: Main EDA report")
    print("- all_missing_values.csv: Detailed missing values analysis")

if __name__ == "__main__":
    main()