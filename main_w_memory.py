import os
import csv
import json
from datetime import datetime
from collections import deque
from typing import List, Dict, Any, Optional

import pandas as pd
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
from langchain.prompts import PromptTemplate


class FlowerCatalogChat:
    """
    All-in-one chat agent for querying a flower product catalog DataFrame with:
      - Rolling chat memory injected into the prompt
      - CSV logging of every turn (question, final answer, compact tool traces)
      - Quick-query helpers (roses, longest vase life) to bypass the agent when possible

    Files:
      - Reads from CSV_PATH (or converts from EXCEL_PATH -> CSV_PATH on first run)
      - Writes logs to logs/chat_turns.csv

    Usage:
      bot = FlowerCatalogChat()
      bot.start_chat()  # launches a simple REPL
      # or programmatic:
      answer = bot.ask("How many unique product groups are there?")
    """

    def __init__(
        self,
        excel_path: str = "data/orders_history.xlsx",
        csv_path: str = "data/orders_history.csv",
        model: str = "gpt-4o-mini",
        temperature: float = 0.0,
        rolling_turns: int = 6,
        log_dir: str = "logs",
        log_filename: str = "chat_turns.csv",
    ):
        # --- Env / Keys ---
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")

        self.EXCEL_PATH = excel_path
        self.CSV_PATH = csv_path

        # --- DataFrame load (convert Excel -> CSV if needed) ---
        if not os.path.exists(self.CSV_PATH):
            if os.path.exists(self.EXCEL_PATH):
                df = pd.read_excel(self.EXCEL_PATH)
                os.makedirs(os.path.dirname(self.CSV_PATH), exist_ok=True)
                df.to_csv(self.CSV_PATH, index=False)
                print(f"Converted {self.EXCEL_PATH} to {self.CSV_PATH}")
            else:
                print(f"Warning: {self.EXCEL_PATH} not found. Creating empty DataFrame.")
                df = pd.DataFrame()
        else:
            df = pd.read_csv(self.CSV_PATH)

        self.df = df

        # --- LLM ---
        self.llm = ChatOpenAI(
            temperature=temperature,
            model=model,
            openai_api_key=api_key,
        )

        # --- Rolling memory ---
        self.rolling_memory = deque(maxlen=rolling_turns)

        # --- Logging ---
        self.LOG_DIR = log_dir
        self.LOG_PATH = os.path.join(log_dir, log_filename)
        os.makedirs(self.LOG_DIR, exist_ok=True)

        # --- Tools ---
        self.tools = [
            Tool(
                name="query_flower_data",
                func=lambda code: self._query_flower_data(code),
                description=(
                    "Execute Python code to analyze the flower products dataframe 'df'. "
                    "Use pandas operations like df.head(), df.info(), "
                    "df['Product name'].value_counts(), df.groupby('Group').size(), etc. "
                    "The dataframe has columns like 'Product name', 'Group', 'Subgroup', "
                    "'Colors (by semicolon)', possibly 'attributes.Expected Vase Life', etc."
                ),
            )
        ]

        # --- Prompt ---
        template = """You are a data analyst for a flower product catalog. Use tools when needed.
You will receive prior chat history to keep context across turns.

Prior conversation (may be empty):
{chat_history}

Available tools:
{tools}

Use this exact format:
Question: the input question you must answer
Thought: think about what to do
Action: the action to take, one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
(repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""
        self.prompt = PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad", "tools", "tool_names", "chat_history"],
        )

        # --- Agent + Executor (capture intermediate steps for logging) ---
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

        # --- Startup prints (optional) ---
        print(f"Loaded dataset with {len(self.df)} rows")
        if not self.df.empty:
            print(f"Columns: {list(self.df.columns)}")

    # -------------------------
    # Public API
    # -------------------------

    def ask(self, question: str) -> str:
        """
        Ask a question about the catalog. Returns the agent's final answer.
        Also logs the turn to logs/chat_turns.csv and updates rolling memory.
        """
        # Quick paths first to save tokens/time
        quick = self._maybe_quick_query(question)
        if quick is not None:
            answer = quick
            self._log_turn(question, answer, intermediate_steps=[])
            self._append_memory(question, answer)
            return answer

        # Full agent path
        response = self.agent_executor.invoke({
            "input": question,
            "chat_history": self._format_chat_history(self.rolling_memory),
        })
        answer = (response.get("output") or "").strip()
        intermediate = response.get("intermediate_steps", [])
        self._log_turn(question, answer, intermediate)
        self._append_memory(question, answer)
        return answer

    def start_chat(self) -> None:
        """
        Simple REPL loop. Type 'quit' or 'exit' to leave.
        """
        print("\n🌸 Flower Product Catalog Chatbot (type 'quit' to exit) 🌸")
        print("I can help you analyze your flower product catalog data!")
        print("Example queries:")
        print("- How many different flower products do we have?")
        print("- What are the most common product groups?")
        print("- Show me products that are seasonal")
        print("- What flower types are available in red colors?")
        print("-" * 60)

        while True:
            try:
                q = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye! 🌺")
                break

            if q.lower() in {"quit", "exit"}:
                print("Goodbye! 🌺")
                break

            try:
                a = self.ask(q)
                print("Bot:", a)
            except Exception as e:
                print(f"Error: {e}")
                print("Please try rephrasing your question or check if your data file exists.")

    # -------------------------
    # Internals
    # -------------------------

    def _maybe_quick_query(self, query: str) -> Optional[str]:
        """
        Fast-path for common requests that don't need the agent.
        """
        q = query.lower()

        # Example: show or find roses
        if "rose" in q and ("show" in q or "find" in q):
            try:
                result = self.df[self.df['Product name'].str.contains('rose', case=False, na=False)]
                if len(result) > 0:
                    sample = result[['Product name', 'Colors (by semicolon)']].head(5)
                    return f"Found {len(result)} products with 'rose' in the name:\n{sample.to_string(index=False)}"
                return "No products found with 'rose' in the name."
            except Exception as e:
                return f"Quick query error (roses): {e}"

        # Example: longest vase life
        if "vase life" in q and "longest" in q:
            try:
                col = 'attributes.Expected Vase Life'
                if col in self.df.columns:
                    valid = self.df[self.df[col].notna()]
                    if len(valid) > 0:
                        row = valid.loc[valid[col].idxmax()]
                        return f"Product with longest vase life:\nName: {row['Product name']}\nVase Life: {row[col]}"
                    return "No vase life data available."
                return "Vase life column not found in the dataset."
            except Exception as e:
                return f"Quick query error (vase life): {e}"

        return None

    def _query_flower_data(self, code: str) -> str:
        """
        Executes Python against the in-memory DataFrame.
        Safely exposes: df, pd, np, and common builtins like len, print, etc.
        Returns captured stdout or a helpful fallback.
        """
        try:
            import io
            import sys
            import numpy as np
            from contextlib import redirect_stdout, redirect_stderr

            # Locals available to user code
            local_vars = {
                "df": self.df,
                "pd": pd,
                "np": np,
                "len": len,
                "print": print,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "sum": sum,
                "max": max,
                "min": min,
                "sorted": sorted,
            }

            code = (code or "").strip()
            if code.startswith('"') and code.endswith('"'):
                code = code[1:-1]
            if code.startswith("'") and code.endswith("'"):
                code = code[1:-1]

            out_buf = io.StringIO()
            err_buf = io.StringIO()

            with redirect_stdout(out_buf), redirect_stderr(err_buf):
                try:
                    # If it's a simple expression with no assignments/flow
                    bad_keywords = ['import', 'def', 'class', 'for', 'while', 'if', 'elif', 'else', '=', 'del', 'global', 'nonlocal']
                    if not any(k in code.lower() for k in bad_keywords):
                        result = eval(code, {"__builtins__": local_vars}, local_vars)
                        if result is not None:
                            if hasattr(result, 'to_string'):
                                print(result.to_string())
                            elif hasattr(result, '__iter__') and not isinstance(result, str):
                                result_list = list(result)
                                if len(result_list) > 10:
                                    print(f"First 10 items: {result_list[:10]}")
                                    print(f"... (showing 10 of {len(result_list)} total items)")
                                else:
                                    print(result_list)
                            else:
                                print(result)
                    else:
                        exec(code, {"__builtins__": local_vars}, local_vars)
                except Exception as e:
                    print(f"Execution error: {e}")

            stdout_output = out_buf.getvalue()
            stderr_output = err_buf.getvalue()

            if not stdout_output.strip() and not stderr_output.strip():
                try:
                    if not self.df.empty and "Product name" in self.df.columns:
                        stdout_output = "No direct output. Showing product names:\n" + self.df["Product name"].to_string(index=False)
                except Exception:
                    pass

            if stderr_output:
                return f"Error: {stderr_output.strip()}"
            if stdout_output.strip():
                return stdout_output.strip()
            return "Code executed successfully (no output to display)"

        except Exception as e:
            return f"Tool error: {e}"

    def _append_memory(self, q: str, a: str) -> None:
        self.rolling_memory.append({"q": q, "a": a})

    @staticmethod
    def _format_chat_history(memory_deque: deque) -> str:
        if not memory_deque:
            return "None"
        lines: List[str] = []
        for turn in memory_deque:
            lines.append(f"Human: {turn['q']}")
            lines.append(f"AI: {turn['a']}")
        return "\n".join(lines)

    def _log_turn(self, question: str, answer: str, intermediate_steps: Any) -> None:
        """
        Append a row: timestamp, question, final_answer, tool_trace_json
        """
        trace = self._compact_trace(intermediate_steps)
        write_header = not os.path.exists(self.LOG_PATH)
        with open(self.LOG_PATH, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if write_header:
                w.writerow(["timestamp", "question", "final_answer", "tool_trace_json"])
            w.writerow([
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                question,
                answer,
                json.dumps(trace, ensure_ascii=False),
            ])

    @staticmethod
    def _compact_trace(intermediate_steps: Any) -> List[Dict[str, Any]]:
        """
        Turn LangChain intermediate_steps into a concise JSON-friendly list.
        Typically each item is a (AgentAction, observation) pair.
        """
        out: List[Dict[str, Any]] = []
        try:
            for step in intermediate_steps or []:
                action = None
                observation = None
                if isinstance(step, (list, tuple)) and len(step) == 2:
                    action, observation = step
                else:
                    # Unknown shape; stringify
                    out.append({"raw": str(step)[:500]})
                    continue

                tool_name = getattr(action, "tool", getattr(action, "tool_name", "unknown"))
                tool_input = getattr(action, "tool_input", None)
                out.append({
                    "tool": tool_name,
                    "tool_input": tool_input,
                    "observation_preview": (str(observation)[:500] if observation is not None else None),
                })
        except Exception as e:
            out.append({"parse_error": str(e)[:200]})
        return out


# Optional: quick CLI if you run this file directly
if __name__ == "__main__":
    bot = FlowerCatalogChat()
    bot.start_chat()