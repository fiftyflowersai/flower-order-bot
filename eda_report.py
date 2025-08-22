import pandas as pd

# -------- CONFIG --------
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
OUTPUT_FILE = "eda_report.txt"
# ------------------------

def main():
    # Load Excel
    df = pd.read_excel(FILE_PATH)
    
    report_lines = []
    report_lines.append("=== BASIC INFO ===\n")
    report_lines.append(f"Shape (rows, cols): {df.shape}\n")
    report_lines.append(str(df.info(buf=None)) + "\n")

    # Missing values
    report_lines.append("\n=== MISSING VALUES (Top 20) ===\n")
    missing = df.isnull().sum().sort_values(ascending=False)
    missing_percent = (df.isnull().mean() * 100).sort_values(ascending=False)
    missing_summary = pd.DataFrame({
        "Missing Count": missing,
        "Missing %": missing_percent
    })
    report_lines.append(str(missing_summary.head(20)) + "\n")

    # Unique counts
    report_lines.append("\n=== UNIQUE VALUE COUNTS (Top 20) ===\n")
    unique_counts = df.nunique().sort_values(ascending=False)
    report_lines.append(str(unique_counts.head(20)) + "\n")

    # Describe numeric
    report_lines.append("\n=== NUMERIC SUMMARY ===\n")
    report_lines.append(str(df.describe(include=[float, int])) + "\n")

    # Describe categorical
    report_lines.append("\n=== CATEGORICAL SUMMARY (Top 20 cols) ===\n")
    cat_cols = df.select_dtypes(include=["object"]).columns
    for col in cat_cols[:20]:
        report_lines.append(f"\n-- {col} --\n")
        report_lines.append(str(df[col].value_counts().head(10)) + "\n")

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    print(f"EDA report saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
