#!/usr/bin/env python3
import pandas as pd
import json
import io
from collections import Counter, defaultdict
import difflib
from typing import Dict, List, Set, Tuple

# -------- CONFIG --------
FILE_PATH = "data/BloombrainCatalogwithprices.xlsx"

REPORT_FILE = "eda_report.md"
RAW_VALUES_FILE = "raw_values.json"

# Canonical outputs (separate files as requested)
COLORS_FILE = "colors.json"
WEEKDAYS_FILE = "weekdays.json"

# Back-compat combined dictionary (optional to keep)
CANONICAL_COMBINED_FILE = "canonical_dict.json"
# ------------------------

SEMI_HINT = "(by semicolon)"

# ---------- Helpers ----------
def split_semicolon_values(series: pd.Series) -> List[str]:
    """Return a sorted list of unique tokens from a semicolon-separated column."""
    values: Set[str] = set()
    for item in series.dropna():
        for v in str(item).split(";"):
            v = v.strip().lower()
            if v:
                values.add(v)
    return sorted(values)

def counts_semicolon_values(series: pd.Series, top_n: int = 20) -> List[Tuple[str, int]]:
    """Return top N value counts from a semicolon-separated column."""
    counter: Counter = Counter()
    for item in series.dropna():
        tokens = [t.strip().lower() for t in str(item).split(";") if t.strip()]
        counter.update(tokens)
    return counter.most_common(top_n)

def get_df_info(df: pd.DataFrame) -> str:
    buf = io.StringIO()
    df.info(buf=buf)
    return buf.getvalue()

def detect_semicolon_cols(df: pd.DataFrame) -> Dict[str, str]:
    """
    Finds columns that contain '(by semicolon)' and returns a canonical name -> actual column mapping.
    E.g. 'colors' -> 'Colors (by semicolon)'
    """
    mapping = {}
    for col in df.columns:
        if SEMI_HINT in col:
            base = col.replace(SEMI_HINT, "").strip().lower()
            mapping[base] = col
    return mapping

def normalize_weekday(token: str) -> str:
    t = token.strip().lower()
    mapping = {
        "mon": "mon", "monday": "mon",
        "tue": "tue", "tues": "tue", "tuesday": "tue",
        "wed": "wed", "weds": "wed", "wednesday": "wed",
        "thu": "thu", "thur": "thu", "thurs": "thu", "thursday": "thu",
        "fri": "fri", "friday": "fri",
        "sat": "sat", "saturday": "sat",
        "sun": "sun", "sunday": "sun",
    }
    return mapping.get(t, t)

def build_weekdays_canonical(raw_tokens: List[str]) -> Dict[str, List[str]]:
    """
    Build a canonical weekday dictionary from raw tokens found in the dataset.
    Result maps canonical keys ('mon', 'tue', ...) to a list of synonyms seen.
    """
    buckets = defaultdict(set)
    for token in raw_tokens:
        norm = normalize_weekday(token)
        if norm in {"mon","tue","wed","thu","fri","sat","sun"}:
            buckets[norm].add(token)
        else:
            # Non-standard (should be rare; keep under 'misc')
            buckets["misc"].add(token)
    # Convert to sorted lists
    return {k: sorted(list(v)) for k, v in buckets.items()}

def auto_expand_color_buckets(raw_colors: List[str], seed_buckets: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Expand color buckets from seed synonyms + raw tokens in the data using simple heuristics/fuzzy matching.
    Returns {bucket: [tokens_from_dataset_mapped_here]}
    """
    # Prepare lowercase seeds
    seeds = {bucket: [s.lower() for s in syns] for bucket, syns in seed_buckets.items()}
    all_seed_terms = sorted({s for syns in seeds.values() for s in syns})

    # Initialize buckets
    assignments: Dict[str, Set[str]] = {b: set() for b in seeds.keys()}
    assignments["_unassigned"] = set()

    # Heuristics
    def belongs(token: str, bucket: str) -> bool:
        token_l = token.lower()
        # Substring rule
        for s in seeds[bucket]:
            if s in token_l or token_l in s:
                return True
        # Catch common light/dark variants
        if bucket == "pink" and ("fuchsia" in token_l or "blush" in token_l or "magenta" in token_l):
            return True
        if bucket == "red" and ("burgundy" in token_l or "wine" in token_l or "maroon" in token_l):
            return True
        if bucket == "green" and ("sage" in token_l or "mint" in token_l or "forest" in token_l or "chartreuse" in token_l):
            return True
        if bucket == "purple" and ("lavender" in token_l or "violet" in token_l or "lilac" in token_l):
            return True
        if bucket == "orange" and ("peach" in token_l or "coral" in token_l or "apricot" in token_l):
            return True
        if bucket == "white" and ("ivory" in token_l or "cream" in token_l):
            return True
        if bucket == "yellow" and ("gold" in token_l or "butter" in token_l):
            return True
        if bucket == "blue" and ("navy" in token_l or "sky" in token_l):
            return True
        if bucket == "multicolor" and any(w in token_l for w in ["mixed","assorted","rainbow","farm mix","farm mixes"]):
            return True
        return False

    for token in raw_colors:
        # Exact seed match -> bucket
        placed = False
        for bucket in seeds:
            if token in seeds[bucket]:
                assignments[bucket].add(token)
                placed = True
                break
        if placed:
            continue

        # Heuristic substring + known patterns
        for bucket in seeds:
            if belongs(token, bucket):
                assignments[bucket].add(token)
                placed = True
                break
        if placed:
            continue

        # Fuzzy match against any seed term
        close = difflib.get_close_matches(token, all_seed_terms, n=1, cutoff=0.9)
        if close:
            # find the bucket containing that seed term
            seed_match = close[0]
            for bucket, syns in seeds.items():
                if seed_match in syns:
                    assignments[bucket].add(token)
                    placed = True
                    break

        if not placed:
            assignments["_unassigned"].add(token)

    # Return sorted lists
    return {k: sorted(list(v)) for k, v in assignments.items()}

def write_report(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ---------- Main ----------
def main():
    df = pd.read_excel(FILE_PATH)

    # Basic info
    info_text = get_df_info(df)
    shape = df.shape

    # Missing summary
    missing = df.isnull().sum().sort_values(ascending=False)
    missing_percent = (df.isnull().mean() * 100).sort_values(ascending=False)
    missing_summary = pd.DataFrame({"Missing Count": missing, "Missing %": missing_percent})

    # Unique counts
    unique_counts = df.nunique().sort_values(ascending=False)

    # Detect semicolon columns
    semi_cols = detect_semicolon_cols(df)  # e.g., {'colors': 'Colors (by semicolon)', ...}

    # Pull raw unique tokens for chatbot-relevant fields
    raw_values = {}

    # Colors
    colors_key = "colors"
    if colors_key in semi_cols:
        colors_raw = split_semicolon_values(df[semi_cols[colors_key]])
        raw_values["colors"] = colors_raw
    else:
        raw_values["colors"] = []

    # Tags
    tags_key = "tags"
    if tags_key in semi_cols:
        tags_raw = split_semicolon_values(df[semi_cols[tags_key]])
        raw_values["tags"] = tags_raw
    else:
        raw_values["tags"] = []

    # Weekdays
    weekdays_key = "weekdays"
    if weekdays_key in semi_cols:
        weekdays_raw = split_semicolon_values(df[semi_cols[weekdays_key]])
        raw_values["weekdays"] = weekdays_raw
    else:
        raw_values["weekdays"] = []

    # Group / Subgroup (not semicolon in your dataset)
    raw_values["group"] = sorted(set(str(v).strip().lower() for v in df.get("Group", pd.Series(dtype=str)).dropna()))
    raw_values["subgroup"] = sorted(set(str(v).strip().lower() for v in df.get("Subgroup", pd.Series(dtype=str)).dropna()))

    # Save raw values for debugging / iteration
    save_json(RAW_VALUES_FILE, raw_values)

    # ----- Build canonical dictionaries -----

    # Seed color buckets (you can refine over time)
    color_seed = {
        "white": ["white", "ivory", "cream"],
        "pink": ["pink", "light pink", "hot pink", "blush", "rose pink"],
        "red": ["red", "burgundy", "maroon", "wine red"],
        "orange": ["orange", "peach", "coral", "apricot"],
        "yellow": ["yellow", "gold", "butter yellow"],
        "green": ["green", "sage green", "mint", "forest green", "chartreuse", "olive"],
        "blue": ["blue", "navy", "light blue", "sky blue"],
        "purple": ["purple", "lavender", "violet", "lilac"],
        "multicolor": ["mixed", "assorted", "rainbow", "farm mix", "farm mixes"]
    }

    # Expand buckets from real data
    colors_canonical = auto_expand_color_buckets(raw_values["colors"], color_seed)
    save_json(COLORS_FILE, colors_canonical)

    # Weekdays canonical map
    weekdays_canonical = build_weekdays_canonical(raw_values["weekdays"])
    save_json(WEEKDAYS_FILE, weekdays_canonical)

    # Combined (back-compat) file
    canonical_combined = {
        "colors": colors_canonical,
        "weekdays": weekdays_canonical
    }
    save_json(CANONICAL_COMBINED_FILE, canonical_combined)

    # ----- Build Markdown report -----
    # Selected top stats for readability
    top_missing = missing_summary.head(20)
    top_unique = unique_counts.head(20)

    # Semicolon column quick stats (if present)
    colors_top = counts_semicolon_values(df[semi_cols[colors_key]]) if colors_key in semi_cols else []
    tags_top = counts_semicolon_values(df[semi_cols[tags_key]]) if tags_key in semi_cols else []
    weekdays_top = counts_semicolon_values(df[semi_cols[weekdays_key]]) if weekdays_key in semi_cols else []

    def fmt_counter_rows(rows: List[Tuple[str, int]]) -> str:
        return "\n".join([f"- {k}: {v}" for k, v in rows])

    report = []
    report.append("# FiftyFlowers Chatbot – EDA & Preprocessing Report\n")
    report.append("## 1) Objective\n")
    report.append(
        "Prepare the product catalog for a website chatbot that helps customers discover, "
        "filter, and select products (e.g., by color, type, price, and delivery day). "
        "This report documents the dataset, preprocessing decisions, and canonical dictionaries "
        "the chatbot will use for reliable filtering and natural-language queries.\n"
    )

    report.append("## 2) Data Summary\n")
    report.append(f"- Source file: `{FILE_PATH}`\n")
    report.append(f"- Shape: **{shape[0]:,} rows × {shape[1]:,} columns**\n")
    report.append("\n<details>\n<summary>pandas DataFrame info</summary>\n\n")
    report.append("```\n" + info_text + "```\n")
    report.append("</details>\n")

    report.append("\n**Top Missing Columns (20)**\n\n")
    report.append("```\n" + str(top_missing) + "\n```\n")

    report.append("\n**Top Unique Count Columns (20)**\n\n")
    report.append("```\n" + str(top_unique) + "\n```\n")

    report.append("## 3) Preprocessing Decisions\n")
    report.append("- Drop columns with ≥99% missing values to reduce noise.\n")
    report.append("- Normalize semicolon-delimited fields into lists: **Colors**, **Tags**, **Weekdays**.\n")
    report.append("- Standardize strings (lowercase, trim) and normalize weekdays to `mon..sun`.\n")
    report.append("- Introduce **canonical dictionaries** for colors and weekdays to enable consistent filtering and synonym handling.\n")
    report.append("- Keep high-signal fields for chatbot retrieval (e.g., Product name, Group, Subgroup, Colors, Tags, Weekdays, prices, statuses).\n")

    report.append("## 4) Files Emitted\n")
    report.append(f"- `{RAW_VALUES_FILE}` – raw unique tokens extracted from dataset for: colors, tags, weekdays, group, subgroup.\n")
    report.append(f"- `{COLORS_FILE}` – canonical **color buckets expanded from real data** (+ `_unassigned` for review).\n")
    report.append(f"- `{WEEKDAYS_FILE}` – canonical weekday map (mon..sun → synonyms seen in data) + `misc` if any.\n")
    report.append(f"- `{CANONICAL_COMBINED_FILE}` – combined canonical file (back-compat).\n")

    report.append("## 5) Key Value Snapshots\n")
    if colors_top:
        report.append("**Top Colors (token frequency, semicolon-split)**\n")
        report.append(fmt_counter_rows(colors_top) + "\n")
    if tags_top:
        report.append("\n**Top Tags (token frequency, semicolon-split)**\n")
        report.append(fmt_counter_rows(tags_top) + "\n")
    if weekdays_top:
        report.append("\n**Weekdays Availability (token frequency, semicolon-split)**\n")
        report.append(fmt_counter_rows(weekdays_top) + "\n")

    report.append("\n## 6) Next Steps\n")
    report.append("- Review `colors.json` `_unassigned` bucket and either map or leave excluded from filters.\n")
    report.append("- Generate a **clean catalog export** (normalized columns, list fields JSON-encoded) for loading into SQL.\n")
    report.append("- Choose hosting for SQL (e.g., **Supabase Postgres** or **PlanetScale MySQL** for cost-effective scaling).\n")
    report.append("- Implement chatbot retrieval flow: parse intent → map synonyms via canonical JSONs → build SQL where-clause → return ranked products.\n")

    write_report(REPORT_FILE, "\n".join(report))

    # Console summary
    print(f"✓ EDA report saved to: {REPORT_FILE}")
    print(f"✓ Raw values saved to: {RAW_VALUES_FILE}")
    print(f"✓ Colors canonical saved to: {COLORS_FILE}")
    print(f"✓ Weekdays canonical saved to: {WEEKDAYS_FILE}")
    print(f"✓ Combined canonical saved to: {CANONICAL_COMBINED_FILE}")

if __name__ == "__main__":
    main()
