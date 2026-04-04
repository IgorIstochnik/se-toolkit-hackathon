"""
Matrix Cafe Menu Scraper

Scrapes and parses the Matrix cafe menu.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import re
import json


class MenuItem:
    """Represents a single menu item from the Matrix cafe."""
    
    def __init__(
        self,
        name: str,
        meal_type: str,
        price: float,
        description: str = "",
        ingredients: List[str] = None,
        weight: str = "",
        date: str = ""
    ):
        self.name = name
        self.meal_type = meal_type  # salad, soup, main course, etc.
        self.price = price
        self.description = description
        self.ingredients = ingredients or []
        self.weight = weight
        self.date = date or datetime.now().strftime("%Y-%m-%d")
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "meal_type": self.meal_type,
            "price": self.price,
            "description": self.description,
            "ingredients": self.ingredients,
            "weight": self.weight,
            "date": self.date
        }
    
    def __repr__(self):
        return f"MenuItem('{self.name}', '{self.meal_type}', {self.price})"


class MatrixCafeScraper:
    """Scraper for Matrix cafe at Innopolis University."""
    
    # Meal type mappings (Russian to English)
    MEAL_TYPE_MAP = {
        "салат": "salad",
        "суп": "soup",
        "горячее": "main course",
        "гарнир": "side dish",
        "напиток": "drink",
        "десерт": "dessert",
        "закуска": "appetizer",
        "каша": "porridge",
        "выпечка": "pastry",
    }
    
    def __init__(self, menu_url: str = ""):
        self.menu_url = menu_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def fetch_menu(self, url: Optional[str] = None) -> str:
        """Fetch the menu HTML from the given URL."""
        target_url = url or self.menu_url
        if not target_url:
            raise ValueError("No URL provided for menu scraping")
        
        response = self.session.get(target_url, timeout=10)
        response.raise_for_status()
        return response.text
    
    def parse_menu(self, html_content: str) -> List[MenuItem]:
        """Parse menu HTML and extract menu items."""
        soup = BeautifulSoup(html_content, "html.parser")
        menu_items = []
        
        # This is a generic parser - adjust selectors based on actual HTML structure
        # Look for menu item containers
        for item_div in soup.find_all(["div", "li"], class_=re.compile(r"menu|item|dish|food", re.I)):
            menu_item = self._extract_menu_item(item_div)
            if menu_item:
                menu_items.append(menu_item)
        
        # If no structured data found, try to extract from text
        if not menu_items:
            menu_items = self._extract_from_text(soup)
        
        return menu_items
    
    def _extract_menu_item(self, element) -> Optional[MenuItem]:
        """Extract a single menu item from an HTML element."""
        name_elem = element.find(["h3", "h4", ".title", ".name"])
        price_elem = element.find(["span", ".price"])
        
        if not name_elem:
            return None
        
        name = name_elem.get_text(strip=True)
        price_text = price_elem.get_text(strip=True) if price_elem else "0"
        
        # Extract price number
        price_match = re.search(r"(\d+)", price_text)
        price = float(price_match.group(1)) if price_match else 0.0
        
        # Determine meal type from context
        meal_type = self._determine_meal_type(element)
        
        return MenuItem(
            name=name,
            meal_type=meal_type,
            price=price,
            description=element.get_text(strip=True)[:200]
        )
    
    def _determine_meal_type(self, element) -> str:
        """Determine the meal type from the element's context."""
        text = element.get_text().lower()
        
        for russian, english in self.MEAL_TYPE_MAP.items():
            if russian in text:
                return english
        
        return "other"
    
    def _extract_from_text(self, soup) -> List[MenuItem]:
        """Fallback: extract menu items from raw text content."""
        menu_items = []
        text = soup.get_text()
        
        # Look for patterns like "Item name - 150₽" or "Item name 150 руб"
        pattern = r"([А-Яа-яA-Za-z\s\-]+)\s*[-–—]?\s*(\d+)\s*(?:₽|руб|rub)"
        matches = re.finditer(pattern, text)
        
        for match in matches:
            name = match.group(1).strip()
            price = float(match.group(2))
            
            if len(name) > 2:  # Filter out very short matches
                menu_items.append(MenuItem(
                    name=name,
                    meal_type="other",
                    price=price
                ))
        
        return menu_items
    
    def scrape_and_parse(self, url: Optional[str] = None) -> List[Dict]:
        """Main method: scrape and parse menu, return as list of dicts."""
        html = self.fetch_menu(url)
        items = self.parse_menu(html)
        return [item.to_dict() for item in items]
    
    def parse_sample_menu(self) -> List[Dict]:
        """Parse a sample menu for testing purposes."""
        sample_items = [
            MenuItem("Цезарь с курицей", "salad", 180, "Classic Caesar salad with chicken", ["lettuce", "chicken", "parmesan", "croutons"], "200g"),
            MenuItem("Борщ", "soup", 120, "Traditional beet soup", ["beet", "cabbage", "potato", "beef"], "300ml"),
            MenuItem("Куриная грудка", "main course", 200, "Grilled chicken breast", ["chicken"], "250g"),
            MenuItem("Гречка", "side dish", 80, "Buckwheat", ["buckwheat"], "200g"),
            MenuItem("Компот", "drink", 50, "Dried fruit compote", ["dried fruits", "sugar"], "300ml"),
            MenuItem("Шарлотка", "dessert", 90, "Apple pie", ["flour", "apple", "sugar", "eggs"], "150g"),
        ]
        return [item.to_dict() for item in sample_items]


if __name__ == "__main__":
    scraper = MatrixCafeScraper()
    
    # Use sample menu for demo
    menu = scraper.parse_sample_menu()
    print(json.dumps(menu, indent=2, ensure_ascii=False))
