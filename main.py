import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain_experimental.tools import PythonREPLTool
from langchain.tools import Tool
from langchain import hub
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")

EXCEL_PATH = "data/orders_history.xlsx"
CSV_PATH = "data/orders_history.csv"

# Convert Excel to CSV if needed
if not os.path.exists(CSV_PATH):
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH)
        df.to_csv(CSV_PATH, index=False)
        print(f"Converted {EXCEL_PATH} to {CSV_PATH}")
    else:
        print(f"Warning: {EXCEL_PATH} not found. Creating empty DataFrame.")
        df = pd.DataFrame()
else:
    df = pd.read_csv(CSV_PATH)

print(f"Loaded dataset with {len(df)} rows")
if not df.empty:
    print(f"Columns: {list(df.columns)}")

# Create LLM
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4o-mini",
    openai_api_key=api_key
)

# Create a standard Python REPL tool
python_repl = PythonREPLTool()

# Create a comprehensive data analysis tool
def query_flower_data(code: str):
    """
    Execute Python code to analyze the flower products dataframe.
    The dataframe 'df' contains flower product data with detailed attributes.
    Available variables: df (pandas DataFrame), pd (pandas module)
    Example usage: df.head(), df['Product name'].value_counts(), df.groupby('Group').size()
    """
    try:
        # Import necessary modules for the execution environment
        import io
        import sys
        from contextlib import redirect_stdout, redirect_stderr
        import pandas as pd
        
        # Create execution environment with the dataframe available
        local_vars = {"df": df, "pd": pd, "len": len, "print": print}
        
        # Capture both stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            try:
                # Try to evaluate as expression first (for simple queries)
                if not any(keyword in code.lower() for keyword in ['import', 'def', 'class', 'for', 'while', 'if', 'elif', 'else', '=', 'del', 'global', 'nonlocal']):
                    result = eval(code, {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict, "set": set, "tuple": tuple, "sum": sum, "max": max, "min": min, "sorted": sorted}}, local_vars)
                    if result is not None:
                        print(result)
                else:
                    # Execute as statement
                    exec(code, {"__builtins__": {"len": len, "str": str, "int": int, "float": float, "list": list, "dict": dict, "set": set, "tuple": tuple, "sum": sum, "max": max, "min": min, "sorted": sorted, "print": print}}, local_vars)
            except Exception as e:
                print(f"Execution error: {str(e)}")
        
        # Get captured output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        if stderr_output:
            return f"Error: {stderr_output}"
        elif stdout_output.strip():
            return stdout_output.strip()
        else:
            return "Code executed successfully (no output to display)"
            
    except Exception as e:
        return f"Tool error: {str(e)}"

# Create tools list - using just the custom tool for better control
tools = [
    Tool(
        name="query_flower_data", 
        func=query_flower_data,
        description="Execute Python code to analyze the flower products dataframe 'df'. Use pandas operations like df.head(), df.info(), df['Product name'].value_counts(), df.groupby('Group').size(), etc. The dataframe has columns like 'Product name', 'Group', 'Subgroup', 'Colors (by semicolon)', etc."
    )
]

# Get the react prompt template
try:
    prompt = hub.pull("hwchase17/react")
except Exception:
    # Fallback prompt if hub is not available
    from langchain.prompts import PromptTemplate
    
    template = """Answer the following questions as best you can about the flower order data. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

    prompt = PromptTemplate(
        template=template,
        input_variables=["input", "agent_scratchpad", "tools", "tool_names"]
    )

# Create the agent
agent = create_react_agent(llm, tools, prompt)

# Create the agent executor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    max_iterations=5,
    handle_parsing_errors=True
)

print("\n🌸 Flower Product Catalog Chatbot (type 'quit' to exit) 🌸")
print("I can help you analyze your flower product catalog data!")
print("Example queries:")
print("- How many different flower products do we have?")
print("- What are the most common product groups?")
print("- Show me products that are seasonal")
print("- What flower types are available in red colors?")
print("-" * 60)

while True:
    query = input("\nYou: ")
    if query.lower() in ["quit", "exit"]:
        print("Goodbye! 🌺")
        break
    
    try:
        response = agent_executor.invoke({"input": query})
        print("Bot:", response["output"])
    except Exception as e:
        print(f"Error: {e}")
        print("Please try rephrasing your question or check if your data file exists.")