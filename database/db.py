"""
Database module for Matrix Cafe Menu Helper

Stores and retrieves menu data using SQLite.
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class MenuDatabase:
    """SQLite database for storing Matrix cafe menu items."""
    
    def __init__(self, db_path: str = "menu.db"):
        self.db_path = db_path
        self.conn = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database and create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                meal_type TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT DEFAULT '',
                ingredients TEXT DEFAULT '[]',
                weight TEXT DEFAULT '',
                date TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def insert_menu(self, menu_items: List[Dict]):
        """Insert a list of menu items into the database."""
        cursor = self.conn.cursor()
        
        # Record the menu date
        if menu_items:
            menu_date = menu_items[0].get("date", datetime.now().strftime("%Y-%m-%d"))
            cursor.execute(
                "INSERT OR IGNORE INTO menu_dates (date) VALUES (?)",
                (menu_date,)
            )
        
        for item in menu_items:
            cursor.execute("""
                INSERT INTO menu_items (name, meal_type, price, description, ingredients, weight, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("name", ""),
                item.get("meal_type", "other"),
                item.get("price", 0.0),
                item.get("description", ""),
                json.dumps(item.get("ingredients", [])),
                item.get("weight", ""),
                item.get("date", datetime.now().strftime("%Y-%m-%d"))
            ))
        
        self.conn.commit()
    
    def get_menu_by_date(self, date: str) -> List[Dict]:
        """Get all menu items for a specific date."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM menu_items WHERE date = ? ORDER BY meal_type, name",
            (date,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_latest_menu(self) -> List[Dict]:
        """Get the most recent menu available."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT date FROM menu_items ORDER BY date DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            return self.get_menu_by_date(row["date"])
        return []
    
    def get_items_by_type(self, meal_type: str, date: Optional[str] = None) -> List[Dict]:
        """Get menu items filtered by meal type."""
        cursor = self.conn.cursor()
        
        if date:
            cursor.execute(
                "SELECT * FROM menu_items WHERE meal_type = ? AND date = ? ORDER BY name",
                (meal_type, date)
            )
        else:
            cursor.execute(
                "SELECT * FROM menu_items WHERE meal_type = ? ORDER BY date DESC, name",
                (meal_type,)
            )
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_items(self, query: str) -> List[Dict]:
        """Search menu items by name or description."""
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        
        cursor.execute("""
            SELECT * FROM menu_items 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY date DESC
        """, (search_pattern, search_pattern))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_all_meal_types(self) -> List[str]:
        """Get all unique meal types in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT meal_type FROM menu_items ORDER BY meal_type")
        return [row["meal_type"] for row in cursor.fetchall()]
    
    def get_price_range(self, min_price: float = 0, max_price: float = float('inf')) -> List[Dict]:
        """Get menu items within a price range."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM menu_items WHERE price BETWEEN ? AND ? ORDER BY price",
            (min_price, max_price)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def clear_old_menus(self, keep_days: int = 7):
        """Remove menu items older than specified days."""
        cursor = self.conn.cursor()
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.strftime("%Y-%m-%d")
        
        cursor.execute("DELETE FROM menu_items WHERE date < ?", (cutoff_date,))
        cursor.execute("DELETE FROM menu_dates WHERE date < ?", (cutoff_date,))
        self.conn.commit()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __del__(self):
        self.close()


if __name__ == "__main__":
    # Test the database
    db = MenuDatabase(":memory:")
    
    sample_menu = [
        {"name": "Цезарь с курицей", "meal_type": "salad", "price": 180, "description": "Classic Caesar salad with chicken", "ingredients": ["lettuce", "chicken", "parmesan"], "weight": "200g", "date": "2026-04-04"},
        {"name": "Борщ", "meal_type": "soup", "price": 120, "description": "Traditional beet soup", "ingredients": ["beet", "cabbage", "potato"], "weight": "300ml", "date": "2026-04-04"},
        {"name": "Куриная грудка", "meal_type": "main course", "price": 200, "description": "Grilled chicken breast", "ingredients": ["chicken"], "weight": "250g", "date": "2026-04-04"},
    ]
    
    db.insert_menu(sample_menu)
    
    print("Latest menu:")
    for item in db.get_latest_menu():
        print(f"  - {item['name']} ({item['meal_type']}): {item['price']}₽")
    
    print("\nSalads:")
    for item in db.get_items_by_type("salad"):
        print(f"  - {item['name']}: {item['price']}₽")
    
    print("\nSearch for 'chicken':")
    for item in db.search_items("chicken"):
        print(f"  - {item['name']}: {item['price']}₽")
