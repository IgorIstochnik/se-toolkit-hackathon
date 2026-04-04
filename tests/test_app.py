"""
Tests for Matrix Cafe Menu Helper
"""

import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.scraper import MatrixCafeScraper, MenuItem, MenuImageOCR
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


class TestMenuImageOCR(unittest.TestCase):
    """Test MenuImageOCR — the parser that turns OCR text into menu items."""

    def setUp(self):
        self.parser = MenuImageOCR()

    def test_parse_simple_menu(self):
        """Test parsing a typical Russian menu with section headers."""
        ocr_text = """Салаты
Цезарь с курицей - 180₽
Витаминный - 90₽

Супы
Борщ - 120₽
Куриный суп - 110₽

Горячее
Куриная грудка - 200₽
Рыба запеченная - 220₽

Напитки
Чай - 40₽
Компот - 50₽"""

        items = self.parser.parse_ocr_text(ocr_text)
        self.assertEqual(len(items), 8)

        # Check section assignment
        salad_items = [i for i in items if i.meal_type == "salad"]
        soup_items = [i for i in items if i.meal_type == "soup"]
        main_items = [i for i in items if i.meal_type == "main course"]
        drink_items = [i for i in items if i.meal_type == "drink"]

        self.assertEqual(len(salad_items), 2)
        self.assertEqual(len(soup_items), 2)
        self.assertEqual(len(main_items), 2)
        self.assertEqual(len(drink_items), 2)

    def test_parse_item_with_dash_price(self):
        """Test parsing 'Item name - 150₽' format."""
        text = "Борщ - 120₽"
        items = self.parser.parse_ocr_text(text)
        self.assertEqual(len(items), 1)
        self.assertIn("Борщ", items[0].name)
        self.assertEqual(items[0].price, 120.0)

    def test_parse_item_with_space_price(self):
        """Test parsing 'Item name 150₽' format."""
        text = "Чай 40₽"
        items = self.parser.parse_ocr_text(text)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].price, 40.0)

    def test_parse_rub_price(self):
        """Test parsing prices with 'руб' instead of '₽'."""
        text = "Котлета - 180 руб"
        items = self.parser.parse_ocr_text(text)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].price, 180.0)

    def test_section_detection(self):
        """Test that section headers are detected correctly."""
        self.assertEqual(self.parser._detect_section("Салаты"), "salad")
        self.assertEqual(self.parser._detect_section("САЛАТЫ"), "salad")
        self.assertEqual(self.parser._detect_section("супы"), "soup")
        self.assertEqual(self.parser._detect_section("Горячее"), "main course")
        self.assertEqual(self.parser._detect_section("Напитки"), "drink")
        self.assertEqual(self.parser._detect_section("Десерты"), "dessert")
        self.assertIsNone(self.parser._detect_section("Куриная грудка - 200₽"))

    def test_ocr_noise_filtering(self):
        """Test that OCR noise and non-item lines are filtered out."""
        noisy_text = """Салаты
12.04.2026
Цезарь - 180₽
|
Борщ - 120₽
MF Admin"""

        items = self.parser.parse_ocr_text(noisy_text)
        names = [i.name for i in items]

        self.assertIn("Цезарь", str(names))
        self.assertIn("Борщ", str(names))
        # Should not have date or noise as items
        self.assertFalse(any("2026" in n for n in names))
        self.assertFalse(any("Admin" in n for n in names))

    def test_date_assignment(self):
        """Test that date is properly assigned."""
        items = self.parser.parse_ocr_text("Борщ - 120₽", date="2026-04-04")
        self.assertEqual(items[0].date, "2026-04-04")


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

    def test_scraper_has_ocr_parser(self):
        """Test that scraper has MenuImageOCR available."""
        scraper = MatrixCafeScraper()
        self.assertIsNotNone(scraper.ocr_parser)
        self.assertIsInstance(scraper.ocr_parser, MenuImageOCR)


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
