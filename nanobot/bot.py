"""
Matrix Cafe Menu Helper - Nanobot Agent

LLM-powered agent that helps Innopolis University students 
choose meals at the Matrix cafe.
"""

import json
import sys
import os
from typing import List, Dict, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper import MatrixCafeScraper
from database.db import MenuDatabase


class MatrixCafeBot:
    """Nanobot agent for Matrix cafe meal recommendations."""
    
    SYSTEM_PROMPT = """You are a helpful assistant for Innopolis University students 
eating at the Matrix cafe. Your job is to help students choose meals based on their 
preferences, budget, and dietary needs.

You have access to today's menu with prices. Make recommendations that are:
- Tasty and nourishing
- Within the student's budget
- Balanced (suggest combos when appropriate)
- Based on their preferences (vegetarian, spicy, light, etc.)

Always be friendly and helpful. Format your responses clearly with meal names, 
prices, and brief explanations of why you're recommending them."""
    
    def __init__(self, db: MenuDatabase):
        self.db = db
        self.conversation_history = []
    
    def get_today_menu(self) -> Dict[str, List[Dict]]:
        """Get today's menu organized by meal type."""
        menu_items = self.db.get_latest_menu()
        
        menu_by_type = {}
        for item in menu_items:
            meal_type = item.get("meal_type", "other")
            if meal_type not in menu_by_type:
                menu_by_type[meal_type] = []
            menu_by_type[meal_type].append(item)
        
        return menu_by_type
    
    def format_menu_for_display(self, menu_by_type: Dict[str, List[Dict]]) -> str:
        """Format menu data for display."""
        output = []
        for meal_type, items in menu_by_type.items():
            output.append(f"\n**{meal_type.upper()}**:")
            for item in items:
                output.append(f"  • {item['name']} - {item['price']}₽ {item.get('weight', '')}")
                if item.get("description"):
                    output.append(f"    {item['description']}")
        
        return "\n".join(output) if output else "No menu available for today."
    
    def recommend_meal(
        self,
        budget: Optional[float] = None,
        meal_type: Optional[str] = None,
        dietary_preference: Optional[str] = None,
        include_combo: bool = False
    ) -> str:
        """Generate meal recommendations based on criteria."""
        menu_items = self.db.get_latest_menu()
        
        # Filter by meal type if specified
        if meal_type:
            menu_items = [item for item in menu_items if item.get("meal_type") == meal_type]
        
        # Filter by budget if specified
        if budget:
            menu_items = [item for item in menu_items if item.get("price", 0) <= budget]
        
        if not menu_items:
            return "Sorry, no items match your criteria. Try adjusting your filters!"
        
        # Generate recommendation
        if include_combo:
            return self._generate_combo(menu_items, budget)
        
        # Simple recommendation: sort by rating (can be enhanced)
        recommendations = sorted(menu_items, key=lambda x: x.get("price", 0), reverse=True)[:3]
        
        response = "Here are my recommendations:\n"
        for item in recommendations:
            response += f"\n• **{item['name']}** ({item['meal_type']}) - {item['price']}₽"
            if item.get("description"):
                response += f"\n  {item['description']}"
        
        total = sum(item.get("price", 0) for item in recommendations)
        response += f"\n\nTotal: {total}₽"
        
        return response
    
    def _generate_combo(self, menu_items: List[Dict], budget: Optional[float] = None) -> str:
        """Generate a balanced meal combo."""
        menu_by_type = {}
        for item in menu_items:
            meal_type = item.get("meal_type", "other")
            if meal_type not in menu_by_type:
                menu_by_type[meal_type] = []
            menu_by_type[meal_type].append(item)
        
        # Build combo: salad + soup + main + drink
        combo_types = ["salad", "soup", "main course", "drink"]
        
        # If budget is specified, pick cheapest options first
        if budget:
            combo = []
            for meal_type in combo_types:
                if meal_type in menu_by_type:
                    # Sort by price and pick cheapest that fits remaining budget
                    remaining = budget - sum(item.get("price", 0) for item in combo)
                    affordable = [item for item in menu_by_type[meal_type] 
                                  if item.get("price", 0) <= remaining]
                    if affordable:
                        combo.append(affordable[0])
            
            total = sum(item.get("price", 0) for item in combo)
            if not combo:
                return "Couldn't create a combo within your budget. Try increasing it!"
        else:
            # No budget constraint - pick first available
            combo = []
            for meal_type in combo_types:
                if meal_type in menu_by_type:
                    combo.append(menu_by_type[meal_type][0])
            total = sum(item.get("price", 0) for item in combo)
        
        if not combo:
            return "Couldn't create a combo within your budget. Try increasing it!"
        
        response = "**Balanced Lunch Combo:**\n"
        for item in combo:
            response += f"\n• {item['name']} ({item['meal_type']}) - {item['price']}₽"
        
        response += f"\n\n**Total: {total}₽**"
        response += f"\n\nThis combo gives you a balanced meal with variety!"
        
        return response
    
    def handle_query(self, query: str) -> str:
        """Handle a user query and return a response."""
        query_lower = query.lower()
        
        # Parse intent from query
        if "menu" in query_lower or "today" in query_lower:
            menu = self.get_today_menu()
            return f"Here's today's Matrix cafe menu:{self.format_menu_for_display(menu)}"
        
        if "combo" in query_lower or "combination" in query_lower:
            budget = self._extract_budget(query)
            return self.recommend_meal(budget=budget, include_combo=True)
        
        if "cheap" in query_lower or "budget" in query_lower or "under" in query_lower:
            budget = self._extract_budget(query_lower) or 200
            return self.recommend_meal(budget=budget)
        
        if any(meal_type in query_lower for meal_type in ["salad", "soup", "main", "drink", "dessert"]):
            meal_type = self._extract_meal_type(query_lower)
            return self.recommend_meal(meal_type=meal_type)
        
        if "recommend" in query_lower or "suggest" in query_lower or "what" in query_lower:
            return self.recommend_meal(include_combo=True)
        
        # Default: show menu and offer help
        menu = self.get_today_menu()
        return (
            f"Hi! Here's today's menu:{self.format_menu_for_display(menu)}\n\n"
            "You can ask me:\n"
            "• 'What's on the menu today?'\n"
            "• 'Recommend a combo for lunch'\n"
            "• 'I want something under 300₽'\n"
            "• 'Show me salads'\n"
            "• 'What soup do you have?'"
        )
    
    def _extract_budget(self, query: str) -> Optional[float]:
        """Extract budget amount from query text."""
        import re
        match = re.search(r"(\d+)\s*(?:₽|rub|руб)", query)
        if match:
            return float(match.group(1))
        
        # Common budget phrases
        if "under 200" in query or "cheap" in query:
            return 200.0
        if "under 300" in query:
            return 300.0
        if "under 400" in query:
            return 400.0
        
        return None
    
    def _extract_meal_type(self, query: str) -> Optional[str]:
        """Extract meal type from query text."""
        meal_types = ["salad", "soup", "main course", "main", "drink", "dessert", "appetizer", "side dish"]
        
        for meal_type in meal_types:
            if meal_type in query:
                return "main course" if meal_type == "main" else meal_type
        
        return None
    
    def interactive_mode(self):
        """Run the bot in interactive CLI mode."""
        print("=" * 50)
        print("🍽️  Matrix Cafe Menu Helper")
        print("=" * 50)
        print("\nHi! I'll help you choose meals at Matrix cafe.")
        print("Type 'quit' to exit, 'menu' to see today's menu.\n")
        
        while True:
            try:
                query = input("You: ").strip()
                
                if query.lower() in ["quit", "exit", "q"]:
                    print("\nEnjoy your meal! 👋")
                    break
                
                if not query:
                    continue
                
                response = self.handle_query(query)
                print(f"\nBot: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nEnjoy your meal! 👋")
                break
            except EOFError:
                break


def main():
    """Main entry point for the nanobot."""
    # Initialize database with sample data for demo
    db = MenuDatabase("menu.db")
    
    # Check if database has data, if not populate with sample
    if not db.get_latest_menu():
        scraper = MatrixCafeScraper()
        sample_menu = scraper.parse_sample_menu()
        db.insert_menu(sample_menu)
        print("Loaded sample menu data.")
    
    bot = MatrixCafeBot(db)
    bot.interactive_mode()


if __name__ == "__main__":
    main()
