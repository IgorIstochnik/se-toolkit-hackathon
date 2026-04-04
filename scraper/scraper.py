"""
Matrix Cafe Menu Scraper

Scrapes and parses the Matrix cafe menu from Telegram channel @matrixfood.
Menu content is posted as images, so OCR is used to extract text.

Usage:
    # Full pipeline (works on university VM where CDN is accessible)
    python scraper/scraper.py

    # From local image file
    python scraper/scraper.py --image menu_photo.jpg

    # From pasted OCR text
    python scraper/scraper.py --text "Салаты\nЦезарь - 180₽\nСупы\nБорщ - 120₽"
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import re
import json
import os
import sys
import io

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    Image = None  # type: ignore
    pytesseract = None  # type: ignore
    OCR_AVAILABLE = False


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
        self.meal_type = meal_type
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


class MenuImageOCR:
    """Extracts structured menu items from OCR text of menu images."""

    # Russian menu section headers -> English meal types
    SECTION_HEADERS = {
        "салат": "salad",
        "салаты": "salad",
        "суп": "soup",
        "супы": "soup",
        "первые блюда": "soup",
        "горячее": "main course",
        "горячее блюдо": "main course",
        "горячие блюда": "main course",
        "вторые блюда": "main course",
        "гарнир": "side dish",
        "гарниры": "side dish",
        "напиток": "drink",
        "напитки": "drink",
        "десерт": "dessert",
        "десерты": "dessert",
        "закуска": "appetizer",
        "закуски": "appetizer",
        "каша": "porridge",
        "каши": "porridge",
        "выпечка": "pastry",
        "хлеб": "bread",
        "соус": "sauce",
        "соусы": "sauce",
        "завтрак": "breakfast",
        "завтраки": "breakfast",
    }

    # Price pattern: number followed by ₽ or руб
    PRICE_PATTERN = re.compile(r'(\d+)\s*(?:₽|руб\.?|rub|rub\.)', re.IGNORECASE)

    # Item line patterns: "item name - price" or "item name price"
    ITEM_LINE_PATTERNS = [
        re.compile(r'(.+?)\s*[-–—]\s*(\d+)\s*₽', re.IGNORECASE),
        re.compile(r'(.+?)\s*(\d+)\s*₽', re.IGNORECASE),
        re.compile(r'(.+?)\s*[-–—]\s*(\d+)\s*руб\.?', re.IGNORECASE),
        re.compile(r'(.+?)\s+(\d+)\s*руб\.?', re.IGNORECASE),
    ]

    def __init__(self):
        self.current_section = "other"

    def parse_ocr_text(self, ocr_text: str, date: str = "") -> List[MenuItem]:
        """Parse OCR text from a menu image into structured menu items."""
        items = []
        lines = ocr_text.strip().split('\n')
        self.current_section = "other"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line is a section header
            section = self._detect_section(line)
            if section:
                self.current_section = section
                continue

            # Try to extract menu item (name + price)
            item = self._parse_item_line(line)
            if item:
                item.date = date or datetime.now().strftime("%Y-%m-%d")
                item.meal_type = self.current_section
                items.append(item)

        return items

    def _detect_section(self, line: str) -> Optional[str]:
        """Check if a line is a section header.

        Section headers are short and match known keywords.
        Lines with prices are items, not headers.
        """
        line_lower = line.lower().strip()

        # Lines with prices are menu items, not headers
        if self.PRICE_PATTERN.search(line):
            return None

        # Section headers are typically short
        if len(line_lower) > 35:
            return None

        for header, meal_type in self.SECTION_HEADERS.items():
            if line_lower == header or (line_lower.startswith(header) and len(line_lower) < len(header) + 5):
                return meal_type

        return None

    def _parse_item_line(self, line: str) -> Optional[MenuItem]:
        """Try to parse a menu item from a single OCR line."""
        for pattern in self.ITEM_LINE_PATTERNS:
            match = pattern.search(line)
            if match:
                name = match.group(1).strip()
                price = float(match.group(2))

                # Filter out noise
                if len(name) < 2 or len(name) > 80:
                    continue

                # Skip dates
                if re.match(r'^\d{1,2}[./-]\d{1,2}', name):
                    continue

                # Skip common noise words
                noise_words = ['the', 'and', 'or', 'no', 'yes', 'да', 'нет', 'the', 'a', 'an']
                if name.lower() in noise_words:
                    continue

                return MenuItem(
                    name=self._clean_name(name),
                    meal_type="other",
                    price=price
                )

        return None

    def _clean_name(self, name: str) -> str:
        """Clean up OCR noise from item name."""
        name = re.sub(r'[|!1]+$', '', name)
        name = re.sub(r'^[|!]+', '', name)
        name = name.strip('.- ')

        # Fix common OCR misrecognitions
        replacements = {
            'Борш': 'Борщ',
            'борш': 'борщ',
            'Kомпот': 'Компот',
            'Гpeчка': 'Гречка',
        }
        for wrong, correct in replacements.items():
            name = name.replace(wrong, correct)

        return name


class MatrixCafeScraper:
    """Scraper for Matrix cafe at Innopolis University.

    Fetches menu images from the Telegram channel web preview
    and uses OCR to extract structured menu data.

    Pipeline:
        1. Fetch https://t.me/s/matrixfood
        2. Extract image URLs from .tgme_widget_message_photo_wrap elements
        3. Download images from cdn*.telesco.pe
        4. OCR with Tesseract (rus+eng)
        5. Parse structured menu items with section detection
    """

    CHANNEL_URL = "https://t.me/s/matrixfood"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        self.ocr_parser = MenuImageOCR()

    # ---- Step 1: Fetch channel web preview ----

    def fetch_channel(self) -> str:
        """Fetch the Telegram channel web preview HTML."""
        response = self.session.get(self.CHANNEL_URL, timeout=15)
        response.raise_for_status()
        return response.text

    # ---- Step 2: Extract image URLs from posts ----

    def extract_image_urls(self, html_content: str, max_images: int = 10) -> List[Dict]:
        """Extract image URLs from the latest posts.

        Returns list of dicts with: url, date, post_text, post_id
        """
        soup = BeautifulSoup(html_content, "html.parser")
        image_data = []

        # Each post is a .tgme_widget_message
        for post in soup.find_all(class_="tgme_widget_message"):
            # Extract post date
            date_tag = post.find("time")
            post_date = ""
            if date_tag:
                post_date = date_tag.get("datetime", "")
                if not post_date:
                    post_date = date_tag.get_text(strip=True)

            # Extract post text
            text_div = post.find(class_="tgme_widget_message_text")
            post_text = text_div.get_text(strip=True) if text_div else ""

            # Find the single post link for fallback
            single_link = post.find("a", class_="tgme_widget_message_date")
            post_id = ""
            if single_link:
                href = single_link.get("href", "")
                if "/matrixfood/" in href:
                    post_id = href.split("/matrixfood/")[-1].split("?")[0]

            # Find image URLs from photo_wrap elements (background-image style)
            photo_wraps = post.find_all("a", class_="tgme_widget_message_photo_wrap")
            for wrap in photo_wraps:
                style = wrap.get("style", "")
                url_match = re.search(r'url\([\"\']?([^)]+)[\"\']?\)', style)
                if url_match:
                    url = url_match.group(1)
                    image_data.append({
                        "url": url,
                        "date": post_date,
                        "post_text": post_text,
                        "post_id": post_id,
                    })

            if len(image_data) >= max_images:
                break

        return image_data[:max_images]

    # ---- Step 3: Download images ----

    def download_image(self, url: str):
        """Download an image from URL and return as PIL Image."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return img
        except Exception as e:
            print(f"Error downloading image {url[:60]}...: {e}")
            return None

    def download_image_to_file(self, url: str, filepath: str) -> bool:
        """Download image and save to file. Returns True on success."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"Error downloading image: {e}")
            return False

    # ---- Step 4: OCR on images ----

    def ocr_image(self, image, lang: str = "rus+eng") -> str:
        """Run OCR on a PIL Image and return extracted text."""
        if not OCR_AVAILABLE:
            return ""

        # Preprocess: convert to grayscale for better OCR
        gray = image.convert('L')

        # Run Tesseract OCR
        text = pytesseract.image_to_string(gray, lang=lang)
        return text

    def ocr_image_file(self, filepath: str, lang: str = "rus+eng") -> str:
        """Run OCR on an image file and return extracted text."""
        if not OCR_AVAILABLE:
            print("Error: OCR libraries not available. Install Pillow and pytesseract.")
            return ""

        image = Image.open(filepath)
        return self.ocr_image(image, lang)

    # ---- Step 5: Parse OCR text into menu items ----

    def parse_menu_from_ocr(self, ocr_text: str, date: str = "") -> List[MenuItem]:
        """Parse OCR-extracted text into structured menu items."""
        return self.ocr_parser.parse_ocr_text(ocr_text, date)

    # ---- Full pipeline ----

    def scrape_today_menu(self) -> List[Dict]:
        """Full pipeline: scrape channel -> extract images -> OCR -> parse menu.

        Returns list of menu item dicts.
        Falls back to sample data if images can't be downloaded.
        """
        # Step 1: Fetch channel
        try:
            html = self.fetch_channel()
            print(f"Fetched channel: {len(html)} bytes")
        except Exception as e:
            print(f"Error fetching channel: {e}")
            return self.parse_sample_menu()

        # Step 2: Extract image URLs from recent posts (up to 5 menu images)
        image_data = self.extract_image_urls(html, max_images=5)

        if not image_data:
            print("No menu images found in channel.")
            return self.parse_sample_menu()

        print(f"Found {len(image_data)} menu images")

        # Step 3-5: Process images (start from most recent)
        all_items = []
        for img_info in image_data:
            url = img_info["url"]
            post_date = img_info["date"]
            post_text = img_info["post_text"]

            print(f"\nProcessing: {post_date} | {post_text[:60]}...")
            print(f"  Image: {url[:70]}...")

            image = self.download_image(url)
            if not image:
                continue

            ocr_text = self.ocr_image(image)
            if not ocr_text.strip():
                print("  OCR returned empty text")
                continue

            print(f"  OCR text ({len(ocr_text)} chars):")
            # Print first few lines
            for line in ocr_text.strip().split('\n')[:8]:
                print(f"    {line}")
            if len(ocr_text.strip().split('\n')) > 8:
                print("    ...")

            items = self.parse_menu_from_ocr(ocr_text, post_date[:10] if post_date else "")
            if items:
                print(f"  Extracted {len(items)} items: {[i.name for i in items]}")
                all_items.extend(items)
            else:
                print("  No items extracted from this image")

        if not all_items:
            print("\nNo menu items extracted from OCR. Falling back to sample data.")
            return self.parse_sample_menu()

        print(f"\nTotal: extracted {len(all_items)} menu items")
        return [item.to_dict() for item in all_items]

    def scrape_from_image_file(self, filepath: str, date: str = "") -> List[Dict]:
        """Scrape menu from a local image file."""
        print(f"Processing local image: {filepath}")

        ocr_text = self.ocr_image_file(filepath)
        if not ocr_text.strip():
            print("OCR returned empty text")
            return self.parse_sample_menu()

        print(f"OCR text ({len(ocr_text)} chars):")
        for line in ocr_text.strip().split('\n')[:15]:
            print(f"  {line}")

        items = self.parse_menu_from_ocr(ocr_text, date)
        if not items:
            print("No menu items extracted")
            return self.parse_sample_menu()

        print(f"\nExtracted {len(items)} menu items:")
        return [item.to_dict() for item in items]

    def scrape_from_text(self, text: str, date: str = "") -> List[Dict]:
        """Parse menu directly from text (e.g., pasted OCR output)."""
        items = self.parse_menu_from_ocr(text, date)
        return [item.to_dict() for item in items]

    # ---- Fallback ----

    def parse_sample_menu(self) -> List[Dict]:
        """Fallback: parse a sample menu for testing/demo."""
        sample_items = [
            MenuItem("Цезарь с курицей", "salad", 180, "Classic Caesar salad with chicken", ["lettuce", "chicken", "parmesan", "croutons"], "200g"),
            MenuItem("Борщ", "soup", 120, "Traditional beet soup", ["beet", "cabbage", "potato", "beef"], "300ml"),
            MenuItem("Куриная грудка", "main course", 200, "Grilled chicken breast", ["chicken"], "250g"),
            MenuItem("Гречка", "side dish", 80, "Buckwheat", ["buckwheat"], "200g"),
            MenuItem("Компот", "drink", 50, "Dried fruit compote", ["dried fruits", "sugar"], "300ml"),
            MenuItem("Шарлотка", "dessert", 90, "Apple pie", ["flour", "apple", "sugar", "eggs"], "150g"),
        ]
        return [item.to_dict() for item in sample_items]


def main():
    """Main entry point with CLI argument support."""
    import argparse

    parser = argparse.ArgumentParser(description="Matrix Cafe Menu Scraper")
    parser.add_argument("--image", type=str, help="Path to local menu image file")
    parser.add_argument("--text", type=str, help="Pasted OCR text to parse")
    parser.add_argument("--date", type=str, default="", help="Menu date (YYYY-MM-DD)")
    args = parser.parse_args()

    scraper = MatrixCafeScraper()

    if args.image:
        # Mode: local image file
        menu = scraper.scrape_from_image_file(args.image, args.date)
    elif args.text:
        # Mode: pasted text
        menu = scraper.scrape_from_text(args.text, args.date)
    else:
        # Mode: full pipeline
        menu = scraper.scrape_today_menu()

    print(f"\n{'='*60}")
    print(f"MENU ({len(menu)} items)")
    print(f"{'='*60}")
    print(json.dumps(menu, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
