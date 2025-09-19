import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDatabaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Prefer new Agent API; fall back to OpenAI Functions agent if needed.
_USE_NEW_API = False
AgentExecutor = None
create_tool_calling_agent = None
OpenAIFunctionsAgent = None

try:
    from langchain.agents import AgentExecutor, create_tool_calling_agent
    _USE_NEW_API = True
except Exception:
    try:
        from langchain.agents import AgentExecutor
        from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
        _USE_NEW_API = False
    except Exception as e:
        raise ImportError(
            "Unsupported LangChain version. Install langchain>=0.1.20 or >=0.2.x.\n"
            "Underlying import error: " + str(e)
        )

# Callback base import (works for 0.2+ and older)
try:
    from langchain_core.callbacks import BaseCallbackHandler
except Exception:
    from langchain.callbacks.base import BaseCallbackHandler  # type: ignore


# =========================
# Timing callback
# =========================
@dataclass
class StepTiming:
    kind: str                     # "llm" or "tool"
    name: str                     # model name or tool name
    start: float
    end: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        return None if self.end is None else self.end - self.start


class TimingCallback(BaseCallbackHandler):
    """
    Captures precise timings for:
      - LLM call(s) (plan & finalize)
      - Tool call(s) (the SQL execution)
    Then you can read handler.pretty_report() after invoke().
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.steps: List[StepTiming] = []
        self._llm_stack: List[int] = []
        self._tool_stack: List[int] = []
        self.token_usages: List[Dict[str, Any]] = []

    # ---- LLM ----
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        name = (serialized or {}).get("name") or (serialized or {}).get("id") or "llm"
        self.steps.append(StepTiming(kind="llm", name=str(name), start=time.perf_counter(), extra={"prompts": prompts}))
        self._llm_stack.append(len(self.steps) - 1)

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        if not self._llm_stack:
            return
        idx = self._llm_stack.pop()
        self.steps[idx].end = time.perf_counter()
        # Try to capture token usage if present
        usage = None
        try:
            usage = (response.llm_output or {}).get("token_usage")
        except Exception:
            usage = None
        if usage:
            self.steps[idx].extra["token_usage"] = usage
            self.token_usages.append(usage)

    # ---- Tool ----
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        name = (serialized or {}).get("name") or "tool"
        self.steps.append(StepTiming(kind="tool", name=str(name), start=time.perf_counter(), extra={"input": input_str}))
        self._tool_stack.append(len(self.steps) - 1)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        if not self._tool_stack:
            return
        idx = self._tool_stack.pop()
        self.steps[idx].end = time.perf_counter()
        # Store a short preview of the output
        preview = output
        if isinstance(preview, str) and len(preview) > 500:
            preview = preview[:500] + "...[truncated]"
        self.steps[idx].extra["output_preview"] = preview

    # Convenience pretty printer
    def pretty_report(self, total_seconds: float) -> str:
        lines = []
        llm_count = 0
        tool_count = 0
        for s in self.steps:
            dur = f"{(s.duration or 0):.3f}s"
            if s.kind == "llm":
                llm_count += 1
                name = s.name
                lines.append(f"  LLM #{llm_count} [{name}]: {dur}")
            else:
                tool_count += 1
                name = s.name
                lines.append(f"  TOOL #{tool_count} [{name}]: {dur}")
                # If it's the SQL tool, show the SQL text briefly
                sql = s.extra.get("input", "")
                if sql:
                    sql_preview = sql
                    if len(sql_preview) > 500:
                        sql_preview = sql_preview[:500] + "...[truncated]"
                    lines.append("    SQL:")
                    for l in sql_preview.splitlines():
                        lines.append(f"      {l}")

        lines.append(f"  TOTAL: {total_seconds:.3f}s")
        return "\n".join(lines)


# =========================
# 1) Load env
# =========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_URI = "postgresql+psycopg2://postgres:Harrison891%21@localhost:5432/flower_bot_db"

# =========================
# 2) System Prompt (unchanged behavior)
# =========================
SYSTEM_PROMPT = """
You are an AI flower consultant that helps customers find the perfect flowers by querying a SQL database.

EXECUTION DISCIPLINE — IMPORTANT
- Build the SQL in one shot and call EXACTLY ONE tool: `sql_db_query`.
- Do NOT call any other tools. Do NOT run multiple queries or retries.
- Use only columns that exist in the schema; do not guess new names.

CRITICAL QUERY RULES — Follow these exactly:

=== UNIVERSAL NULL HANDLING RULE ===
- When user specifies a preference: add "AND <column> IS NOT NULL" to filter out missing data.
- When user doesn't specify: include products with NULL values in that column.
- Applies to ALL variables.

=== 1) BUDGET FILTERING ===
Column: variant_price
User Intent Mapping:
- "under $X" → WHERE variant_price < X AND variant_price IS NOT NULL
- "$X to $Y" → WHERE variant_price BETWEEN X AND Y AND variant_price IS NOT NULL
- "budget-friendly" → WHERE variant_price <= 100 AND variant_price IS NOT NULL
- "premium/expensive" → WHERE variant_price > 200 AND variant_price IS NOT NULL
- "around $X" → WHERE variant_price BETWEEN (X-20) AND (X+20) AND variant_price IS NOT NULL

=== 2) EVENT DATE FILTERING ===
Columns (exact DB names):
- season_start_month, season_start_day, season_end_month, season_end_day
- season_range_2_start_month, season_range_2_start_day, season_range_2_end_month, season_range_2_end_day
- season_range_3_start_month, season_range_3_start_day, season_range_3_end_month, season_range_3_end_day
- is_year_round (boolean)

Rules:
1. Always include products with is_year_round = TRUE.
2. Convert user input to (event_month, event_day):
   - Specific date: "May 12" → (5, 12)
   - Seasons: spring→(3,20), summer→(6,21), fall/autumn→(9,22), winter→(12,21)
   - Month name → mid-month (e.g., December → (12,15))
3. A product matches if the event date falls inside ANY of the 3 ranges.

IMPORTANT PARENTHESES RULE:
- When combining availability with other filters, wrap the entire availability OR-block in parentheses, then AND with other conditions.

Availability WHERE block (parenthesize as a single unit):
(
  is_year_round = TRUE
  OR (
    (season_start_month < :event_month OR (season_start_month = :event_month AND season_start_day <= :event_day))
    AND
    (season_end_month > :event_month OR (season_end_month = :event_month AND season_end_day >= :event_day))
  )
  OR ... (for range 2 and range 3)
)

=== 3) EVENT TYPE FILTERING ===
Column: holiday_occasion (string)
Examples:
- wedding → LOWER(holiday_occasion) LIKE '%wedding%' AND holiday_occasion IS NOT NULL
- valentine's day → LIKE '%valentine%' ...
- mother's day → LIKE '%mother%' ...
- birthday → LIKE '%birthday%' ...
- graduation → LIKE '%graduation%' ...

=== 4) EFFORT LEVEL FILTERING ===
Column: diy_level ∈ ('Ready To Go','DIY In A Kit','DIY From Scratch')
Examples:
- "ready-made"/"no work"/"easy"/"low effort"/"pre-made" → diy_level = 'Ready To Go' AND diy_level IS NOT NULL
- "some DIY"/"kit"/"medium effort" → diy_level = 'DIY In A Kit' AND diy_level IS NOT NULL
- "from scratch"/"high effort" → diy_level = 'DIY From Scratch' AND diy_level IS NOT NULL

=== 5) COLOR FILTERING ===
Columns: colors_raw (string), has_red, has_pink, has_white, has_yellow, has_orange, has_purple, has_blue, has_green

AND logic (e.g., "red and white"):
  has_red = true AND has_white = true AND colors_raw IS NOT NULL

OR logic (e.g., "red or white"):
  (has_red = true OR has_white = true) AND colors_raw IS NOT NULL

Single color:
  has_pink = true AND colors_raw IS NOT NULL

Literal name (not in booleans, e.g., "terracotta"):
  LOWER(colors_raw) LIKE '%terracotta%' AND colors_raw IS NOT NULL

=== 6) FLOWER TYPE FILTERING ===
Columns: group_category, subgroup_category, product_name, variant_name, product_type_all_flowers, recipe_metafield
Auto singularize: roses→rose, lilies→lily, peonies→peony, carnations→carnation
"Rose" detection across multiple columns:
  (
    LOWER(group_category) LIKE '%rose%'
    OR LOWER(recipe_metafield) LIKE '%rose%'
    OR LOWER(product_type_all_flowers) LIKE '%rose%'
    OR LOWER(product_name) LIKE '%rose%'
  )
AND (group_category IS NOT NULL OR recipe_metafield IS NOT NULL OR product_type_all_flowers IS NOT NULL OR product_name IS NOT NULL)

=== FAST RESULT SELECTION (NO ORDER BY RANDOM()) — REQUIRED ===
PostgreSQL does NOT allow referencing table columns/CTEs in OFFSET/LIMIT. Use a window-function sampler (no variables in OFFSET/LIMIT):

-- Replace <FILTERS> with your combined WHERE filters.
-- Use an indexed, stable ORDER BY (unique_id).
WITH filtered AS (
  SELECT *
  FROM flowers
  WHERE <FILTERS>
),
numbered AS (
  SELECT
    f.*,
    ROW_NUMBER() OVER (ORDER BY unique_id) AS rn,
    COUNT(*)    OVER ()                   AS c
  FROM filtered f
),
params AS (
  -- pick a starting index r uniformly from [0, GREATEST(0,c-10)]
  SELECT FLOOR(random() * GREATEST(0, c - 10))::int AS r
  FROM numbered
  LIMIT 1
)
SELECT n.*
FROM numbered n
CROSS JOIN params p
WHERE n.rn > p.r AND n.rn <= p.r + 10;

=== QUERY CONSTRUCTION RULES ===
1) Select only necessary columns when feasible (avoid SELECT *).
2) Combine filters with correct AND/OR logic; add IS NOT NULL where the user specified a preference.
3) Use the WINDOW SAMPLER above (do NOT use ORDER BY RANDOM(); do NOT put columns in OFFSET/LIMIT).
4) Run exactly one `sql_db_query` call.

=== RESPONSE FORMATTING ===
Open with a sentence about how many products are shown. For each product:

{{n}}. **Product Name**
    Price: $X
    Colors: ...
    Effort Level: ...
    Product Type: ...
    Recipe: ...
    Availability: ...
    Description: ...
    Occasions: ...

- Numbered list; indent attributes.
- Include available fields; skip if NULL.
- Availability: "Year-round" if is_year_round = TRUE; else show ranges like "Nov 15 – Feb 20".
- If no results, offer close alternatives or ask a clarifying question.
"""

# =========================
# 3) LLM + DB + Tool (query only)
# =========================
llm = ChatOpenAI(
    model="gpt-4o-mini-2024-07-18",
    temperature=0,
    timeout=8,        # keep snappy
    max_retries=0,    # no client retries; we want crisp timing
    openai_api_key=OPENAI_API_KEY,
)

# Keep a pooled engine to avoid reconnect costs
db = SQLDatabase.from_uri(
    DB_URI,
    engine_args={
        "pool_size": 5,
        "max_overflow": 5,
        "pool_pre_ping": True,
    },
)

tools = [QuerySQLDatabaseTool(db=db)]  # only the query tool → no schema/list detours

# =========================
# 4) Prompt: system → scratchpad → user
# =========================
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT.strip()),
    MessagesPlaceholder("agent_scratchpad"),
    ("user", "{input}"),
])

# =========================
# 5) Agent + executor (allow up to 3 steps)
# =========================
if _USE_NEW_API:
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=False,
        max_iterations=3,   # NOTE: allow 2 LLM calls + 1 tool call
    )
else:
    agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=False,
        max_iterations=3,
    )

# =========================
# 6) Wrapper & CLI
# =========================
class FlowerConsultant:
    def __init__(self, db_uri: str, api_key: str):
        self.db_uri = db_uri
        self.api_key = api_key
        self.executor = agent_executor
        self.conversation_count = 0

    def ask(self, user_input: str):
        self.conversation_count += 1
        print(f"\nProcessing query #{self.conversation_count}...")
        handler = TimingCallback()

        t0 = time.perf_counter()
        try:
            # Pass our timing callback through invoke config
            result = self.executor.invoke({"input": user_input}, config={"callbacks": [handler]})
            total = time.perf_counter() - t0

            # Print the bot's answer
            output = result.get("output") if isinstance(result, dict) else result
            print(f"\nBot:\n{output}\n")

            # Pretty timing report
            print("TIMINGS:")
            print(handler.pretty_report(total_seconds=total))
            print()

        except Exception as e:
            total = time.perf_counter() - t0
            print(f"Error: {e}")
            print("Please try rephrasing your question or ask for help with flower selection.\n")
            # Even on error, dump whatever timings we captured
            try:
                print("TIMINGS (partial):")
                print(handler.pretty_report(total_seconds=total))
                print()
            except Exception:
                pass


if __name__ == "__main__":
    bot = FlowerConsultant(DB_URI, OPENAI_API_KEY)
    print("AI Flower Consultant ready! Type 'exit' to quit.")
    print("Example queries:")
    print("- 'I need red and white flowers for a wedding under $150'")
    print("- 'Show me ready-made pink bouquets for Mother's Day'")
    print("- 'What roses are available for Valentine's Day?'")
    print("- 'I want DIY flowers for a summer graduation'")
    print()
    while True:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        if user_input.lower() in ["exit", "quit", "q"]:
            break
        if not user_input.strip():
            print("Please enter a question about flowers!")
            continue
        bot.ask(user_input)
    print("Thank you for using the AI Flower Consultant!")

