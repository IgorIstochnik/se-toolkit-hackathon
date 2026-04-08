"""
Matrix Cafe Menu Scraper via Telegram API (Telethon)

Connects to Telegram via MTProto to download menu photos from @matrixfood channel.
Uses MTProto proxy to bypass connection restrictions.

Setup:
    pip install telethon cryptg Pillow pytesseract
    sudo apt install -y tesseract-ocr tesseract-ocr-rus

Usage:
    # First-time login (creates session)
    python scraper/scraper_telethon.py --login

    # Scrape menu
    python scraper/scraper_telethon.py
"""

import asyncio
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

try:
    from telethon import TelegramClient
    from telethon.network import ConnectionTcpMTProxy
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    Image = None
    pytesseract = None
    OCR_AVAILABLE = False

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper.scraper import MenuItem, MenuImageOCR


# ============================================================
# TELEGRAM API CONFIGURATION
# Get credentials at https://my.telegram.org
# MTProto proxy: (host, port, secret_hex)
# ============================================================
TELEGRAM_CONFIG = {
    "api_id": int(os.environ.get("TG_API_ID", "36586474")),
    "api_hash": os.environ.get("TG_API_HASH", "74ce76defbf51a85fdc33251683a12b5"),
    "channel": "matrixfood",
    "session_name": "matrix_scraper",
    # MTProto proxy (host, port, secret_hex)
    "proxy": (
        os.environ.get("MTROTO_HOST", "89.169.167.123"),
        int(os.environ.get("MTROTO_PORT", "443")),
        os.environ.get("MTROTO_SECRET", "eeb827aa7dd083babc9a303f21c9f04e09766b2e7275"),
    )
}


class TelethonMenuScraper:
    """Scraper using Telethon MTProto API with SOCKS5 proxy."""

    def __init__(self, config: Dict = None):
        self.config = config or TELEGRAM_CONFIG
        self.ocr_parser = MenuImageOCR()

    def _create_client(self) -> TelegramClient:
        """Create TelegramClient with MTProto proxy."""
        proxy = self.config["proxy"]

        # Telethon MTProto proxy format:
        # (proxy_type_string, host, port, secret)
        mtproto_proxy = ("mtproto", proxy[0], proxy[1], proxy[2])

        return TelegramClient(
            self.config["session_name"],
            self.config["api_id"],
            self.config["api_hash"],
            proxy=mtproto_proxy,
            connection_retries=10,
            retry_delay=2,
        )

    async def download_recent_menus(self, limit: int = 5) -> List[Dict]:
        """Download recent menu photos from @matrixfood channel."""
        if not TELETHON_AVAILABLE:
            print("Error: Telethon not installed. Run: pip install telethon")
            return []

        client = self._create_client()
        proxy = self.config["proxy"]
        print(f"Connecting to Telegram via MTProto proxy {proxy[0]}:{proxy[1]}...")

        try:
            await client.connect()

            if not await client.is_user_authorized():
                print("Not authorized. Run with --login first:")
                print("  python scraper/scraper_telethon.py --login")
                return []

            me = await client.get_me()
            print(f"Connected as: {me.first_name}")

            print(f"Fetching recent messages from @{self.config['channel']}...")
            channel = await client.get_entity(self.config["channel"])
            print(f"Found channel: {channel.title}")

            results = []
            photo_count = 0

            async for msg in client.iter_messages(channel, limit=limit):
                if not msg.photo:
                    continue

                date_str = msg.date.strftime("%Y-%m-%d") if msg.date else ""
                text = msg.text or ""

                print(f"\nMessage {msg.id} | {date_str}")
                if text:
                    preview = text[:100].replace('\n', ' ')
                    print(f"  Text: {preview}...")

                photo_path = f"/tmp/menu_{msg.id}.jpg"
                try:
                    await msg.download_media(photo_path)
                    print(f"  Photo saved: {photo_path}")
                    photo_count += 1
                    results.append({
                        "photo_path": photo_path,
                        "date": date_str,
                        "post_text": text,
                        "message_id": msg.id,
                    })
                except Exception as e:
                    print(f"  Download error: {e}")

            print(f"\nDownloaded {photo_count} menu photo(s)")
            return results

        except Exception as e:
            print(f"Error: {e}")
            return []
        finally:
            await client.disconnect()

    async def ocr_photos(self, photos: List[Dict]) -> List[MenuItem]:
        """OCR downloaded photos and parse menu items."""
        if not OCR_AVAILABLE:
            print("Error: OCR not available.")
            print("  pip install Pillow pytesseract")
            print("  sudo apt install tesseract-ocr tesseract-ocr-rus")
            return []

        all_items = []
        for photo_info in photos:
            path = photo_info["photo_path"]
            date = photo_info["date"]

            print(f"\nOCR processing: {path}")
            try:
                image = Image.open(path)
                gray = image.convert('L')
                text = pytesseract.image_to_string(gray, lang='rus+eng')

                if not text.strip():
                    print("  OCR returned empty text")
                    continue

                items = self.ocr_parser.parse_ocr_text(text, date)
                if items:
                    print(f"  Extracted {len(items)} items")
                    for item in items:
                        print(f"    [{item.meal_type}] {item.name} - {item.price}₽")
                    all_items.extend(items)
                else:
                    print("  No menu items found in OCR text")
                    for line in text.strip().split('\n')[:5]:
                        print(f"    {line}")

            except Exception as e:
                print(f"  OCR error: {e}")

        return all_items

    def get_sample_menu(self) -> List[Dict]:
        """Fallback sample menu."""
        from scraper.scraper import MatrixCafeScraper
        return MatrixCafeScraper().parse_sample_menu()


async def login():
    """Interactive login to create session file."""
    config = TELEGRAM_CONFIG

    client = TelegramClient(
        config["session_name"],
        config["api_id"],
        config["api_hash"],
        proxy=config["proxy"],
    )

    print("Starting login via proxy...")
    await client.start()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (phone: {me.phone})")
    print("Session saved. You can now run the scraper.")
    await client.disconnect()


async def main():
    """Main scraper entry point."""
    if "--login" in sys.argv:
        await login()
        return

    scraper = TelethonMenuScraper()

    # Download recent menu photos
    photos = await scraper.download_recent_menus(limit=5)

    if not photos:
        print("\nNo photos downloaded. Falling back to sample data.")
        menu = scraper.get_sample_menu()
        print(json.dumps(menu, indent=2, ensure_ascii=False))
        return

    # OCR and parse
    items = await scraper.ocr_photos(photos)

    if not items:
        print("\nNo menu items extracted. Falling back to sample data.")
        menu = scraper.get_sample_menu()
        print(json.dumps(menu, indent=2, ensure_ascii=False))
        return

    # Output parsed menu
    menu_dicts = [item.to_dict() for item in items]
    print(f"\n{'='*60}")
    print(f"MENU ({len(menu_dicts)} items)")
    print(f"{'='*60}")
    print(json.dumps(menu_dicts, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
