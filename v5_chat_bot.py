import os
import json
import time
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text

# =========================
# 1) Env & DB
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_URI = "postgresql+psycopg2://postgres:Harrison891%21@localhost:5432/flower_bot_db"

# SQLAlchemy engine (fast direct exec)
ENGINE = create_engine(DB_URI, pool_pre_ping=True)

# =========================
# 2) System Prompt (compact but complete)
# =========================
SYSTEM_PROMPT = """
You are an AI that ONLY returns JSON containing a single SQL query to retrieve up to 10 flower products.
Return exactly: {"sql": "<final SQL>"} — no other text.

DATABASE (PostgreSQL) TABLE: flowers
Columns include (not exhaustive):
- unique_id (PK, text), product_name, variant_name, description_clean, variant_price (numeric)
- group_category, subgroup_category, product_type_all_flowers, recipe_metafield
- holiday_occasion, diy_level
- colors_raw (string), has_red, has_pink, has_white, has_yellow, has_orange, has_purple, has_blue, has_green (booleans)
- seasonality (text)
- season_start_month, season_start_day, season_end_month, season_end_day
- season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day
- season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
- is_year_round (boolean)
(Use ONLY existing names above. Do not invent columns.)

EXECUTION DISCIPLINE
- Build the SQL in ONE SHOT, no retries.
- Use <= 10 rows.
- Prefer selecting the specific columns needed for display:
  unique_id, product_name, variant_name, description_clean, variant_price,
  colors_raw, diy_level, product_type_all_flowers, group_category,
  recipe_metafield, holiday_occasion, is_year_round,
  season_start_month, season_start_day, season_end_month, season_end_day,
  season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day,
  season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
- DO NOT use ORDER BY RANDOM().

UNIVERSAL NULL HANDLING RULE
- If the user explicitly specifies a preference on a column, add "AND <column> IS NOT NULL".
- If the user did NOT specify a preference on that column, keep NULLs.

BUDGET FILTERING (variant_price)
- "under $X" -> variant_price < X AND variant_price IS NOT NULL
- "$X to $Y" -> variant_price BETWEEN X AND Y AND variant_price IS NOT NULL
- "budget-friendly" -> variant_price <= 100 AND variant_price IS NOT NULL
- "premium/expensive" -> variant_price > 200 AND variant_price IS NOT NULL
- "around $X" -> variant_price BETWEEN (X-20) AND (X+20) AND variant_price IS NOT NULL

EVENT TYPE FILTERING (holiday_occasion)
- Examples:
  "wedding" -> LOWER(holiday_occasion) LIKE '%wedding%' AND holiday_occasion IS NOT NULL
  "valentine's day" -> LIKE '%valentine%' AND holiday_occasion IS NOT NULL
  "mother's day" -> LIKE '%mother%' AND holiday_occasion IS NOT NULL
  "birthday" -> LIKE '%birthday%' AND holiday_occasion IS NOT NULL
  "graduation" -> LIKE '%graduation%' AND holiday_occasion IS NOT NULL

EFFORT LEVEL FILTERING (diy_level) ∈ {'Ready To Go','DIY In A Kit','DIY From Scratch'}
- ready-made / no work / easy / pre-made -> diy_level = 'Ready To Go' AND diy_level IS NOT NULL
- some DIY / kit / medium effort -> diy_level = 'DIY In A Kit' AND diy_level IS NOT NULL
- full DIY / from scratch / high effort -> diy_level = 'DIY From Scratch' AND diy_level IS NOT NULL

COLOR FILTERING
- AND logic: if user says "red and white": has_red = true AND has_white = true AND colors_raw IS NOT NULL
- OR logic: if user says "red or white": (has_red = true OR has_white = true) AND colors_raw IS NOT NULL
- Single color (e.g., pink): has_pink = true AND colors_raw IS NOT NULL
- Literal names not covered by booleans (e.g., "terracotta", "sage"): LOWER(colors_raw) LIKE '%terracotta%' AND colors_raw IS NOT NULL

FLOWER TYPE FILTERING
- Auto singularize common plurals: roses→rose, lilies→lily, peonies→peony, carnations→carnation
- For a specific flower name "rose", check ANY of:
  (LOWER(group_category) LIKE '%rose%' OR
   LOWER(recipe_metafield) LIKE '%rose%' OR
   LOWER(product_type_all_flowers) LIKE '%rose%' OR
   LOWER(product_name) LIKE '%rose%')
  AND (group_category IS NOT NULL OR recipe_metafield IS NOT NULL OR
       product_type_all_flowers IS NOT NULL OR product_name IS NOT NULL)
- Product types ("bouquet"/"centerpiece"):
  (LOWER(product_name) LIKE '%bouquet%' OR LOWER(product_type_all_flowers) LIKE '%bouquet%')
  AND (product_name IS NOT NULL OR product_type_all_flowers IS NOT NULL)
- Quantity ("100 stems"): LOWER(variant_name) LIKE '%100%' AND variant_name IS NOT NULL

EVENT DATE (AVAILABILITY) FILTERING
- User input → (event_month, event_day)
  Seasons: spring→(3,20), summer→(6,21), fall/autumn→(9,22), winter→(12,21)
  Month name → mid-month (Jan→(1,15), ..., Dec→(12,15))
  Specific date "May 12" → (5,12)
- Always include is_year_round = TRUE.
- A product matches if event date falls inside ANY of the 3 ranges:
  Single range check template:
  (
    (season_start_month < :event_month OR
     (season_start_month = :event_month AND season_start_day <= :event_day))
    AND
    (season_end_month > :event_month OR
     (season_end_month = :event_month AND season_end_day >= :event_day))
  )
- IMPORTANT: Wrap the WHOLE availability OR-block in parentheses, then AND with other filters:
  (
    is_year_round = TRUE
    OR <range 1 condition>
    OR <range 2 condition>
    OR <range 3 condition>
  )

FAST RESULT SELECTION (NO ORDER BY RANDOM())
- Use a window-function sampler to pick a random start without OFFSET variables:
  -- Replace <FILTERS> with the combined WHERE conditions.
  WITH filtered AS (
    SELECT
      unique_id, product_name, variant_name, description_clean, variant_price,
      colors_raw, diy_level, product_type_all_flowers, group_category,
      recipe_metafield, holiday_occasion, is_year_round,
      season_start_month, season_start_day, season_end_month, season_end_day,
      season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day,
      season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
    FROM flowers
    WHERE <FILTERS>
  ),
  numbered AS (
    SELECT f.*,
           ROW_NUMBER() OVER (ORDER BY unique_id) AS rn,
           COUNT(*)    OVER ()                    AS c
    FROM filtered f
  ),
  params AS (
    SELECT FLOOR(random() * GREATEST(0, c - 10))::int AS r
    FROM numbered
    LIMIT 1
  )
  SELECT *
  FROM numbered n
  CROSS JOIN params p
  WHERE n.rn > p.r AND n.rn <= p.r + 10;

CONSTRAINTS
- Use correct column names exactly as listed.
- Combine filters using correct AND/OR (especially color “and” vs “or”).
- Respect NULL-handling rule.
- Limit to <= 10 rows (window sampler does this).
- Return ONLY valid JSON with key "sql".
"""

# =========================
# 3) LLM (one call)
# =========================
llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    timeout=12,     # keep snappy
    max_retries=0,  # no client retries
)

# =========================
# 4) Helpers
# =========================
MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def first_nonempty(row: Dict[str, Any], keys: List[str]) -> Optional[str]:
    for k in keys:
        v = row.get(k)
        if v is None:
            continue
        if isinstance(v, str) and v.strip() == "":
            continue
        return str(v)
    return None

def format_availability(row: Dict[str, Any]) -> Optional[str]:
    # Year-round?
    if row.get("is_year_round") in (True, "t", "true", 1):
        return "Year-round"

    def fmt_range(sm, sd, em, ed):
        try:
            if sm and sd and em and ed:
                sm = int(sm); sd = int(sd); em = int(em); ed = int(ed)
                if 1 <= sm <= 12 and 1 <= em <= 12:
                    return f"{MONTH_ABBR[sm-1]} {sd:02d} – {MONTH_ABBR[em-1]} {ed:02d}"
        except Exception:
            return None
        return None

    r1 = fmt_range(row.get("season_start_month"), row.get("season_start_day"),
                   row.get("season_end_month"), row.get("season_end_day"))
    r2 = fmt_range(row.get("season_range_2_start_month"), row.get("season_range_2_start_day"),
                   row.get("season_range_2_end_month"), row.get("season_range_2_end_day"))
    r3 = fmt_range(row.get("season_range_3_start_month"), row.get("season_range_3_start_day"),
                   row.get("season_range_3_end_month"), row.get("season_range_3_end_day"))
    ranges = [r for r in [r1, r2, r3] if r]
    if ranges:
        return " / ".join(ranges)
    return None

def render_rows(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "I couldn’t find matching products. Want me to loosen a filter or try alternatives?"

    out_lines = []
    out_lines.append(f"Here are {min(len(rows), 10)} products that match your request:\n")
    for i, r in enumerate(rows[:10], start=1):
        name = first_nonempty(r, ["product_name"]) or "(Unnamed product)"
        price = first_nonempty(r, ["variant_price"])
        colors = first_nonempty(r, ["colors_raw"])
        effort = first_nonempty(r, ["diy_level"])
        ptype = first_nonempty(r, ["product_type_all_flowers", "group_category"])
        recipe = first_nonempty(r, ["recipe_metafield"])
        occ = first_nonempty(r, ["holiday_occasion"])
        avail = format_availability(r) or (first_nonempty(r, ["seasonality"]) or None)

        out_lines.append(f"{i}. **{name}**")
        if price:  out_lines.append(f"   - Price: ${price}")
        if colors: out_lines.append(f"   - Colors: {colors}")
        if effort: out_lines.append(f"   - Effort Level: {effort}")
        if ptype:  out_lines.append(f"   - Product Type: {ptype}")
        if recipe: out_lines.append(f"   - Recipe: {recipe}")
        if avail:  out_lines.append(f"   - Availability: {avail}")
        if occ:    out_lines.append(f"   - Occasions: {occ}")
        # Optional tiny description to keep output tight
        desc = first_nonempty(r, ["description_clean"])
        if desc:
            short = (desc[:180] + "…") if len(desc) > 180 else desc
            out_lines.append(f"   - Description: {short}")
        out_lines.append("")  # blank line between items
    return "\n".join(out_lines)

def ask_llm_for_sql(user_input: str) -> str:
    # To help the color AND/OR behavior, pass your raw text — rules in SYSTEM_PROMPT decide.
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": f"USER_REQUEST:\n{user_input}\n\nReturn only JSON: {{\"sql\": \"...\"}}"}
    ]
    t0 = time.perf_counter()
    resp = llm.invoke(messages)
    t1 = time.perf_counter()
    content = resp.content.strip()
    # Parse JSON
    try:
        data = json.loads(content)
        sql = data.get("sql")
        if not sql or not isinstance(sql, str):
            raise ValueError("Missing 'sql' in response.")
    except Exception as e:
        raise ValueError(f"Failed to parse LLM JSON: {e}\nRaw: {content}") from e
    return sql, (t1 - t0)

def run_sql(sql: str) -> (List[Dict[str, Any]], float):
    t0 = time.perf_counter()
    with ENGINE.connect() as conn:
        result = conn.execute(text(sql))
        rows = [dict(row._mapping) for row in result]
    t1 = time.perf_counter()
    return rows, (t1 - t0)

# =========================
# 5) CLI wrapper with timings
# =========================
class FlowerConsultant:
    def __init__(self):
        self.count = 0

    def ask(self, user_input: str):
        self.count += 1
        print(f"\nProcessing query #{self.count}...")

        try:
            sql, t_llm = ask_llm_for_sql(user_input)
        except Exception as e:
            print(f"Error building SQL from LLM: {e}\n")
            return

        try:
            rows, t_sql = run_sql(sql)
        except Exception as e:
            print("SQL execution error:")
            print(sql)
            print(f"\nError: {e}\n")
            return

        t0 = time.perf_counter()
        answer = render_rows(rows)
        t_render = time.perf_counter() - t0

        # Print the answer
        print("\nBot:\n" + answer + "\n")

        # Timings
        print("TIMINGS:")
        print(f"  LLM (build SQL): {t_llm:.3f}s")
        print(f"  SQL exec+fetch  : {t_sql:.3f}s")
        print(f"  Render (python) : {t_render:.3f}s")
        print(f"  TOTAL           : {t_llm + t_sql + t_render:.3f}s\n")

        # (Optional) Log SQL for debugging
        print("SQL USED:")
        print(sql)
        print()

# =========================
# 6) Main
# =========================
if __name__ == "__main__":
    print("AI Flower Consultant ready! Type 'exit' to quit.")
    print("Example queries:")
    print("- 'I need red and white flowers for a wedding under $150'")
    print("- 'Show me ready-made pink bouquets for Mother's Day'")
    print("- 'What roses are available for Valentine's Day?'")
    print("- 'I want DIY flowers for a summer graduation'")
    print()
    bot = FlowerConsultant()
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower().strip() in {"exit", "quit", "q"}:
            break
        if not user_input.strip():
            print("Please enter a question about flowers!")
            continue
        bot.ask(user_input)
    print("Thank you for using the AI Flower Consultant!")