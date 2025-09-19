import os
import json
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

# ---------------------------
# 1. Enhanced Configuration
# ---------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# 2. Data Structures
# ---------------------------
class ConversationState(Enum):
    GREETING = "greeting"
    GATHERING_INFO = "gathering_info"
    SHOWING_RESULTS = "showing_results"
    REFINING_SEARCH = "refining_search"
    CLOSING = "closing"

@dataclass
class UserRequirements:
    """Store user requirements throughout the conversation"""
    event_type: Optional[str] = None
    event_date: Optional[datetime] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    colors: List[str] = field(default_factory=list)
    diy_level: Optional[str] = None
    flower_types: List[str] = field(default_factory=list)
    guest_count: Optional[int] = None
    specific_needs: List[str] = field(default_factory=list)
    
    def is_complete(self) -> bool:
        """Check if we have minimum required info for recommendations"""
        return bool(self.event_type and (self.event_date or self.budget_max))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for SQL query generation"""
        return {
            'event_type': self.event_type,
            'event_date': self.event_date.strftime('%Y-%m-%d') if self.event_date else None,
            'budget_min': self.budget_min,
            'budget_max': self.budget_max,
            'colors': self.colors,
            'diy_level': self.diy_level,
            'flower_types': self.flower_types,
            'guest_count': self.guest_count,
            'specific_needs': self.specific_needs
        }

# ---------------------------
# 3. Enhanced Flower Consultant Class
# ---------------------------
class EnhancedFlowerConsultant:
    def __init__(self, db_uri: str, openai_api_key: str):
        # Database and LLM setup
        self.db = SQLDatabase.from_uri(db_uri)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3, openai_api_key=openai_api_key)
        
        # SQL Agent for database queries
        self.sql_agent = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type="openai-tools",
            verbose=True,
        )
        
        # Conversation management
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.state = ConversationState.GREETING
        self.requirements = UserRequirements()
        
        # Load reference data
        self.load_reference_data()
        
        # Create specialized prompts
        self.setup_prompts()
    
    def load_reference_data(self):
        """Load color mappings and other reference data"""
        try:
            # Load color mapping (create if doesn't exist)
            if os.path.exists('color_mapping.json'):
                with open('color_mapping.json', 'r') as f:
                    self.color_mapping = json.load(f)
            else:
                # Fallback color mapping
                self.color_mapping = {
                    "red": ["red", "crimson", "burgundy", "maroon", "scarlet"],
                    "white": ["white", "ivory", "cream", "pearl"],
                    "pink": ["pink", "blush", "rose", "salmon", "coral"],
                    "blue": ["blue", "navy", "royal blue", "powder blue"],
                    "purple": ["purple", "lavender", "violet", "plum"],
                    "yellow": ["yellow", "golden", "sunflower", "lemon"],
                    "orange": ["orange", "peach", "tangerine", "amber"],
                    "green": ["green", "sage", "eucalyptus", "mint"]
                }
            
            # Event types
            self.event_types = [
                "wedding", "birthday", "anniversary", "funeral", "corporate event",
                "baby shower", "bridal shower", "graduation", "holiday", "valentine's day"
            ]
            
            # DIY levels
            self.diy_levels = ["beginner", "moderate", "advanced", "expert"]
            
        except Exception as e:
            logger.error(f"Error loading reference data: {e}")
            # Use minimal fallback data
            self.color_mapping = {"red": ["red"], "white": ["white"], "pink": ["pink"]}
            self.event_types = ["wedding", "birthday", "anniversary"]
            self.diy_levels = ["beginner", "moderate", "advanced"]
    
    def setup_prompts(self):
        """Create specialized prompt templates"""
        self.info_gathering_prompt = ChatPromptTemplate.from_template("""
        You are an expert flower consultant. Based on the conversation so far and the user's latest message, 
        determine what information you still need to gather to provide good flower recommendations.

        Current requirements gathered:
        - Event Type: {event_type}
        - Event Date: {event_date}
        - Budget: {budget_range}
        - Colors: {colors}
        - DIY Level: {diy_level}
        - Flower Types: {flower_types}
        - Guest Count: {guest_count}

        User's latest message: {user_input}

        Available event types: {event_types}
        Available DIY levels: {diy_levels}
        Available colors: {available_colors}

        Respond naturally as a flower consultant would. Ask for the most important missing information first.
        If you have enough information, suggest moving to recommendations.
        
        Guidelines:
        - Be conversational and warm
        - Ask one main question at a time
        - Provide helpful context (e.g., typical budget ranges)
        - Validate dates and suggest alternatives for out-of-season requests
        """)
        
        self.sql_generation_prompt = ChatPromptTemplate.from_template("""
        Based on the user requirements, generate a SQL query to find matching flowers from the database.
        
        Database Schema:
        - Table: cleaned_flower_data
        - Key columns:
          * variant_price (decimal) - price of the product
          * seasonality_parsed (text array) - months/seasons when available
          * colors_list (text array) - available colors  
          * holiday_occasions_list (text array) - suitable occasions
          * diy_level_normalized (text) - difficulty level
          * group_name (text) - flower type/category
          * product_name (text) - product name
          * color_categories (text array) - normalized color categories

        User Requirements:
        {requirements}

        Generate a SQL query that:
        1. Filters by budget if specified (variant_price <= budget_max)
        2. Matches seasonality if date specified
        3. Includes requested colors using color_categories or colors_list
        4. Matches event type in holiday_occasions_list
        5. Filters by DIY level if specified
        6. Orders by popularity or price

        Return only the SQL query, no explanation.
        """)
    
    def normalize_color_input(self, color_input: str) -> List[str]:
        """Convert user color input to standardized colors"""
        color_input = color_input.lower().strip()
        normalized_colors = []
        
        for base_color, variations in self.color_mapping.items():
            if color_input in [v.lower() for v in variations]:
                normalized_colors.append(base_color)
                break
        
        if not normalized_colors:
            # Try partial matching
            for base_color, variations in self.color_mapping.items():
                if any(color_input in v.lower() for v in variations):
                    normalized_colors.append(base_color)
                    break
        
        return normalized_colors if normalized_colors else [color_input]
    
    def parse_user_input(self, user_input: str) -> Dict[str, Any]:
        """Extract structured information from user input"""
        parsed_info = {}
        user_lower = user_input.lower()
        
        # Extract budget
        import re
        budget_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?) dollars?',
            r'budget.*?(\d+(?:,\d{3})*(?:\.\d{2})?)',
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, user_lower)
            if match:
                budget_value = float(match.group(1).replace(',', ''))
                parsed_info['budget_max'] = budget_value
                break
        
        # Extract date
        # This is simplified - you might want to use a more sophisticated date parser
        date_patterns = [
            r'(\w+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?',
            r'(\d{1,2})/(\d{1,2})/(\d{4})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]
        
        # Extract colors
        for color_family in self.color_mapping.keys():
            if color_family in user_lower:
                if 'colors' not in parsed_info:
                    parsed_info['colors'] = []
                parsed_info['colors'].append(color_family)
        
        # Extract event type
        for event_type in self.event_types:
            if event_type.lower() in user_lower:
                parsed_info['event_type'] = event_type
                break
        
        # Extract DIY level
        for diy_level in self.diy_levels:
            if diy_level in user_lower:
                parsed_info['diy_level'] = diy_level
                break
        
        return parsed_info
    
    def update_requirements(self, parsed_info: Dict[str, Any]):
        """Update user requirements with new information"""
        for key, value in parsed_info.items():
            if hasattr(self.requirements, key):
                if key == 'colors' and isinstance(value, list):
                    # Extend colors list
                    existing_colors = getattr(self.requirements, key, [])
                    existing_colors.extend(value)
                    setattr(self.requirements, key, list(set(existing_colors)))
                else:
                    setattr(self.requirements, key, value)
    
    def generate_sql_query(self) -> str:
        """Generate SQL query based on current requirements"""
        try:
            response = self.llm.invoke([
                HumanMessage(content=self.sql_generation_prompt.format(
                    requirements=json.dumps(self.requirements.to_dict(), indent=2)
                ))
            ])
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating SQL query: {e}")
            return self.fallback_query()
    
    def fallback_query(self) -> str:
        """Fallback query when SQL generation fails"""
        return """
        SELECT product_name, variant_price, colors_list, group_name, 
               diy_level_normalized, seasonality_parsed
        FROM cleaned_flower_data 
        WHERE variant_price IS NOT NULL 
        ORDER BY variant_price 
        LIMIT 10;
        """
    
    def execute_search(self) -> List[Dict]:
        """Execute search and return results"""
        try:
            sql_query = self.generate_sql_query()
            logger.info(f"Executing SQL: {sql_query}")
            
            response = self.sql_agent.invoke({"input": f"Execute this query and return results: {sql_query}"})
            
            # Parse the results (this might need adjustment based on your agent's output format)
            return self.parse_search_results(response.get('output', ''))
            
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            return []
    
    def parse_search_results(self, agent_output: str) -> List[Dict]:
        """Parse SQL agent output into structured results"""
        # This is a simplified parser - you might need to adjust based on actual agent output
        results = []
        try:
            # If the agent returns structured data, parse it
            # For now, we'll return a placeholder
            results = [
                {
                    'product_name': 'Sample Rose Bouquet',
                    'variant_price': 89.99,
                    'colors_list': ['red', 'white'],
                    'group_name': 'roses'
                }
            ]
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return results
    
    def get_popular_recommendations(self, category: str = None) -> List[Dict]:
        """Get popular recommendations as fallback"""
        try:
            fallback_query = f"""
            SELECT product_name, variant_price, colors_list, group_name, diy_level_normalized
            FROM cleaned_flower_data 
            WHERE variant_price IS NOT NULL 
            {f"AND '{category}' = ANY(holiday_occasions_list)" if category else ""}
            ORDER BY variant_price ASC 
            LIMIT 5;
            """
            
            response = self.sql_agent.invoke({"input": f"Execute: {fallback_query}"})
            return self.parse_search_results(response.get('output', ''))
            
        except Exception as e:
            logger.error(f"Error getting popular recommendations: {e}")
            return []
    
    def format_recommendations(self, results: List[Dict]) -> str:
        """Format search results into user-friendly recommendations"""
        if not results:
            return "I couldn't find exact matches for your requirements, but let me suggest some popular alternatives."
        
        response = "Based on your requirements, here are my recommendations:\n\n"
        
        for i, result in enumerate(results[:5], 1):
            response += f"{i}. **{result.get('product_name', 'Unknown Product')}**\n"
            response += f"   Price: ${result.get('variant_price', 'N/A')}\n"
            response += f"   Colors: {', '.join(result.get('colors_list', []))}\n"
            response += f"   Type: {result.get('group_name', 'N/A')}\n\n"
        
        response += "Would you like more details about any of these options, or would you like to adjust your requirements?"
        
        return response
    
    def handle_conversation(self, user_input: str) -> str:
        """Main conversation handler"""
        try:
            # Add user input to memory
            self.memory.chat_memory.add_user_message(user_input)
            
            # Parse user input for structured information
            parsed_info = self.parse_user_input(user_input)
            self.update_requirements(parsed_info)
            
            # Determine conversation flow based on state and gathered info
            if self.state == ConversationState.GREETING:
                response = self.handle_greeting(user_input)
                self.state = ConversationState.GATHERING_INFO
                
            elif self.state == ConversationState.GATHERING_INFO:
                if self.requirements.is_complete():
                    # Execute search
                    results = self.execute_search()
                    if results:
                        response = self.format_recommendations(results)
                        self.state = ConversationState.SHOWING_RESULTS
                    else:
                        # No results, get popular recommendations
                        popular = self.get_popular_recommendations(self.requirements.event_type)
                        response = self.format_recommendations(popular)
                        response = "I couldn't find exact matches, but here are some popular options:\n\n" + response
                        self.state = ConversationState.SHOWING_RESULTS
                else:
                    response = self.gather_more_info(user_input)
                    
            elif self.state == ConversationState.SHOWING_RESULTS:
                response = self.handle_results_followup(user_input)
                
            else:
                response = "I'm here to help you find the perfect flowers! What can I assist you with?"
            
            # Add bot response to memory
            self.memory.chat_memory.add_ai_message(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in conversation handler: {e}")
            return "I apologize, but I encountered an error. Let me try to help you differently. What flowers are you looking for?"
    
    def handle_greeting(self, user_input: str) -> str:
        """Handle initial greeting and basic info gathering"""
        if any(word in user_input.lower() for word in ['wedding', 'anniversary', 'birthday', 'event']):
            return f"Wonderful! I'd love to help you with flowers. I see you mentioned a {self.requirements.event_type or 'special event'}. To give you the best recommendations, could you tell me when your event is and what your budget range is?"
        else:
            return "Hello! I'm your AI flower consultant. I'm here to help you find the perfect flowers for any occasion. What type of event are you planning flowers for?"
    
    def gather_more_info(self, user_input: str) -> str:
        """Gather missing information using LLM"""
        try:
            # Use the info gathering prompt
            response = self.llm.invoke([
                HumanMessage(content=self.info_gathering_prompt.format(
                    event_type=self.requirements.event_type or "Not specified",
                    event_date=self.requirements.event_date.strftime('%Y-%m-%d') if self.requirements.event_date else "Not specified",
                    budget_range=f"${self.requirements.budget_max}" if self.requirements.budget_max else "Not specified",
                    colors=", ".join(self.requirements.colors) if self.requirements.colors else "Not specified",
                    diy_level=self.requirements.diy_level or "Not specified",
                    flower_types=", ".join(self.requirements.flower_types) if self.requirements.flower_types else "Not specified",
                    guest_count=self.requirements.guest_count or "Not specified",
                    user_input=user_input,
                    event_types=", ".join(self.event_types),
                    diy_levels=", ".join(self.diy_levels),
                    available_colors=", ".join(self.color_mapping.keys())
                ))
            ])
            return response.content
            
        except Exception as e:
            logger.error(f"Error in gather_more_info: {e}")
            return "Could you tell me a bit more about your event? When is it and what's your budget range?"
    
    def handle_results_followup(self, user_input: str) -> str:
        """Handle follow-up questions after showing results"""
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ['more', 'other', 'different', 'alternatives']):
            # Get more results
            results = self.execute_search()
            return self.format_recommendations(results[5:10])  # Show next 5 results
            
        elif any(word in user_lower for word in ['details', 'tell me more', 'information']):
            return "I'd be happy to provide more details! Which specific arrangement interests you most? I can tell you about care instructions, delivery options, or customization possibilities."
            
        elif any(word in user_lower for word in ['change', 'different', 'adjust']):
            self.state = ConversationState.GATHERING_INFO
            return "Of course! What would you like to change about your requirements? Budget, colors, event date, or something else?"
            
        else:
            return "Is there anything specific you'd like to know about these recommendations? I can provide more details, suggest alternatives, or help you refine your search."

# ---------------------------
# 4. Enhanced Main Loop
# ---------------------------
def main():
    DB_URI = "postgresql+psycopg2://postgres:Harrison891%21@localhost:5432/flower_bot_db"
    
    consultant = EnhancedFlowerConsultant(DB_URI, OPENAI_API_KEY)
    
    print("💐 Enhanced AI Flower Consultant ready! Type 'exit' to quit.")
    print("I'm here to help you find perfect flowers for any occasion!\n")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Thank you for using the AI Flower Consultant! Have a beautiful day! 💐")
            break

        try:
            response = consultant.handle_conversation(user_input)
            print(f"\nBot: {response}")
            
            # Debug info (remove in production)
            if user_input.lower().startswith('debug'):
                print(f"\nDEBUG - Current state: {consultant.state}")
                print(f"DEBUG - Requirements: {consultant.requirements.to_dict()}")
                
        except Exception as e:
            logger.error(f"Main loop error: {e}")
            print(f"⚠️ I apologize, but I encountered an error. Let me try again. What can I help you with?")

if __name__ == "__main__":
    main()