import pandas as pd
import json
import io

# -------- CONFIG --------
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"
OUTPUT_FILE = "eda_report.txt"
RAW_VALUES_FILE = "raw_values.json"
CANONICAL_FILE = "canonical_dict.json"
ALL_MISSING_FILE = "all_missing_values.csv"
DROPPED_COLS_FILE = "dropped_columns.csv"
# Derived JSONs
COLORS_FILE = "colors.json"
SEASONS_FILE = "seasons.json"
WEEKDAYS_FILE = "weekdays.json"
# ------------------------

def split_values(series):
    """Split semicolon-separated values into a flat set."""
    values = set()
    for item in series.dropna():
        for v in str(item).split(";"):
            v = v.strip().lower()
            if v:
                values.add(v)
    return sorted(values)

def normalize_values(raw_values, mapping):
    """Map raw values into canonical groups, return (categorized, uncategorized)."""
    categorized = {k: [] for k in mapping.keys()}
    uncategorized = []

    for val in raw_values:
        found = False
        for category, aliases in mapping.items():
            if val in aliases:
                categorized[category].append(val)
                found = True
                break
        if not found:
            uncategorized.append(val)

    return categorized, uncategorized

def main():
    # Load Excel
    df = pd.read_excel(FILE_PATH)
    
    report_lines = []
    report_lines.append("=== BASIC INFO ===\n")

    # ✅ Save basic info
    buffer = io.StringIO()
    df.info(buf=buffer)
    report_lines.append(buffer.getvalue() + "\n")

    # === Missing values ===
    report_lines.append("\n=== MISSING VALUES (Top 20) ===\n")
    missing = df.isnull().sum().sort_values(ascending=False)
    missing_percent = (df.isnull().mean() * 100).sort_values(ascending=False)
    missing_summary = pd.DataFrame({
        "Missing Count": missing,
        "Missing %": missing_percent
    })

    # Save all missing values
    missing_summary.to_csv(ALL_MISSING_FILE, index=True)

    # Save dropped columns (≥99% missing)
    threshold = 99.0
    dropped = missing_summary[missing_summary["Missing %"] >= threshold]
    if not dropped.empty:
        dropped.to_csv(DROPPED_COLS_FILE, index=True)
    else:
        with open(DROPPED_COLS_FILE, "w") as f:
            f.write("No columns dropped (none ≥99% missing).\n")

    # Keep report concise (top 20 only)
    report_lines.append(str(missing_summary.head(20)) + "\n")

    # === Unique counts ===
    report_lines.append("\n=== UNIQUE VALUE COUNTS (Top 20) ===\n")
    unique_counts = df.nunique().sort_values(ascending=False)
    report_lines.append(str(unique_counts.head(20)) + "\n")

    # === Active vs Inactive ===
    if "Active" in df.columns:
        report_lines.append("\n=== ACTIVE VS INACTIVE PRODUCTS ===\n")
        report_lines.append(str(df["Active"].value_counts()) + "\n")

    # --- Extract raw values for chatbot-related columns ---
    columns_of_interest = ["Colors", "Seasonality", "Weekdays", "Tags", "Group", "Subgroup"]
    raw_values = {}
    for col in columns_of_interest:
        if col in df.columns:
            raw_values[col] = split_values(df[col])

    with open(RAW_VALUES_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_values, f, indent=2)

    # --- Define canonical mappings (starter dictionary) ---
    canonical_dict = {
        "colors": {
            "white": ["white", "ivory", "cream"],
            "pink": ["pink", "light pink", "hot pink", "blush"],
            "red": ["red", "burgundy", "maroon"],
            "orange": ["orange", "peach", "coral"],
            "yellow": ["yellow", "gold"],
            "green": ["green", "lime", "olive"],
            "blue": ["blue", "navy", "light blue"],
            "purple": ["purple", "lavender", "violet"],
            "multicolor": ["assorted", "mixed", "rainbow"]
        },
        "seasons": {
            "spring": ["spring"],
            "summer": ["summer"],
            "fall": ["fall", "autumn"],
            "winter": ["winter"],
            "all": ["all seasons", "year-round"]
        },
        "weekdays": {
            "monday": ["mon", "monday"],
            "tuesday": ["tue", "tuesday"],
            "wednesday": ["wed", "wednesday"],
            "thursday": ["thu", "thursday"],
            "friday": ["fri", "friday"],
            "saturday": ["sat", "saturday"],
            "sunday": ["sun", "sunday"]
        }
    }

    with open(CANONICAL_FILE, "w", encoding="utf-8") as f:
        json.dump(canonical_dict, f, indent=2)

    # --- Normalize values into dedicated JSONs ---
    if "Colors" in raw_values:
        colors_categorized, colors_uncat = normalize_values(raw_values["Colors"], canonical_dict["colors"])
        with open(COLORS_FILE, "w", encoding="utf-8") as f:
            json.dump(colors_categorized, f, indent=2)
        if colors_uncat:
            print("⚠️ Unassigned colors:", colors_uncat)

    if "Seasonality" in raw_values:
        seasons_categorized, seasons_uncat = normalize_values(raw_values["Seasonality"], canonical_dict["seasons"])
        with open(SEASONS_FILE, "w", encoding="utf-8") as f:
            json.dump(seasons_categorized, f, indent=2)
        if seasons_uncat:
            print("⚠️ Unassigned seasons:", seasons_uncat)

    if "Weekdays" in raw_values:
        weekdays_categorized, weekdays_uncat = normalize_values(raw_values["Weekdays"], canonical_dict["weekdays"])
        with open(WEEKDAYS_FILE, "w", encoding="utf-8") as f:
            json.dump(weekdays_categorized, f, indent=2)
        if weekdays_uncat:
            print("⚠️ Unassigned weekdays:", weekdays_uncat)

    # --- Add chatbot raw values summary ---
    report_lines.append("\n=== CHATBOT RAW VALUES SUMMARY ===\n")
    for col, values in raw_values.items():
        report_lines.append(f"\n-- {col} ({len(values)} unique after split) --\n")
        report_lines.append(", ".join(values[:30]) + ("..." if len(values) > 30 else "") + "\n")

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    print(f"EDA report saved to {OUTPUT_FILE}")
    print(f"Raw chatbot values saved to {RAW_VALUES_FILE}")
    print(f"Canonical dictionary saved to {CANONICAL_FILE}")
    print(f"Colors normalized saved to {COLORS_FILE}")
    print(f"Seasons normalized saved to {SEASONS_FILE}")
    print(f"Weekdays normalized saved to {WEEKDAYS_FILE}")
    print(f"Full missing values saved to {ALL_MISSING_FILE}")
    print(f"Dropped columns saved to {DROPPED_COLS_FILE}")

if __name__ == "__main__":
    main()
