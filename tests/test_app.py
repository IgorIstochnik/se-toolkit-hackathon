"""
Tests for Matrix Cafe Menu Helper
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper import MatrixCafeScraper, MenuItem
from database.db import MenuDatabase


class TestMenuItem(unittest.TestCase):
    """Test MenuItem class."""
    
    def test_menu_item_creation(self):
        item = MenuItem("Цезарь", "salad", 180, "Caesar salad", ["lettuce"], "200g")
        self.assertEqual(item.name, "Цезарь")
        self.assertEqual(item.meal_type, "salad")
        self.assertEqual(item.price, 180)
    
    def test_menu_item_to_dict(self):
        item = MenuItem("Борщ", "soup", 120)
        data = item.to_dict()
        self.assertIn("name", data)
        self.assertIn("price", data)
        self.assertEqual(data["name"], "Борщ")


class TestMatrixCafeScraper(unittest.TestCase):
    """Test MatrixCafeScraper class."""
    
    def test_parse_sample_menu(self):
        scraper = MatrixCafeScraper()
        menu = scraper.parse_sample_menu()
        self.assertIsInstance(menu, list)
        self.assertGreater(len(menu), 0)
        
        # Check structure
        first_item = menu[0]
        self.assertIn("name", first_item)
        self.assertIn("meal_type", first_item)
        self.assertIn("price", first_item)
    
    def test_sample_menu_has_all_types(self):
        scraper = MatrixCafeScraper()
        menu = scraper.parse_sample_menu()
        meal_types = [item["meal_type"] for item in menu]
        
        self.assertIn("salad", meal_types)
        self.assertIn("soup", meal_types)
        self.assertIn("main course", meal_types)
        self.assertIn("drink", meal_types)


class TestMenuDatabase(unittest.TestCase):
    """Test MenuDatabase class."""
    
    def setUp(self):
        self.db = MenuDatabase(":memory:")
    
    def test_insert_and_retrieve_menu(self):
        sample_menu = [
            {"name": "Цезарь", "meal_type": "salad", "price": 180, "date": "2026-04-04"},
        ]
        self.db.insert_menu(sample_menu)
        
        retrieved = self.db.get_latest_menu()
        self.assertEqual(len(retrieved), 1)
        self.assertEqual(retrieved[0]["name"], "Цезарь")
    
    def test_get_items_by_type(self):
        sample_menu = [
            {"name": "Цезарь", "meal_type": "salad", "price": 180, "date": "2026-04-04"},
            {"name": "Борщ", "meal_type": "soup", "price": 120, "date": "2026-04-04"},
        ]
        self.db.insert_menu(sample_menu)
        
        salads = self.db.get_items_by_type("salad")
        self.assertEqual(len(salads), 1)
        self.assertEqual(salads[0]["name"], "Цезарь")
    
    def test_search_items(self):
        sample_menu = [
            {"name": "Цезарь с курицей", "meal_type": "salad", "price": 180, 
             "description": "Classic Caesar with chicken", "date": "2026-04-04"},
        ]
        self.db.insert_menu(sample_menu)
        
        results = self.db.search_items("Caesar")
        self.assertEqual(len(results), 1)
    
    def test_get_price_range(self):
        sample_menu = [
            {"name": "Cheap", "meal_type": "soup", "price": 50, "date": "2026-04-04"},
            {"name": "Expensive", "meal_type": "main course", "price": 300, "date": "2026-04-04"},
        ]
        self.db.insert_menu(sample_menu)
        
        cheap_items = self.db.get_price_range(0, 100)
        self.assertEqual(len(cheap_items), 1)
        self.assertEqual(cheap_items[0]["name"], "Cheap")


class TestMatrixCafeBot(unittest.TestCase):
    """Test MatrixCafeBot class."""
    
    def setUp(self):
        from nanobot.bot import MatrixCafeBot
        self.db = MenuDatabase(":memory:")
        
        # Populate with sample data
        scraper = MatrixCafeScraper()
        self.db.insert_menu(scraper.parse_sample_menu())
        
        self.bot = MatrixCafeBot(self.db)
    
    def test_get_today_menu(self):
        menu = self.bot.get_today_menu()
        self.assertIsInstance(menu, dict)
        self.assertGreater(len(menu), 0)
    
    def test_handle_menu_query(self):
        response = self.bot.handle_query("What's on the menu today?")
        self.assertIsInstance(response, str)
        self.assertIn("menu", response.lower())
    
    def test_handle_combo_query(self):
        response = self.bot.handle_query("Recommend a combo")
        self.assertIsInstance(response, str)
        self.assertIn("combo", response.lower())
    
    def test_handle_budget_query(self):
        response = self.bot.handle_query("I want something under 200₽")
        self.assertIsInstance(response, str)
    
    def test_recommend_meal_with_budget(self):
        response = self.bot.recommend_meal(budget=150)
        self.assertIsInstance(response, str)
    
    def test_recommend_combo(self):
        response = self.bot.recommend_meal(include_combo=True)
        self.assertIsInstance(response, str)
        self.assertIn("combo", response.lower())


if __name__ == "__main__":
    unittest.main()
