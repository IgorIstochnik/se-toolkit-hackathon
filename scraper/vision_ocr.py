"""
Vision LLM OCR for Matrix Cafe Menu

Uses GPT-4o (or any OpenAI-compatible vision model) to OCR menu images.
Much more accurate than Tesseract for styled menu images.

Usage:
    # Set API key and run
    OPENAI_API_KEY=sk-... python scraper/vision_ocr.py --image menu.jpg

    # Or use any OpenAI-compatible endpoint
    OPENAI_API_KEY=xxx OPENAI_BASE_URL=http://localhost:11434/v1 python scraper/vision_ocr.py --image menu.jpg
"""

import os
import sys
import json
import base64
from typing import List, Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from scraper.scraper import MenuItem, MenuImageOCR


VISION_OCR_PROMPT = """You are an OCR system specialized in reading Russian cafe menus.
Look at this menu image and extract ALL menu items as a JSON array.

For each item, extract:
- "name": the dish name in Russian (before any "/" separator, remove decorative symbols like •, }, ©)
- "price": the price as a number (ignore "₽", "руб", "P", "rp" suffixes)
- "weight": the weight/volume if visible (e.g. "200g", "300ml", or empty string)

Rules:
- Extract ONLY actual dish names, not headers like "MENU", "ОБЕД", "КОМПЛЕКСНЫЙ ОБЕД", "Set lunch"
- Ignore the English translations after "/" - take only the Russian name before "/"
- Prices should be reasonable (50-500₽ range for cafe food, not 2501 or 1590)
- If "250" is followed by "₽" or "руб" or "P" or "p" or "rp", the price is 250 (not 2501)
- If "150" is followed by such suffix, the price is 150 (not 1500)
- Return ONLY valid JSON, no markdown, no explanation

Example output:
[{"name":"Цезарь с курицей","price":180,"weight":"200g"},{"name":"Борщ","price":120,"weight":"300ml"}]
"""


class VisionOCR:
    """OCR menu images using GPT-4 Vision API."""

    def __init__(self, model: str = "gpt-4o", api_key: str = None, base_url: str = None):
        if not OPENAI_AVAILABLE:
            raise ImportError("Install openai: pip install openai")

        self.model = model
        self.client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
        )

    def ocr_image(self, image_path: str) -> List[Dict]:
        """OCR a menu image and return parsed menu items."""
        # Read and encode image
        with open(image_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_OCR_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            temperature=0,
            max_tokens=2000,
        )

        # Parse JSON response
        text = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        try:
            items = json.loads(text)
            return items if isinstance(items, list) else []
        except json.JSONDecodeError:
            print(f"Failed to parse JSON from response:\n{text[:500]}")
            return []


def vision_ocr_file(image_path: str, date: str = "", model: str = "gpt-4o") -> List[Dict]:
    """Convenience function: OCR a file and return menu items."""
    if not OPENAI_AVAILABLE:
        print("Error: openai not installed. Run: pip install openai")
        return []

    ocr = VisionOCR(model=model)
    items = ocr.ocr_image(image_path)

    result = []
    for item in items:
        result.append({
            "name": item.get("name", ""),
            "meal_type": "other",
            "price": item.get("price", 0),
            "weight": item.get("weight", ""),
            "date": date,
        })

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Vision LLM OCR for menu images")
    parser.add_argument("--images", nargs="+", required=True, help="Menu image files")
    parser.add_argument("--date", default="", help="Menu date (YYYY-MM-DD)")
    parser.add_argument("--model", default="gpt-4o", help="Vision model to use")
    args = parser.parse_args()

    all_items = []
    for image_path in args.images:
        print(f"Processing: {image_path}")
        items = vision_ocr_file(image_path, args.date, args.model)
        print(f"  Extracted {len(items)} items")
        for item in items:
            print(f"    {item['name']} - {item['price']}₽")
        all_items.extend(items)

    print(f"\nTotal: {len(all_items)} items")
    print(json.dumps(all_items, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
