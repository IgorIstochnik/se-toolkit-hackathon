"""
Matrix Cafe Menu Scraper

Scrapes and parses the Matrix cafe menu from Telegram channel.
Menu content is posted as images, so OCR is used to extract text.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re
import json
import os
import base64
import io

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    Image = None  # type: ignore
    pytesseract = None  # type: ignore
    OCR_AVAILABLE = False
    print("Warning: pytesseract or PIL not installed. OCR will fall back to sample data.")


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
    }

    # Price pattern: number followed by ₽ or руб
    PRICE_PATTERN = re.compile(r'(\d+)\s*(?:₽|руб\.?|rub|rub\.)', re.IGNORECASE)

    # Item line pattern: "item name - price" or "item name ... price"
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
        """Check if a line is a section header (e.g., 'Салаты').

        Section headers are typically short (<30 chars) and match known keywords.
        Lines that look like menu items (contain price, dash+price) are NOT headers.
        """
        line_lower = line.lower().strip()

        # If the line contains a price pattern, it's a menu item, not a header
        if self.PRICE_PATTERN.search(line):
            return None

        # Section headers are short and don't look like item names
        if len(line_lower) > 35:
            return None

        for header, meal_type in self.SECTION_HEADERS.items():
            # Match the header at the start or as the whole line
            if line_lower == header or line_lower.startswith(header) and len(line_lower) < len(header) + 5:
                return meal_type

        return None

    def _parse_item_line(self, line: str) -> Optional[MenuItem]:
        """Try to parse a menu item from a single OCR line."""
        for pattern in self.ITEM_LINE_PATTERNS:
            match = pattern.search(line)
            if match:
                name = match.group(1).strip()
                price = float(match.group(2))

                # Filter out noise: names should be reasonable length
                if len(name) < 2 or len(name) > 80:
                    continue

                # Skip lines that look like headers or dates
                if re.match(r'^\d{1,2}[./-]\d{1,2}', name):
                    continue

                # Skip very short suspicious matches
                if name.lower() in ['the', 'and', 'or', 'no', 'yes', 'да', 'нет']:
                    continue

                return MenuItem(
                    name=self._clean_name(name),
                    meal_type="other",
                    price=price
                )

        return None

    def _clean_name(self, name: str) -> str:
        """Clean up OCR noise from item name."""
        # Remove common OCR artifacts
        name = re.sub(r'[|!1]+$', '', name)  # trailing pipes/numbers
        name = re.sub(r'^[|!]+', '', name)   # leading pipes
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

    def extract_image_urls(self, html_content: str, max_images: int = 5) -> List[Tuple[str, str]]:
        """Extract image URLs from the latest posts.
        
        Returns list of (image_url, post_date) tuples, newest first.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        image_data = []

        # Each post is wrapped in .tgme_widget_message
        for post in soup.find_all("div", class_="tgme_widget_message"):
            # Extract post date
            date_tag = post.find("time", class_="tgme_widget_message_date")
            post_date = ""
            if date_tag:
                post_date = date_tag.get("datetime", "")
                if not post_date:
                    post_date = date_tag.get_text(strip=True)

            # Find all image URLs in this post
            photos = post.find_all("img", class_="tgme_widget_message_photo")
            for photo in photos:
                src = photo.get("src", "") or photo.get("data-src", "")
                if src:
                    image_data.append((src, post_date))

            if len(image_data) >= max_images:
                break

        return image_data[:max_images]

    # ---- Step 3: Download images ----

    def download_image(self, url: str):  # -> Optional[Image.Image]:
        """Download an image from URL and return as PIL Image."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
            return img
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            return None

    # ---- Step 4: OCR on images ----

    def ocr_image(self, image, lang: str = "rus+eng") -> str:  # image: Image.Image
        """Run OCR on a PIL Image and return extracted text."""
        if not OCR_AVAILABLE:
            return ""

        # Preprocess: convert to grayscale and increase contrast for better OCR
        gray = image.convert('L')

        # Run Tesseract OCR
        text = pytesseract.image_to_string(gray, lang=lang)
        return text

    # ---- Step 5: Parse OCR text into menu items ----

    def parse_menu_from_ocr(self, ocr_text: str, date: str = "") -> List[MenuItem]:
        """Parse OCR-extracted text into structured menu items."""
        return self.ocr_parser.parse_ocr_text(ocr_text, date)

    # ---- Main pipeline ----

    def scrape_today_menu(self) -> List[Dict]:
        """Full pipeline: scrape channel -> extract images -> OCR -> parse menu.
        
        Returns list of menu item dicts.
        """
        # Step 1: Fetch channel
        try:
            html = self.fetch_channel()
        except Exception as e:
            print(f"Error fetching channel: {e}")
            return self.parse_sample_menu()

        # Step 2: Extract image URLs (get the most recent post's images)
        image_data = self.extract_image_urls(html, max_images=5)

        if not image_data:
            print("No menu images found in channel.")
            return self.parse_sample_menu()

        # Step 3-5: Process each image
        all_items = []
        for img_url, post_date in image_data:
            print(f"Processing image: {img_url[:60]}... (date: {post_date})")

            image = self.download_image(img_url)
            if not image:
                continue

            ocr_text = self.ocr_image(image)
            if not ocr_text.strip():
                continue

            print(f"OCR text ({len(ocr_text)} chars):")
            print(ocr_text[:300])
            print("---")

            items = self.parse_menu_from_ocr(ocr_text, post_date)
            all_items.extend(items)

        if not all_items:
            print("No menu items extracted from OCR. Falling back to sample data.")
            return self.parse_sample_menu()

        print(f"Extracted {len(all_items)} menu items.")
        return [item.to_dict() for item in all_items]

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


if __name__ == "__main__":
    scraper = MatrixCafeScraper()

    print("=" * 60)
    print("Matrix Cafe Menu Scraper — Telegram Channel")
    print("=" * 60)

    menu = scraper.scrape_today_menu()
    print(f"\nMenu has {len(menu)} items:")
    print(json.dumps(menu, indent=2, ensure_ascii=False))
