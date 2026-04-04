"""
Menu Scheduler for Matrix Cafe Menu Helper

Periodically scrapes and updates the menu database.
"""

import time
import schedule
from datetime import datetime
from typing import Optional

from scraper.scraper import MatrixCafeScraper
from database.db import MenuDatabase


class MenuScheduler:
    """Schedules periodic menu scraping and database updates."""
    
    def __init__(self, db: MenuDatabase, scraper: MatrixCafeScraper, scrape_interval_hours: int = 4):
        self.db = db
        self.scraper = scraper
        self.scrape_interval_hours = scrape_interval_hours
        self.running = False
    
    def scrape_and_store(self):
        """Scrape the menu and store in database."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scraping menu...")
        
        try:
            # Try to scrape from URL (if available)
            menu_items = self.scraper.parse_sample_menu()
            
            if menu_items:
                self.db.insert_menu(menu_items)
                print(f"  Stored {len(menu_items)} menu items.")
            else:
                print("  No menu items found.")
        
        except Exception as e:
            print(f"  Error scraping menu: {e}")
    
    def cleanup_old_menus(self):
        """Remove menu items older than 7 days."""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cleaning up old menus...")
        self.db.clear_old_menus(keep_days=7)
        print("  Cleanup complete.")
    
    def start(self):
        """Start the scheduler."""
        print(f"Starting menu scheduler (interval: {self.scrape_interval_hours}h)...")
        
        # Initial scrape
        self.scrape_and_store()
        
        # Schedule periodic scraping
        schedule.every(self.scrape_interval_hours).hours.do(self.scrape_and_store)
        
        # Schedule daily cleanup at 3 AM
        schedule.every().day.at("03:00").do(self.cleanup_old_menus)
        
        self.running = True
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        print("Scheduler stopped.")


def main():
    """Run the menu scheduler."""
    db = MenuDatabase("menu.db")
    scraper = MatrixCafeScraper()
    
    scheduler = MenuScheduler(db, scraper)
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nShutting down scheduler...")
        scheduler.stop()


if __name__ == "__main__":
    main()
