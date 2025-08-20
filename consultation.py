import os
import csv
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# -------------------------
# Helpers: parsing & vocab
# -------------------------

COLOR_VOCAB = {
    "white", "ivory", "cream", "blush", "pink", "peach", "coral", "red",
    "burgundy", "wine", "orange", "yellow", "gold", "green", "olive", "sage",
    "mint", "blue", "navy", "lavender", "purple", "black", "brown", "rust",
    "terracotta"
}

FLOWER_VOCAB = {
    "rose", "ranunculus", "peony", "tulip", "lily", "dahlia", "carnation",
    "anemone", "hydrangea", "orchid", "sunflower", "daisy", "stock",
    "eucalyptus", "baby's breath", "gypsophila"
}

OCCASIONS = [
    "wedding", "birthday", "anniversary", "funeral", "graduation", "baby shower",
    "bridal shower", "prom", "homecoming", "valentine's", "valentine",
    "mother's day", "christmas", "thanksgiving", "easter", "holiday",
    "party", "celebration", "sympathy"
]

EFFORT_TYPES = [
    "diy", "diy flower kits", "focal flowers", "centerpieces", "bouquets",
    "arrangements", "premade", "ready-made", "custom"
]


def _parse_event_date(text: str) -> Optional[str]:
    """
    Returns ISO 'YYYY-MM-DD' or None. Handles:
    - 09/21/2025, 2025-09-21, Sep 21, Sept 21 2025, etc.
    - today, tomorrow
    - this <weekday>
    """
    t = text.lower().strip()
    today = pd.Timestamp.today().normalize()

    # quick words
    if re.search(r"\btoday\b", t):
        return today.strftime("%Y-%m-%d")
    if re.search(r"\btomorrow\b", t):
        return (today + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    # "this saturday"
    m = re.search(r"\bthis\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", t)
    if m:
        wd_map = dict(monday=0, tuesday=1, wednesday=2, thursday=3, friday=4, saturday=5, sunday=6)
        target = wd_map[m.group(1)]
        delta = (target - today.weekday()) % 7
        return (today + pd.Timedelta(days=delta)).strftime("%Y-%m-%d")

    # general parse
    try:
        parsed = pd.to_datetime(text, errors="coerce", utc=False)
        if pd.notnull(parsed):
            return parsed.date().isoformat()
    except Exception:
        pass
    return None


def _season_from_iso(iso_date: str) -> str:
    month = int(iso_date.split("-")[1])
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10, 11):
        return "fall"
    return "winter"


def _extract_occasion(text: str) -> Optional[str]:
    """Extract occasion from text (wedding, birthday, etc.)"""
    t = text.lower()
    # prefer multi-word occasions first
    for occ in sorted(OCCASIONS, key=len, reverse=True):
        if occ in t:
            if occ == "valentine":
                return "valentine's"
            return occ
    return None


def _extract_effort_type(text: str) -> Optional[str]:
    """Extract effort/product type from text (DIY, bouquets, etc.)"""
    t = text.lower()
    
    # Check for specific mentions
    if any(word in t for word in ["diy", "do it myself", "make myself", "assemble"]):
        return "diy flower kits"
    if any(word in t for word in ["bouquet", "bouquets"]):
        return "bouquets"
    if any(word in t for word in ["centerpiece", "centerpieces"]):
        return "centerpieces"
    if any(word in t for word in ["focal", "statement"]):
        return "focal flowers"
    if any(word in t for word in ["arrangement", "arrangements", "premade", "ready"]):
        return "arrangements"
    
    # Direct matches
    for effort in EFFORT_TYPES:
        if effort in t:
            return effort
    
    return None


def _extract_prefs(text: str) -> Tuple[List[str], List[str]]:
    t = text.lower()

    # colors
    colors = [c for c in COLOR_VOCAB if re.search(rf"\b{re.escape(c)}\b", t)]
    if "blush pink" in t and "blush" not in colors:
        colors.append("blush")

    # flowers
    flowers = []
    for f in FLOWER_VOCAB:
        if re.search(rf"\b{re.escape(f)}\b", t):
            flowers.append(f)
    return sorted(set(colors)), sorted(set(flowers))


# -------------------------
# Main class
# -------------------------

class FlowerConsultantChat:
    """
    Flower consultant chatbot that gathers user information in a structured way:
    1. Occasion (wedding, birthday, etc.)
    2. Event date (optional - can skip)
    3. Theme (optional - general style/aesthetic)
    4. Effort level (DIY, bouquets, centerpieces, etc.)
    5. Additional preferences (colors, specific flowers, etc.)

    Then filters the product catalog and provides 5 recommendations.
    """

    def __init__(
        self,
        excel_path: str = "data/orders_history.xlsx",
        csv_path: str = "data/orders_history.csv",
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        log_dir: str = "logs",
        log_filename: str = "consultation_logs.csv",
    ):
        # --- Env / Keys ---
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")

        self.EXCEL_PATH = excel_path
        self.CSV_PATH = csv_path

        # --- DataFrame load ---
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

        # --- LLM (optional for chitchat) ---
        self.llm = ChatOpenAI(
            temperature=temperature,
            model=model,
            openai_api_key=api_key,
        )

        # --- Consultation State & logs ---
        self.reset_consultation()

        self.LOG_DIR = log_dir
        self.LOG_PATH = os.path.join(log_dir, log_filename)
        os.makedirs(self.LOG_DIR, exist_ok=True)

        print(f"🌸 Flower Consultant loaded with {len(self.df)} products")
        if not self.df.empty:
            print(f"Available columns: {list(self.df.columns)}")

    # -------------------------
    # Public API
    # -------------------------

    def reset_consultation(self):
        """Reset consultation state for a new customer."""
        self.consultation_state = {
            "occasion": None,         # wedding, birthday, etc.
            "event_date": None,       # ISO string YYYY-MM-DD (optional)
            "season": None,           # spring/summer/fall/winter (if date provided)
            "theme": None,            # general style/aesthetic (optional)
            "effort_type": None,      # DIY, bouquets, centerpieces, etc.
            "preferences": {"colors": [], "flowers": [], "raw": ""},
            "phase": "greeting",      # greeting -> occasion -> date -> theme -> effort -> preferences -> recommendations
            "selected_product": None, # For tracking delivery date recommendations
        }
        self.chat_history: List[Dict[str, str]] = []

    def ask(self, message: str) -> str:
        """
        Process user message and return consultant response.
        Manages consultation state and progression.
        """
        # Update consultation state based on message
        self._update_state_from_message(message)

        phase = self.consultation_state["phase"]

        if phase == "greeting":
            self.consultation_state["phase"] = "occasion"
            return ("Hi there! I'd love to help you find the perfect flowers. "
                    "What's the occasion? (e.g., wedding, birthday, anniversary, holiday, etc.)")

        elif phase == "occasion":
            if not self.consultation_state["occasion"]:
                return "What's the occasion? (e.g., wedding, birthday, anniversary, holiday, etc.)"
            else:
                occ = self.consultation_state["occasion"]
                self.consultation_state["phase"] = "date"
                return (f"A {occ} — wonderful! Do you have a specific date in mind? "
                        "(e.g., 09/21/2025, Sep 21, 'today', 'this Saturday', or say 'no date yet' to skip)")

        elif phase == "date":
            # Date is optional, so we move on regardless
            self.consultation_state["phase"] = "theme"
            if self.consultation_state["event_date"]:
                d = self.consultation_state['event_date']
                s = self.consultation_state['season']
                return (f"Perfect — {d} ({s}). Do you have a particular theme or style in mind? "
                        "(e.g., rustic, elegant, modern, bohemian, or say 'no theme' to skip)")
            else:
                return ("No problem! Do you have a particular theme or style in mind? "
                        "(e.g., rustic, elegant, modern, bohemian, or say 'no theme' to skip)")

        elif phase == "theme":
            # Theme is optional, move to effort level
            self.consultation_state["phase"] = "effort"
            return ("What kind of flower arrangement are you looking for? "
                    "(e.g., DIY flower kits, ready-made bouquets, centerpieces, focal flowers, or custom arrangements)")

        elif phase == "effort":
            if not self.consultation_state["effort_type"]:
                return ("What kind of flower arrangement are you looking for? "
                        "(e.g., DIY flower kits, ready-made bouquets, centerpieces, focal flowers, or custom arrangements)")
            else:
                effort = self.consultation_state["effort_type"]
                self.consultation_state["phase"] = "preferences"
                return (f"Great choice with {effort}! Any preferences for colors or specific flowers? "
                        "You can say 'no preference' if you're open to anything.")

        elif phase == "preferences":
            prefs = self.consultation_state["preferences"]
            if not prefs["colors"] and not prefs["flowers"] and prefs["raw"] == "":
                return ("Any color palette you love (e.g., blush & white) or specific flowers "
                        "(e.g., roses, ranunculus)? You can say 'no preference'.")
            else:
                # We have enough info; move to recommendations
                self.consultation_state["phase"] = "recommendations"
                return self._get_recommendations()

        elif phase == "recommendations":
            return self._get_recommendations()

        # Fallback: try LLM small talk while nudging next step
        return self._get_conversational_response(message)

    def get_delivery_recommendation(self, product_name: str) -> str:
        """Get delivery date recommendation for a selected product."""
        if self.df.empty:
            return "I don't have delivery information available right now."
        
        # Find the product
        product_match = self.df[self.df.get("Product name", "").str.lower().str.contains(
            product_name.lower(), na=False
        )]
        
        if product_match.empty:
            return "I couldn't find that specific product for delivery timing."
        
        # Get recommended delivery date
        delivery_col = "attributes.Recommended Delivery Date"
        if delivery_col in self.df.columns:
            delivery_info = product_match.iloc[0].get(delivery_col, "")
            if delivery_info and str(delivery_info) != "nan":
                return f"For {product_name}, I recommend ordering by {delivery_info} to ensure timely delivery."
        
        return "I don't have specific delivery timing for this product, but I'd recommend ordering at least 3-5 days in advance."

    def start_consultation(self):
        """Start interactive consultation session."""
        print("\n🌸 Welcome to our Flower Consultation Service! 🌸")
        print("I'm here to help you find the perfect flowers for your special occasion.")
        print("Type 'quit' to exit or 'restart' to begin a new consultation.\n")

        # Initial prompt
        first = self.ask("")  # triggers greeting->occasion prompt
        print(f"Consultant: {first}")

        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\nThank you for using our consultation service! 🌺")
                break

            if user_input.lower() in ["quit", "exit"]:
                print("Thank you for using our consultation service! 🌺")
                break
            elif user_input.lower() == "restart":
                self.reset_consultation()
                print("\n--- New Consultation Started ---")
                print(f"Consultant: {self.ask('')}")
                continue

            if not user_input:
                continue

            try:
                response = self.ask(user_input)
                print(f"Consultant: {response}")

                # Log turn
                self._log_consultation_turn(user_input, response)

                # If consultation is complete, allow restart or delivery questions
                if self.consultation_state["phase"] == "recommendations":
                    print("\n--- Consultation Complete ---")
                    print("Would you like delivery timing for any of these options? Just mention the product name!")
                    print("Or type 'restart' for a new consultation or 'quit' to exit.")

            except Exception as e:
                print(f"I apologize for the technical difficulty: {e}")
                print("Please try again or type 'restart' for a fresh consultation.")

    # -------------------------
    # Conversation helpers
    # -------------------------

    def _get_conversational_response(self, message: str) -> str:
        """Generate a conversational response using LLM without tools."""
        try:
            simple_prompt = f"""You are a friendly flower consultant. Respond naturally and keep guiding the user to the next step.

Current state:
- Occasion: {self.consultation_state["occasion"]}
- Event Date: {self.consultation_state["event_date"]}
- Season: {self.consultation_state["season"]}
- Theme: {self.consultation_state["theme"]}
- Effort Type: {self.consultation_state["effort_type"]}
- Preferences: {self.consultation_state["preferences"]}
- Phase: {self.consultation_state["phase"]}

User just said: {message}

Your goal: friendly, concise guidance to the next required detail."""
            response = self.llm.invoke(simple_prompt)
            return response.content.strip()
        except Exception:
            # Minimal fallback guidance
            phase = self.consultation_state["phase"]
            if phase == "occasion":
                return "What's the occasion? (e.g., wedding, birthday, anniversary, holiday, etc.)"
            if phase == "date":
                return "Do you have a specific date? (e.g., 09/21/2025, Sep 21, 'today', or 'no date yet')"
            if phase == "theme":
                return "Any particular theme or style? (e.g., rustic, elegant, modern, or 'no theme')"
            if phase == "effort":
                return "What kind of arrangement? (DIY kits, bouquets, centerpieces, etc.)"
            if phase == "preferences":
                return "Any colors or specific flowers you love? You can say 'no preference'."
            return "How can I help with your event flowers?"

    # -------------------------
    # State updates & parsing
    # -------------------------

    def _update_state_from_message(self, message: str):
        """Extract information from user message and update consultation state."""
        msg_lower = message.lower().strip()
        phase = self.consultation_state["phase"]

        # Check for "skip" phrases for optional fields
        skip_phrases = ["no date", "don't know", "not sure", "skip", "no theme", "no specific"]
        is_skip = any(phrase in msg_lower for phrase in skip_phrases)

        # Occasion
        if phase in ["greeting", "occasion"]:
            occ = _extract_occasion(message)
            if occ:
                self.consultation_state["occasion"] = occ
                self.consultation_state["phase"] = "date"
                return

        # Event date (optional)
        if phase == "date":
            if is_skip:
                self.consultation_state["phase"] = "theme"
                return
            
            iso = _parse_event_date(message)
            if iso:
                self.consultation_state["event_date"] = iso
                self.consultation_state["season"] = _season_from_iso(iso)
                self.consultation_state["phase"] = "theme"
                return
            else:
                # If no date found, still move on since it's optional
                self.consultation_state["phase"] = "theme"
                return

        # Theme (optional)
        if phase == "theme":
            if is_skip:
                self.consultation_state["phase"] = "effort"
                return
            
            # Store theme as raw text for now since we're not sure what themes look like
            if message.lower() not in ["no theme", "none", "skip"]:
                self.consultation_state["theme"] = message.strip()
            self.consultation_state["phase"] = "effort"
            return

        # Effort type
        if phase == "effort":
            effort = _extract_effort_type(message)
            if effort:
                self.consultation_state["effort_type"] = effort
                self.consultation_state["phase"] = "preferences"
                return

        # Preferences
        if phase == "preferences":
            if "no preference" in msg_lower or "anything" in msg_lower:
                self.consultation_state["preferences"] = {"colors": [], "flowers": [], "raw": message}
                # proceed to recs if we have minimum requirements
                if self.consultation_state["occasion"] and self.consultation_state["effort_type"]:
                    self.consultation_state["phase"] = "recommendations"
                return

            colors, flowers = _extract_prefs(message)
            prefs = self.consultation_state["preferences"]
            prefs["colors"] = sorted(set(prefs.get("colors", []) + colors))
            prefs["flowers"] = sorted(set(prefs.get("flowers", []) + flowers))
            prefs["raw"] = message

            # proceed to recs if we have minimum requirements
            if self.consultation_state["occasion"] and self.consultation_state["effort_type"]:
                self.consultation_state["phase"] = "recommendations"
            return

        # If user voluntarily provides missing info earlier than asked:
        if not self.consultation_state["occasion"]:
            occ = _extract_occasion(message)
            if occ:
                self.consultation_state["occasion"] = occ
        if not self.consultation_state["event_date"] and phase != "date":
            iso = _parse_event_date(message)
            if iso:
                self.consultation_state["event_date"] = iso
                self.consultation_state["season"] = _season_from_iso(iso)
        if not self.consultation_state["effort_type"]:
            effort = _extract_effort_type(message)
            if effort:
                self.consultation_state["effort_type"] = effort

        # Always check for preferences if we're past the preferences phase
        if phase in ["preferences", "recommendations"]:
            colors, flowers = _extract_prefs(message)
            if colors or flowers:
                prefs = self.consultation_state["preferences"]
                prefs["colors"] = sorted(set(prefs.get("colors", []) + colors))
                prefs["flowers"] = sorted(set(prefs.get("flowers", []) + flowers))
                prefs["raw"] = message

    # -------------------------
    # Catalog filtering & recs
    # -------------------------

    def _safe_get_column(self, df: pd.DataFrame, col_name: str, default: str = "") -> pd.Series:
        """Safely get a column from DataFrame, returning empty strings if column doesn't exist."""
        if col_name in df.columns:
            return df[col_name].fillna("").astype(str)
        else:
            return pd.Series(default, index=df.index, dtype=str)

    def _normalized_catalog(self) -> pd.DataFrame:
        """Create normalized catalog with safe column access."""
        df = self.df.copy()
        if df.empty:
            return df
        
        # Use safe column access to avoid the 'str' object has no attribute 'astype' error
        df["__name"] = self._safe_get_column(df, "Product name").str.lower()
        
        # Try multiple column names for colors
        colors_col = None
        for col in ["Colors (by semicolon)", "Colors", "Color"]:
            if col in df.columns:
                colors_col = col
                break
        df["__colors"] = self._safe_get_column(df, colors_col).str.lower()
        
        # Try multiple column names for group/category
        group_col = None
        for col in ["Group", "Category", "Occasion"]:
            if col in df.columns:
                group_col = col
                break
        df["__group"] = self._safe_get_column(df, group_col).str.lower()
        
        df["__season"] = self._safe_get_column(df, "Season").str.lower()
        df["__product_type"] = self._safe_get_column(df, "attributes.Product Type").str.lower()
        
        return df

    def _filter_catalog(self) -> pd.DataFrame:
        d0 = self._normalized_catalog()
        if d0.empty:
            return d0

        wants = self.consultation_state
        colors = wants["preferences"].get("colors", [])
        flowers = wants["preferences"].get("flowers", [])
        occasion = wants["occasion"]
        season = wants["season"]
        effort_type = wants["effort_type"]

        def apply(d, use_occasion=True, use_color=True, use_flower=True, use_season=True, use_effort=True):
            m = pd.Series(True, index=d.index)
            if use_occasion and occasion:
                m &= d["__group"].str.contains(occasion, na=False) | d["__name"].str.contains(occasion, na=False)
            if use_color and colors:
                m &= d["__colors"].apply(lambda s: any(c in s for c in colors))
            if use_flower and flowers:
                m &= d["__name"].apply(lambda s: any(f in s for f in flowers))
            if use_season and season:
                m &= d["__season"].str.contains(season, na=False)
            if use_effort and effort_type:
                m &= d["__product_type"].str.contains(effort_type.replace(" ", ""), na=False)
            return d[m]

        attempts = [
            dict(use_occasion=True,  use_color=True,  use_flower=True,  use_season=True,  use_effort=True),
            dict(use_occasion=True,  use_color=True,  use_flower=True,  use_season=False, use_effort=True),
            dict(use_occasion=True,  use_color=True,  use_flower=False, use_season=False, use_effort=True),
            dict(use_occasion=True,  use_color=False, use_flower=False, use_season=False, use_effort=True),
            dict(use_occasion=False, use_color=True,  use_flower=True,  use_season=False, use_effort=True),
            dict(use_occasion=False, use_color=True,  use_flower=False, use_season=False, use_effort=True),
            dict(use_occasion=False, use_color=False, use_flower=True,  use_season=False, use_effort=True),
            dict(use_occasion=False, use_color=False, use_flower=False, use_season=False, use_effort=True),
            dict(use_occasion=True,  use_color=False, use_flower=False, use_season=False, use_effort=False),
            dict(use_occasion=False, use_color=False, use_flower=False, use_season=False, use_effort=False),
        ]

        for rule in attempts:
            out = apply(d0, **rule)
            if len(out) > 0:
                return out

        return d0  # absolute fallback

    def _get_recommendations(self) -> str:
        filtered_df = self._filter_catalog()

        if filtered_df.empty:
            return ("I couldn't find matching items in the catalog yet. "
                    "Want me to broaden the color, flower, or arrangement type preferences?")

        k = min(5, len(filtered_df))
        picks = filtered_df.sample(k, random_state=None)

        d = self.consultation_state
        occasion_text = f"**{d['occasion']}**" if d['occasion'] else "your event"
        effort_text = f" with **{d['effort_type']}**" if d['effort_type'] else ""
        season_text = f" in **{d['season']}**" if d['season'] else ""
        
        header = f"Based on your {occasion_text}{effort_text}{season_text}, here are {k} lovely picks:\n"
        lines = [header]

        def fmt_price(v):
            try:
                return f"${float(v):.2f}"
            except Exception:
                return str(v) if v not in (None, "", "nan") else "Contact for pricing"

        for i, (_, row) in enumerate(picks.iterrows(), 1):
            name = row.get("Product name", "Beautiful Arrangement")
            group = row.get("Group") or row.get("Category") or ""
            colors = (row.get("Colors (by semicolon)")
                      or row.get("Colors")
                      or row.get("Color")
                      or "")
            price = fmt_price(row.get("Price"))
            product_type = row.get("attributes.Product Type", "")

            block = [f"{i}. **{name}**" + (f" ({group})" if group else "")]
            if product_type:
                block.append(f"   • Type: {product_type}")
            if colors:
                block.append(f"   • Colors: {colors}")
            if price:
                block.append(f"   • Price: {price}")
            lines.append("\n".join(block))

        lines.append("\nWould you like delivery timing for any of these, or should I adjust the preferences?")
        text = "\n\n".join(lines)

        # Log the completed recommendations turn
        self._log_consultation_turn("RECOMMENDATIONS_GENERATED", text)

        return text

    # -------------------------
    # Logging & history
    # -------------------------

    def _format_chat_history(self) -> str:
        if not self.chat_history:
            return "No previous conversation."
        formatted = []
        for turn in self.chat_history[-3:]:
            formatted.append(f"Human: {turn['human']}")
            formatted.append(f"AI: {turn['ai']}")
        return "\n".join(formatted)

    def _log_consultation_turn(self, user_message: str, bot_response: str):
        """Log each turn of the consultation."""
        write_header = not os.path.exists(self.LOG_PATH)

        with open(self.LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp", "user_message", "bot_response", "phase",
                    "occasion", "event_date", "season", "theme", "effort_type", "preferences_json"
                ])

            writer.writerow([
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                user_message,
                bot_response,
                self.consultation_state["phase"],
                self.consultation_state["occasion"],
                self.consultation_state["event_date"],
                self.consultation_state["season"],
                self.consultation_state["theme"],
                self.consultation_state["effort_type"],
                json.dumps(self.consultation_state["preferences"], ensure_ascii=False)
            ])


# -------------------------
# CLI entry point
# -------------------------

if __name__ == "__main__":
    consultant = FlowerConsultantChat()
    consultant.start_consultation()

