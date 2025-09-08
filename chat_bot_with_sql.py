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
# 3. Define LLM
# ---------------------------
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

# ---------------------------
# 4. Create SQL Agent (new style)
# ---------------------------
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",  # modern agent type
    verbose=True,
)

# ---------------------------
# 5. Add memory for conversation
# ---------------------------
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# ---------------------------
# 6. Run chatbot loop
# ---------------------------
print("💐 AI Flower Consultant ready! Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "q"]:
        break

    try:
        response = agent_executor.invoke({"input": user_input})
        print(f"Bot: {response['output']}\n")
    except Exception as e:
        print(f"⚠️ Error: {e}")
