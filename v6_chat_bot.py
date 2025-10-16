import os
import json
import time
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from sqlalchemy import create_engine, text

# Load color and occasion mappings
def load_mappings():
    """Load color and occasion mappings from JSON files"""
    try:
        with open('data/color_mapping.json', 'r') as f:
            color_mapping = json.load(f)
        with open('data/holiday_occasions.json', 'r') as f:
            occasions = json.load(f)
        return color_mapping, occasions
    except Exception as e:
        print(f"Warning: Could not load mappings: {e}")
        return {}, []

COLOR_MAPPING, OCCASIONS = load_mappings()

# =========================
# 1) Env & DB
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_URI = "postgresql+psycopg2://postgres:Harrison891%21@localhost:5432/flower_bot_db"

# SQLAlchemy engine (fast direct exec)
ENGINE = create_engine(DB_URI, pool_pre_ping=True)

# =========================
# 2) Memory State Management
# =========================
class MemoryState:
    """Stores user preferences extracted from conversation"""
    def __init__(self):
        self.colors = []  # List of colors user wants
        self.flower_types = []  # List of specific flower types (rose, lily, etc.)
        self.occasions = []  # List of occasions (wedding, birthday, etc.)
        self.budget = {"min": None, "max": None, "around": None}  # Budget constraints
        self.effort_level = None  # "Ready To Go", "DIY In A Kit", "DIY From Scratch"
        self.season = None  # "spring", "summer", "fall", "winter" or specific date
        self.quantity = None  # Number of stems, bouquets, etc.
        self.product_type = None  # "bouquet", "centerpiece", etc.
        self.color_logic = "AND"  # "AND" or "OR" for multiple colors
        # Negative preferences - things user specifically doesn't want
        self.exclude_colors = []
        self.exclude_flower_types = []
        self.exclude_occasions = []
        self.exclude_effort_levels = []
        self.exclude_product_types = []
        
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "colors": self.colors,
            "flower_types": self.flower_types,
            "occasions": self.occasions,
            "budget": self.budget,
            "effort_level": self.effort_level,
            "season": self.season,
            "quantity": self.quantity,
            "product_type": self.product_type,
            "color_logic": self.color_logic,
            "exclude_colors": self.exclude_colors,
            "exclude_flower_types": self.exclude_flower_types,
            "exclude_occasions": self.exclude_occasions,
            "exclude_effort_levels": self.exclude_effort_levels,
            "exclude_product_types": self.exclude_product_types
        }
    
    def update_from_dict(self, data: dict):
        """Update state from dictionary"""
        # Handle filter removal commands
        for key, value in data.items():
            if key.startswith("REMOVE_"):
                field_name = key[7:]  # Remove "REMOVE_" prefix
                if field_name == "all":
                    # Clear everything
                    self.colors = []
                    self.flower_types = []
                    self.occasions = []
                    self.budget = {"min": None, "max": None, "around": None}
                    self.effort_level = None
                    self.season = None
                    self.quantity = None
                    self.product_type = None
                    self.color_logic = "AND"
                elif field_name == "colors":
                    self.colors = []
                elif field_name == "flower_types":
                    self.flower_types = []
                elif field_name == "occasions":
                    self.occasions = []
                elif field_name == "budget":
                    self.budget = {"min": None, "max": None, "around": None}
                elif field_name == "effort_level":
                    self.effort_level = None
                elif field_name == "season":
                    self.season = None
                elif field_name == "quantity":
                    self.quantity = None
                elif field_name == "product_type":
                    self.product_type = None
                elif field_name == "exclude_colors":
                    self.exclude_colors = []
                elif field_name == "exclude_flower_types":
                    self.exclude_flower_types = []
                elif field_name == "exclude_occasions":
                    self.exclude_occasions = []
                elif field_name == "exclude_effort_levels":
                    self.exclude_effort_levels = []
                elif field_name == "exclude_product_types":
                    self.exclude_product_types = []
        
        # Handle regular updates - only update if field has actual values (not empty list/None)
        if "colors" in data and data["colors"]:  # Only update if non-empty
            self.colors = data["colors"]
        if "flower_types" in data and data["flower_types"]:  # Only update if non-empty
            self.flower_types = data["flower_types"]
        if "occasions" in data and data["occasions"]:  # Only update if non-empty
            self.occasions = data["occasions"]
        if "budget" in data and data["budget"]:
            self.budget.update(data["budget"])
        if "effort_level" in data and data["effort_level"]:
            self.effort_level = data["effort_level"]
        if "season" in data and data["season"]:
            self.season = data["season"]
        if "quantity" in data and data["quantity"]:
            self.quantity = data["quantity"]
        if "product_type" in data and data["product_type"]:
            self.product_type = data["product_type"]
        if "color_logic" in data and data["color_logic"]:
            self.color_logic = data["color_logic"]
        
        # Handle exclude fields - only update if field has actual values
        if "exclude_colors" in data and data["exclude_colors"]:  # Only update if non-empty
            self.exclude_colors = data["exclude_colors"]
        if "exclude_flower_types" in data and data["exclude_flower_types"]:  # Only update if non-empty
            self.exclude_flower_types = data["exclude_flower_types"]
        if "exclude_occasions" in data and data["exclude_occasions"]:  # Only update if non-empty
            self.exclude_occasions = data["exclude_occasions"]
        if "exclude_effort_levels" in data and data["exclude_effort_levels"]:  # Only update if non-empty
            self.exclude_effort_levels = data["exclude_effort_levels"]
        if "exclude_product_types" in data and data["exclude_product_types"]:  # Only update if non-empty
            self.exclude_product_types = data["exclude_product_types"]

# =========================
# 3) Parser LLM (Memory Updates)
# =========================
PARSER_PROMPT = """
You are an AI that extracts user preferences from natural language and updates a memory state.

Return ONLY valid JSON with the following structure:
{
  "colors": ["red", "white"],  // List of colors mentioned
  "flower_types": ["rose", "lily"],  // Specific flower types mentioned  
  "occasions": ["wedding", "birthday"],  // Occasions mentioned
  "budget": {"min": 50, "max": 100, "around": null},  // Budget constraints
  "effort_level": "Ready To Go",  // or "DIY In A Kit" or "DIY From Scratch"
  "season": "spring",  // Season or specific date like "May 15"
  "quantity": "100 stems",  // Quantity mentioned
  "product_type": "bouquet",  // Product type mentioned
  "color_logic": "AND",  // "AND" if colors should be combined, "OR" if alternatives
  "exclude_colors": ["pink"],  // Colors user specifically doesn't want
  "exclude_flower_types": ["rose"],  // Flower types user doesn't want
  "exclude_occasions": ["wedding"],  // Occasions user doesn't want
  "exclude_effort_levels": ["DIY From Scratch"],  // Effort levels user doesn't want
  "exclude_product_types": ["centerpiece"]  // Product types user doesn't want
}

RULES:
- Only include fields that are explicitly mentioned or can be clearly inferred
- For budget: "under $50" → {"max": 50}, "$50-$100" → {"min": 50, "max": 100}, "around $75" → {"around": 75}
- For colors: "red and white" → ["red", "white"] with "AND", "red or white" → ["red", "white"] with "OR"
- For color phrases: "cool colors" → ["cool colors"], "warm colors" → ["warm colors"], "neutral colors" → ["neutral colors"]
- For seasons: "spring" → "spring", "summer" → "summer", "fall" → "fall", "winter" → "winter"
- For months: "October" → "October", "December" → "December", "May" → "May"
- For specific dates: "October 15" → "October 15", "November 19" → "November 19", "May 12th" → "May 12"
- For effort: "ready-made" → "Ready To Go", "DIY kit" → "DIY In A Kit", "from scratch" → "DIY From Scratch"
- For flower types: "roses" → ["rose"], "lilies" → ["lily"], "peonies" → ["peony"], "carnations" → ["carnation"]
- For occasions: "wedding" → ["wedding"], "birthday" → ["birthday"], "valentine's day" → ["valentine's day"]
- For filter removal (ONLY when user explicitly says "remove", "clear", "don't want anymore"):
  * "remove colors" or "clear colors" or "don't want colors anymore" → {"REMOVE_colors": true}
  * "remove budget" or "clear budget" → {"REMOVE_budget": true}
  * "remove season" or "clear season" or "no season filter" → {"REMOVE_season": true}
  * "remove occasion" or "clear occasion" or "don't want occasion" → {"REMOVE_occasions": true}
  * "remove flowers" or "clear flowers" → {"REMOVE_flower_types": true}
  * "remove effort" or "clear effort" → {"REMOVE_effort_level": true}
  * "remove product type" or "clear product type" → {"REMOVE_product_type": true}
  * "remove all" or "clear all" or "clear everything" or "reset" → {"REMOVE_all": true}
- IMPORTANT: "for a wedding" means ADD occasions: ["wedding"], NOT remove it!
- For negative preferences: "don't want pink" → {"exclude_colors": ["pink"]}, "no roses" → {"exclude_flower_types": ["rose"]}
- For "avoid expensive" → {"exclude_effort_levels": ["DIY From Scratch"]}, "not DIY" → {"exclude_effort_levels": ["DIY From Scratch"]}
- For "no centerpieces" → {"exclude_product_types": ["centerpiece"]}, "avoid weddings" → {"exclude_occasions": ["wedding"]}
- Leave fields as null/empty if not mentioned
- Return ONLY the JSON, no other text
"""

# =========================
# 4) System Prompt (compact but complete)
# =========================
SYSTEM_PROMPT = """
You are an AI that ONLY returns JSON containing a single SQL query to retrieve up to 6 flower products.
Return exactly: {"sql": "<final SQL>"} — no other text.

DATABASE (PostgreSQL) TABLE: flowers
Columns include (not exhaustive):
- unique_id (PK, text), product_name, variant_name, description_clean, variant_price (numeric)
- group_category, subgroup_category, product_type_all_flowers, recipe_metafield
- holiday_occasion, diy_level, non_color_options
- colors_raw (string), has_red, has_pink, has_white, has_yellow, has_orange, has_purple, has_blue, has_green (booleans)
- seasonality (text)
- season_start_month, season_start_day, season_end_month, season_end_day
- season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day
- season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
- is_year_round (boolean)
(Use ONLY existing names above. Do not invent columns.)

EXECUTION DISCIPLINE
- Build the SQL in ONE SHOT, no retries.
- Use <= 6 rows.
- ensure variety by DISTINCT ON (product_name).

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
    SELECT DISTINCT ON (product_name)
      unique_id, product_name, variant_name, description_clean, variant_price,
      colors_raw, diy_level, product_type_all_flowers, group_category,
      recipe_metafield, holiday_occasion, is_year_round, non_color_options,
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
    SELECT FLOOR(random() * GREATEST(0, c - 6))::int AS r
    FROM numbered
    LIMIT 1
  )
  SELECT *
  FROM numbered n
  CROSS JOIN params p
  WHERE n.rn > p.r AND n.rn <= p.r + 6;

CONSTRAINTS
- Use correct column names exactly as listed.
- Combine filters using correct AND/OR (especially color "and" vs "or").
- Respect NULL-handling rule.
- Limit to <= 6 rows (window sampler does this).
- Return ONLY valid JSON with key "sql".
"""

# =========================
# 5) LLM Instances
# =========================
llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    timeout=12,     # keep snappy
    max_retries=1,  # no client retries
)

parser_llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
    timeout=8,      # even snappier for parsing
    max_retries=1,
)

# =========================
# 6) Parser and SQL Builder Functions
# =========================
def parse_user_input(user_input: str) -> dict:
    """Parse user input and extract preferences into structured format"""
    messages = [
        {"role": "system", "content": PARSER_PROMPT.strip()},
        {"role": "user", "content": f"USER_INPUT: {user_input}\n\nExtract preferences:"}
    ]
    
    try:
        resp = parser_llm.invoke(messages)
        content = resp.content.strip()
        
        # Parse JSON response
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"Parser error: {e}")
        return {}

def is_valid_date(month: int, day: int) -> bool:
    """Validate if a month/day combination is valid"""
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return False
    
    # Days per month
    days_in_month = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]  # Feb has 29 for leap year validation
    return day <= days_in_month[month - 1]

def parse_season_to_date(season_input: str) -> tuple:
    """Parse season/date input to (month, day) tuple"""
    import re
    from datetime import datetime
    
    season_lower = season_input.lower().strip()
    
    # Season mappings
    seasons = {
        'spring': (3, 20),
        'summer': (6, 21), 
        'fall': (9, 22),
        'autumn': (9, 22),
        'winter': (12, 21)
    }
    
    # Month name mappings (to mid-month)
    months = {
        'january': (1, 15), 'jan': (1, 15),
        'february': (2, 15), 'feb': (2, 15),
        'march': (3, 15), 'mar': (3, 15),
        'april': (4, 15), 'apr': (4, 15),
        'may': (5, 15),
        'june': (6, 15), 'jun': (6, 15),
        'july': (7, 15), 'jul': (7, 15),
        'august': (8, 15), 'aug': (8, 15),
        'september': (9, 15), 'sep': (9, 15), 'sept': (9, 15),
        'october': (10, 15), 'oct': (10, 15),
        'november': (11, 15), 'nov': (11, 15),
        'december': (12, 15), 'dec': (12, 15)
    }
    
    # Check for seasons first
    if season_lower in seasons:
        return seasons[season_lower]
    
    # Check for month names
    if season_lower in months:
        return months[season_lower]
    
    # Check for specific dates like "October 15", "Nov 19", "May 12th"
    date_patterns = [
        r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?',  # "October 15th", "Nov 19"
        r'(\d{1,2})/(\d{1,2})',  # "10/15", "12/25"
        r'(\d{1,2})-(\d{1,2})'   # "10-15", "12-25"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, season_lower)
        if match:
            if pattern.startswith(r'(\w+)'):  # Month name + day
                month_name = match.group(1).lower()
                day = int(match.group(2))
                if month_name in months:
                    # Validate day for the specific month
                    month_num = months[month_name][0]
                    if is_valid_date(month_num, day):
                        return (month_num, day)
            else:  # Numeric format
                month = int(match.group(1))
                day = int(match.group(2))
                if 1 <= month <= 12 and is_valid_date(month, day):
                    return (month, day)
    
    # Default fallback - return None if can't parse
    return (None, None)

def build_seasonality_condition(event_month: int, event_day: int) -> str:
    """Build the complex seasonality condition for the SQL query"""
    
    def build_range_condition(start_month_col, start_day_col, end_month_col, end_day_col):
        return f"""
            ({start_month_col} < {event_month} OR
             ({start_month_col} = {event_month} AND {start_day_col} <= {event_day}))
            AND
            ({end_month_col} > {event_month} OR
             ({end_month_col} = {event_month} AND {end_day_col} >= {event_day}))
        """
    
    # Build the complete seasonality condition with all 3 ranges
    range1 = build_range_condition('season_start_month', 'season_start_day', 'season_end_month', 'season_end_day')
    range2 = build_range_condition('season_range_2_start_month', 'season_range_2_start_day', 'season_range_2_end_month', 'season_range_2_end_day')
    range3 = build_range_condition('season_range_3_start_month', 'season_range_3_start_day', 'season_range_3_end_month', 'season_range_3_end_day')
    
    return f"""
        (
            is_year_round = TRUE
            OR ({range1})
            OR ({range2})
            OR ({range3})
        )
    """

def build_sql_from_memory(memory: MemoryState) -> str:
    """Build SQL query deterministically from memory state"""
    
    # Start building WHERE conditions
    conditions = []
    
    # Color filtering with enhanced mapping support
    if memory.colors:
        color_conditions = []
        for color in memory.colors:
            color_lower = color.lower()
            
            # Handle color phrases first
            if "cool colors" in color_lower or "cool tones" in color_lower:
                color_conditions.append("(has_blue = true OR has_purple = true OR has_green = true)")
            elif "warm colors" in color_lower or "warm tones" in color_lower:
                color_conditions.append("(has_red = true OR has_orange = true OR has_yellow = true)")
            elif "neutral colors" in color_lower or "neutral tones" in color_lower:
                color_conditions.append("(has_white = true OR has_pink = true)")
            # Basic colors using boolean columns
            elif color_lower == "red":
                color_conditions.append("has_red = true")
            elif color_lower == "pink":
                color_conditions.append("has_pink = true")
            elif color_lower == "white":
                color_conditions.append("has_white = true")
            elif color_lower == "yellow":
                color_conditions.append("has_yellow = true")
            elif color_lower == "orange":
                color_conditions.append("has_orange = true")
            elif color_lower == "purple":
                color_conditions.append("has_purple = true")
            elif color_lower == "blue":
                color_conditions.append("has_blue = true")
            elif color_lower == "green":
                color_conditions.append("has_green = true")
            else:
                # Try to find color in JSON mappings
                found_in_mapping = False
                if COLOR_MAPPING and "color_categories" in COLOR_MAPPING:
                    for category, variants in COLOR_MAPPING["color_categories"].items():
                        if color_lower in variants or color_lower == category:
                            # Map to boolean column
                            if category == "red":
                                color_conditions.append("has_red = true")
                            elif category == "pink":
                                color_conditions.append("has_pink = true")
                            elif category == "white":
                                color_conditions.append("has_white = true")
                            elif category == "yellow":
                                color_conditions.append("has_yellow = true")
                            elif category == "orange":
                                color_conditions.append("has_orange = true")
                            elif category == "purple":
                                color_conditions.append("has_purple = true")
                            elif category == "blue":
                                color_conditions.append("has_blue = true")
                            elif category == "green":
                                color_conditions.append("has_green = true")
                            found_in_mapping = True
                            break
                
                if not found_in_mapping:
                    # For colors not covered by booleans or mappings, search in colors_raw
                    color_escaped = color_lower.replace("'", "''")
                    color_conditions.append(f"LOWER(colors_raw) LIKE '%{color_escaped}%'")
        
        if color_conditions:
            if memory.color_logic == "AND":
                color_clause = " AND ".join(color_conditions)
            else:  # OR logic
                color_clause = "(" + " OR ".join(color_conditions) + ")"
            
            conditions.append(f"({color_clause} AND colors_raw IS NOT NULL)")
    
    # Exclude color filtering
    if memory.exclude_colors:
        exclude_color_conditions = []
        for color in memory.exclude_colors:
            color_lower = color.lower()
            
            # Handle color phrases for exclusion
            if "cool colors" in color_lower or "cool tones" in color_lower:
                exclude_color_conditions.append("(has_blue = false AND has_purple = false AND has_green = false)")
            elif "warm colors" in color_lower or "warm tones" in color_lower:
                exclude_color_conditions.append("(has_red = false AND has_orange = false AND has_yellow = false)")
            elif "neutral colors" in color_lower or "neutral tones" in color_lower:
                exclude_color_conditions.append("(has_white = false AND has_pink = false)")
            # Basic colors using boolean columns
            elif color_lower == "red":
                exclude_color_conditions.append("has_red = false")
            elif color_lower == "pink":
                exclude_color_conditions.append("has_pink = false")
            elif color_lower == "white":
                exclude_color_conditions.append("has_white = false")
            elif color_lower == "yellow":
                exclude_color_conditions.append("has_yellow = false")
            elif color_lower == "orange":
                exclude_color_conditions.append("has_orange = false")
            elif color_lower == "purple":
                exclude_color_conditions.append("has_purple = false")
            elif color_lower == "blue":
                exclude_color_conditions.append("has_blue = false")
            elif color_lower == "green":
                exclude_color_conditions.append("has_green = false")
            else:
                # For colors not covered by booleans, exclude from colors_raw
                color_escaped = color_lower.replace("'", "''")
                exclude_color_conditions.append(f"LOWER(colors_raw) NOT LIKE '%{color_escaped}%'")
        
        if exclude_color_conditions:
            exclude_clause = " AND ".join(exclude_color_conditions)
            conditions.append(f"({exclude_clause})")
    
    # Flower type filtering
    if memory.flower_types:
        flower_conditions = []
        for flower in memory.flower_types:
            flower_lower = flower.lower()
            flower_conditions.append(f"""
                (LOWER(group_category) LIKE '%{flower_lower}%' OR
                 LOWER(recipe_metafield) LIKE '%{flower_lower}%' OR
                 LOWER(product_type_all_flowers) LIKE '%{flower_lower}%' OR
                 LOWER(product_name) LIKE '%{flower_lower}%')
            """)
        
        if flower_conditions:
            conditions.append(f"({' OR '.join(flower_conditions)})")
    
    # Exclude flower type filtering
    if memory.exclude_flower_types:
        exclude_flower_conditions = []
        for flower in memory.exclude_flower_types:
            flower_lower = flower.lower()
            exclude_flower_conditions.append(f"""
                (LOWER(group_category) NOT LIKE '%{flower_lower}%' AND
                 LOWER(recipe_metafield) NOT LIKE '%{flower_lower}%' AND
                 LOWER(product_type_all_flowers) NOT LIKE '%{flower_lower}%' AND
                 LOWER(product_name) NOT LIKE '%{flower_lower}%')
            """)
        
        if exclude_flower_conditions:
            conditions.append(f"({' AND '.join(exclude_flower_conditions)})")
    
    # Occasion filtering with JSON mapping support
    if memory.occasions:
        occasion_conditions = []
        for occasion in memory.occasions:
            occasion_lower = occasion.lower().replace("'", "''")  # Escape single quotes for SQL
            
            # Check if occasion is in our known list for validation
            if OCCASIONS and occasion_lower in OCCASIONS:
                occasion_conditions.append(f"LOWER(holiday_occasion) LIKE '%{occasion_lower}%'")
            else:
                # Still allow custom occasions but log for potential improvement
                occasion_conditions.append(f"LOWER(holiday_occasion) LIKE '%{occasion_lower}%'")
        
        if occasion_conditions:
            conditions.append(f"({' OR '.join(occasion_conditions)} AND holiday_occasion IS NOT NULL)")
    
    # Exclude occasion filtering
    if memory.exclude_occasions:
        exclude_occasion_conditions = []
        for occasion in memory.exclude_occasions:
            occasion_lower = occasion.lower().replace("'", "''")
            exclude_occasion_conditions.append(f"LOWER(holiday_occasion) NOT LIKE '%{occasion_lower}%'")
        
        if exclude_occasion_conditions:
            conditions.append(f"({' AND '.join(exclude_occasion_conditions)})")
    
    # Budget filtering
    if memory.budget.get("max") is not None:
        conditions.append(f"variant_price < {memory.budget['max']} AND variant_price IS NOT NULL")
    if memory.budget.get("min") is not None:
        conditions.append(f"variant_price >= {memory.budget['min']} AND variant_price IS NOT NULL")
    if memory.budget.get("around") is not None:
        around = memory.budget["around"]
        conditions.append(f"variant_price BETWEEN {around-20} AND {around+20} AND variant_price IS NOT NULL")
    
    # Effort level filtering
    if memory.effort_level:
        conditions.append(f"diy_level = '{memory.effort_level}' AND diy_level IS NOT NULL")
    
    # Exclude effort level filtering
    if memory.exclude_effort_levels:
        exclude_effort_conditions = []
        for effort in memory.exclude_effort_levels:
            exclude_effort_conditions.append(f"diy_level != '{effort}'")
        
        if exclude_effort_conditions:
            conditions.append(f"({' AND '.join(exclude_effort_conditions)})")
    
    # Product type filtering
    if memory.product_type:
        product_lower = memory.product_type.lower()
        conditions.append(f"""
            (LOWER(product_name) LIKE '%{product_lower}%' OR 
             LOWER(product_type_all_flowers) LIKE '%{product_lower}%')
            AND (product_name IS NOT NULL OR product_type_all_flowers IS NOT NULL)
        """)
    
    # Exclude product type filtering
    if memory.exclude_product_types:
        exclude_product_conditions = []
        for product_type in memory.exclude_product_types:
            product_lower = product_type.lower()
            exclude_product_conditions.append(f"""
                (LOWER(product_name) NOT LIKE '%{product_lower}%' AND 
                 LOWER(product_type_all_flowers) NOT LIKE '%{product_lower}%')
            """)
        
        if exclude_product_conditions:
            conditions.append(f"({' AND '.join(exclude_product_conditions)})")
    
    # Quantity filtering
    if memory.quantity:
        # Extract just the number from quantity strings like "100 stems", "50 stems"
        import re
        quantity_match = re.search(r'\d+', memory.quantity)
        if quantity_match:
            quantity_num = quantity_match.group()
            conditions.append(f"LOWER(variant_name) LIKE '%{quantity_num}%' AND variant_name IS NOT NULL")
    
    # Season filtering (proper implementation)
    if memory.season:
        event_month, event_day = parse_season_to_date(memory.season)
        if event_month and event_day:
            # Build the complex seasonality query
            seasonality_condition = build_seasonality_condition(event_month, event_day)
            conditions.append(seasonality_condition)
    
    # Build the final SQL
    where_clause = " AND ".join(conditions) if conditions else "TRUE"
    
    sql = f"""
    WITH filtered AS (
        SELECT DISTINCT ON (product_name)
            unique_id, product_name, variant_name, description_clean, variant_price,
            colors_raw, diy_level, product_type_all_flowers, group_category,
            recipe_metafield, holiday_occasion, is_year_round, non_color_options,
            season_start_month, season_start_day, season_end_month, season_end_day,
            season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day,
            season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
        FROM flowers
        WHERE {where_clause}
    ),
    numbered AS (
        SELECT f.*,
               ROW_NUMBER() OVER (ORDER BY unique_id) AS rn,
               COUNT(*)    OVER ()                    AS c
        FROM filtered f
    ),
    params AS (
        SELECT FLOOR(random() * GREATEST(0, c - 6))::int AS r
        FROM numbered
        LIMIT 1
    )
    SELECT *
    FROM numbered n
    CROSS JOIN params p
    WHERE n.rn > p.r AND n.rn <= p.r + 6;
    """
    
    return sql.strip()

# =========================
# 7) Helpers
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
        return "I couldn't find matching products with those exact criteria. Try:\n• Removing some filters (like budget or season)\n• Using broader terms (e.g., 'flowers' instead of specific types)\n• Checking if the date/season is valid\n\nWant me to show you some general options instead?"

    # Add seasonality breakdown for debugging
    seasonal_count = sum(1 for r in rows if not r.get('is_year_round', True))
    year_round_count = len(rows) - seasonal_count
    
    seasonality_info = ""
    if seasonal_count > 0:
        seasonality_info = f"\n📊 Seasonality: {seasonal_count} seasonal, {year_round_count} year-round products"

    out_lines = []
    out_lines.append(f"Here are {min(len(rows), 6)} recommendations I have:\n")
    for i, r in enumerate(rows[:6], start=1):
        name = first_nonempty(r, ["product_name"]) or "(Unnamed product)"
        variant = first_nonempty(r, ["variant_name"])
        price = first_nonempty(r, ["variant_price"])
        colors = first_nonempty(r, ["colors_raw"])
        effort = first_nonempty(r, ["diy_level"])
        ptype = first_nonempty(r, ["product_type_all_flowers", "group_category"])
        recipe = first_nonempty(r, ["recipe_metafield"])
        occ = first_nonempty(r, ["holiday_occasion"])
        avail = format_availability(r) or (first_nonempty(r, ["seasonality"]) or None)
        non_color_opts = first_nonempty(r, ["non_color_options"])

        # Display product name with variant if available
        display_name = name
        if variant and variant.lower() != name.lower():
            display_name = f"{name} - {variant}"

        out_lines.append(f"{i}. **{display_name}**")
        if price:  out_lines.append(f"   - Price: ${price}")
        if colors: out_lines.append(f"   - Colors: {colors}")
        if non_color_opts: out_lines.append(f"   - Options: {non_color_opts}")
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
    
    # Add seasonality info at the end
    out_lines.append(seasonality_info)
    return "\n".join(out_lines)

# This function is replaced by the memory-based system
# def ask_llm_for_sql(user_input: str) -> str:

def run_sql(sql: str) -> (List[Dict[str, Any]], float):
    t0 = time.perf_counter()
    with ENGINE.connect() as conn:
        result = conn.execute(text(sql))
        rows = [dict(row._mapping) for row in result]
    t1 = time.perf_counter()
    return rows, (t1 - t0)

# =========================
# 8) CLI wrapper with memory-based system
# =========================
class FlowerConsultant:
    def __init__(self):
        self.count = 0
        self.memory = MemoryState()  # Persistent memory across conversations

    def ask(self, user_input: str):
        self.count += 1
        print(f"\nProcessing query #{self.count}...")

        # Step 1: Parse user input and update memory
        try:
            t0 = time.perf_counter()
            parsed_data = parse_user_input(user_input)
            t_parse = time.perf_counter() - t0
            
            # Update memory with new preferences
            self.memory.update_from_dict(parsed_data)
            
            # Debug: Show current memory state
            print(f"Memory state: {self.memory.to_dict()}")
            
        except Exception as e:
            print(f"Error parsing user input: {e}\n")
            return

        # Step 2: Build SQL from memory
        try:
            t0 = time.perf_counter()
            sql = build_sql_from_memory(self.memory)
            t_sql_build = time.perf_counter() - t0
        except Exception as e:
            print(f"Error building SQL from memory: {e}\n")
            return

        # Step 3: Execute SQL
        try:
            rows, t_sql = run_sql(sql)
        except Exception as e:
            print("SQL execution error:")
            print(sql)
            print(f"\nError: {e}\n")
            return

        # Step 4: Render results
        t0 = time.perf_counter()
        answer = render_rows(rows)
        t_render = time.perf_counter() - t0

        # Print the answer
        print("\nFlower Assistant:\n" + answer + "\n")
        print("7. Book a consultation with a floral expert for personalized help:")
        print("https://fiftyflowers.com/products/personal-consultation-with-our-wedding-floral-expert?srsltid=AfmBOoqMQEmMIGbvgWhzct-LJYQY_yQ_d9_F8x4rpjJhrxa2-47Rfh51" + "\n")
        
        # Timings (optional - uncomment to see)
        # print("TIMINGS:")
        # print(f"  Parse (LLM)     : {t_parse:.3f}s")
        # print(f"  SQL build       : {t_sql_build:.3f}s")
        # print(f"  SQL exec+fetch  : {t_sql:.3f}s")
        # print(f"  Render (python) : {t_render:.3f}s")
        # print(f"  TOTAL           : {t_parse + t_sql_build + t_sql + t_render:.3f}s\n")

        # (Optional) Log SQL for debugging
        # print("SQL USED:")
        # print(sql)
        # print()

# =========================
# 6) Main
# =========================
if __name__ == "__main__":
    print()
    print("AI Flower Consultant ready! Type 'exit' to quit.")
    print("I'm your personal flower assistant! How can I help you find what you're looking for?")
    print("Give me some details about what you have in mind - color preferences, event type/date, effort level, etc.")
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
