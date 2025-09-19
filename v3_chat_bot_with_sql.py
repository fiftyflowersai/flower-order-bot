import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

# ---------------------------
# 1. Load environment
# ---------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ---------------------------
# 2. Connect to Postgres
# ---------------------------
DB_URI = "postgresql+psycopg2://postgres:Harrison891%21@localhost:5432/flower_bot_db"
db = SQLDatabase.from_uri(DB_URI)

# ---------------------------
# 3. Comprehensive System Prompt
# ---------------------------
SYSTEM_PROMPT = """
You are an AI flower consultant that helps customers find the perfect flowers by querying a SQL database.

CRITICAL QUERY RULES - Follow these exactly:

=== UNIVERSAL NULL HANDLING RULE ===
- When user specifies a preference: Add "AND column_name IS NOT NULL" to filter out missing data
- When user doesn't specify: Include products with NULL values in that column
- This applies to ALL variables below

=== 1. BUDGET FILTERING ===
Column: variant_price
User Intent Mapping:
- "under $X" → WHERE variant_price < X AND variant_price IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "$X to $Y" → WHERE variant_price BETWEEN X AND Y AND variant_price IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "budget-friendly" → WHERE variant_price <= 100 AND variant_price IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "premium/expensive" → WHERE variant_price > 200 AND variant_price IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "around $X" → WHERE variant_price BETWEEN (X-20) AND (X+20) AND variant_price IS NOT NULL ORDER BY RANDOM() LIMIT 10

=== 2. EVENT DATE FILTERING ===
Columns:
- season_start_month, season_start_day, season_end_month, season_end_day
- season2_start_month, season2_start_day, season2_end_month, season2_end_day
- season3_start_month, season3_start_day, season3_end_month, season3_end_day
- year_round (boolean)

Rules:
1. Always include products with year_round = TRUE.
2. Convert the user’s input into an (event_month, event_day).
   - Specific date: "May 12" → (5, 12)
   - Season: "summer" → (6, 21)
   - Month: "December" → (12, 15)
3. A product matches if the event date falls inside ANY of the three season ranges.

SQL Pattern for checking a single range:
(
   (season_start_month < :event_month OR 
    (season_start_month = :event_month AND season_start_day <= :event_day))
   AND
   (season_end_month > :event_month OR 
    (season_end_month = :event_month AND season_end_day >= :event_day))
)

Final SQL structure:
SELECT * 
FROM flowers
WHERE year_round = TRUE
   OR <range 1 condition>
   OR <range 2 condition>
   OR <range 3 condition>
ORDER BY RANDOM() LIMIT 10;

SEASON MAPPING:
- "spring" → March 20 (3, 20)
- "summer" → June 21 (6, 21) 
- "fall"/"autumn" → September 22 (9, 22)
- "winter" → December 21 (12, 21)

MONTH MAPPING (convert to mid-month):
- January → (1, 15), February → (2, 15), March → (3, 15), April → (4, 15),
- May → (5, 15), June → (6, 15), July → (7, 15), August → (8, 15),
- September → (9, 15), October → (10, 15), November → (11, 15), December → (12, 15)

User Intent Mapping:
- Specific dates ("May 12", "October 14") → use parsed numbers
- Seasons ("summer", "winter") → use season mapping
- Months ("December", "June") → use month mapping

=== 3. EVENT TYPE FILTERING ===
Column: holiday_occasion
Available Options: 4th of july, anniversary, baby shower, birthday, bridal shower, celebration of life, christmas, easter, engagement, fundraising, graduation, halloween, hanukkah, holiday, mother's day, new years, prom & homecoming, sympathy, thanksgiving, valentine's day, wedding

User Intent Mapping:
- "wedding" → WHERE LOWER(holiday_occasion) LIKE '%wedding%' AND holiday_occasion IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "valentine's day" → WHERE LOWER(holiday_occasion) LIKE '%valentine%' AND holiday_occasion IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "mother's day" → WHERE LOWER(holiday_occasion) LIKE '%mother%' AND holiday_occasion IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "birthday" → WHERE LOWER(holiday_occasion) LIKE '%birthday%' AND holiday_occasion IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "graduation" → WHERE LOWER(holiday_occasion) LIKE '%graduation%' AND holiday_occasion IS NOT NULL ORDER BY RANDOM() LIMIT 10

Special Cases:
- Valentine's Day queries: ALWAYS add "ORDER BY RANDOM() LIMIT 10"
- ALL queries must have ORDER BY RANDOM() LIMIT 10 to prevent token overflow

=== 4. EFFORT LEVEL FILTERING ===
Column: diy_level
Available Values: 'Ready To Go', 'DIY In A Kit', 'DIY From Scratch'

User Intent Mapping:
- "ready-made"/"no work"/"easy"/"low effort"/"pre-made" → WHERE diy_level = 'Ready To Go' AND diy_level IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "some DIY"/"kit"/"medium effort"/"partial assembly" → WHERE diy_level = 'DIY In A Kit' AND diy_level IS NOT NULL ORDER BY RANDOM() LIMIT 10
- "full DIY"/"from scratch"/"high effort"/"make myself" → WHERE diy_level = 'DIY From Scratch' AND diy_level IS NOT NULL ORDER BY RANDOM() LIMIT 10

=== 5. COLOR FILTERING ===
Columns: colors_raw (string), has_red, has_pink, has_white, has_yellow, has_orange, has_purple, has_blue, has_green (booleans)

CRITICAL: Handle AND vs OR logic correctly!

Multiple Colors with AND:
- if the user says they want "red and white" → WHERE has_red = true AND has_white = true AND colors_raw IS NOT NULL ORDER BY RANDOM() LIMIT 10

Multiple Colors with OR:
- if the user says they want "red or white" → WHERE (has_red = true OR has_white = true) AND colors_raw IS NOT NULL ORDER BY RANDOM() LIMIT 10

Single Color:
- "pink" → WHERE has_pink = true AND colors_raw IS NOT NULL ORDER BY RANDOM() LIMIT 10

Specific Color Names (not in boolean categories):
- "amber", "terracotta", "sage green" → WHERE LOWER(colors_raw) LIKE '%amber%' AND colors_raw IS NOT NULL ORDER BY RANDOM() LIMIT 10

=== 6. FLOWER TYPE FILTERING ===
Columns: group_category, subgroup_category, product_name, variant_name, product_type_all_flowers, recipe_metafield

Auto-format flower names (remove plurals):
- "roses" → "rose"
- "lilies" → "lily"
- "peonies" → "peony"
- "carnations" → "carnation"

User Intent Mapping:
- Specific flowers ("roses", "lily") → WHERE (LOWER(group_category) LIKE '%rose%' OR LOWER(recipe_metafield) LIKE '%rose%') AND (group_category IS NOT NULL OR recipe_metafield IS NOT NULL) ORDER BY RANDOM() LIMIT 10
- Product types ("bouquets", "centerpiece") → WHERE (LOWER(product_name) LIKE '%bouquet%' OR LOWER(product_type_all_flowers) LIKE '%bouquet%') AND (product_name IS NOT NULL OR product_type_all_flowers IS NOT NULL) ORDER BY RANDOM() LIMIT 10
- Quantity ("100 stems", "50 stems") → WHERE LOWER(variant_name) LIKE '%100%' AND variant_name IS NOT NULL ORDER BY RANDOM() LIMIT 10

=== QUERY CONSTRUCTION RULES ===
1. Always start with SELECT * FROM flowers
2. Apply filters using WHERE clauses with proper AND/OR logic
3. Add IS NOT NULL checks when user specifies preferences
4. ALWAYS ADD ORDER BY RANDOM() LIMIT 10
5. For date filtering, use structured season columns (no Python, no string parsing)

=== RESPONSE FORMATTING ===
For every matching product, display details in this order with these exact labels:

{n}. **Product Name**  
    Price: $X  
    Colors: ...  
    Effort Level: ...  
    Product Type: ...  
    Recipe: ...  
    Availability: ...  
    Description: ...  
    Occasions: ...

Formatting rules:
- Always present as a numbered list.
- Indent all attributes beneath the product name.
- Include all available fields (skip only if NULL).
- For availability: if year_round = TRUE, show "Year-round". Otherwise, format ranges like "Nov 15 – Feb 20".
- Start responses with a sentence explaining how many products were found (e.g., "Here are 7 flower products available in December:").
- If no results, suggest related alternatives or ask clarifying questions.
"""

# ---------------------------
# 4. Define LLM
# ---------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)

# ---------------------------
# 5. Create SQL Agent
# ---------------------------
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",
    verbose=True,
    max_iterations=10,
    return_intermediate_steps=True
)

# ---------------------------
# 6. Placeholder for user preferences
# ---------------------------
user_preferences = {}

# ---------------------------
# 7. Chatbot Loop
# ---------------------------
print("AI Flower Consultant ready! Type 'exit' to quit.")
print("Example queries:")
print("- 'I need red and white flowers for a wedding under $150'")
print("- 'Show me ready-made pink bouquets for Mother's Day'")
print("- 'What roses are available for Valentine's Day?'")
print("- 'I want DIY flowers for a summer graduation'")
print()

conversation_count = 0
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "q"]:
        break
    
    if not user_input.strip():
        print("Please enter a question about flowers!")
        continue

    try:
        conversation_count += 1
        print(f"\nProcessing query #{conversation_count}...")

        context_input = user_input
        enhanced_input = f"""{SYSTEM_PROMPT}

USER QUERY: {context_input}

Please help the user find flowers using the database query rules above and format results cleanly as specified."""
        
        response = agent_executor.invoke({"input": enhanced_input})

        if 'intermediate_steps' in response:
            print(f"Debug - Completed {len(response['intermediate_steps'])} steps")
        
        print(f"\nBot: {response['output']}\n")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please try rephrasing your question or ask for help with flower selection.")
        print()

print("Thank you for using the AI Flower Consultant!")
