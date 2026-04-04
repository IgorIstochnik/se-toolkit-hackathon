# Matrix Cafe Menu Helper

An LLM-powered nanobot that helps Innopolis University students choose meals at the Matrix cafe by parsing menus, showing prices, and recommending balanced meal combos.

## Demo

> _Screenshot of the nanobot recommending a meal combo_

![Demo placeholder - will be replaced with actual screenshot](demo-placeholder.png)

## Product Context

### End Users
Students and staff of Innopolis University who eat at the Matrix cafe.

### Problem
It can be hard to decide what to eat when you arrive at the cafe, especially when you want a balanced meal within your budget.

### Solution
A chat-based nanobot that:
- Scrapes the Matrix cafe Telegram channel (`@matrixfood`) where daily menus are posted as images
- Uses OCR (Tesseract) to extract text from menu images
- Shows today's menu with prices and meal types
- Recommends meals based on your preferences and budget
- Suggests balanced lunch combos (salad + soup + main + drink)

## Features

### Implemented (Version 1)
- ✅ Telegram channel scraper that extracts menu images from `@matrixfood`
- ✅ OCR-based menu text extraction (Tesseract with Russian + English support)
- ✅ Menu text parser that converts OCR output into structured items with sections (salads, soups, etc.)
- ✅ SQLite database for storing menu items with prices, ingredients, and meal types
- ✅ LLM-powered nanobot for meal recommendations
- ✅ Interactive CLI interface
- ✅ Filter by meal type (salad, soup, main course, drink, dessert)
- ✅ Filter by budget

### Implemented (Version 2)
- ✅ Balanced meal combo generator with budget awareness
- ✅ Menu scheduler for periodic auto-refresh
- ✅ Docker configuration with Tesseract OCR installed
- ✅ Deployment script (`./deploy.sh`)

### Not Yet Implemented
- [ ] Web UI frontend
- [ ] User preference learning over time

## Usage

### Prerequisites
- Python 3.11+
- pip

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the nanobot:
   ```bash
   python nanobot/bot.py
   ```

3. Interact with the bot:
   - Type `menu` to see today's menu
   - Ask for recommendations: "What should I eat today?"
   - Request combos: "Recommend a combo under 300₽"
   - Filter by type: "Show me salads"
   - Filter by budget: "I want something cheap"

### Example Queries
```
You: menu
Bot: Here's today's Matrix cafe menu:
  **SALAD**:
    • Цезарь с курицей - 180₽ 200g
      Classic Caesar salad with chicken
  **SOUP**:
    • Борщ - 120₽ 300ml
      Traditional beet soup
  ...

You: recommend a combo under 300₽
Bot: **Balanced Lunch Combo:**
  • Цезарь с курицей (salad) - 180₽
  • Борщ (soup) - 120₽
  
  **Total: 300₽**
```

## Deployment

### Requirements
- OS: Ubuntu 24.04 (or similar Linux)
- Docker and Docker Compose installed

### Step-by-Step Deployment

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd se-toolkit-hackathon
   ```

2. Build and start with Docker Compose:
   ```bash
   docker compose up -d
   ```

3. Access the nanobot:
   ```bash
   docker attach matrix-cafe-bot
   ```

### Manual Deployment (without Docker)

1. Ensure Python 3.11+ is installed:
   ```bash
   python3 --version
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the bot:
   ```bash
   python nanobot/bot.py
   ```

### Architecture
```
┌──────────────────────┐     ┌──────────────┐     ┌──────────────┐
│ Telegram Channel     │     │  SQLite DB   │     │  Nanobot     │
│ @matrixfood          │────>│  (menu.db)   │────>│  (CLI Agent) │
│ (menu images)        │     │              │     │              │
└──────────────────────┘     └──────────────┘     └──────────────┘
        │
        ▼
┌──────────────────────┐     ┌──────────────┐
│ Image Extractor      │────>│ Tesseract OCR│
│ (BS4 + requests)     │     │ (rus+eng)    │
└──────────────────────┘     └──────────────┘
```

## Project Structure
```
se-toolkit-hackathon/
├── scraper/
│   ├── scraper.py          # Menu scraping and parsing module
│   └── README.md
├── database/
│   ├── db.py               # SQLite database module
│   └── README.md
├── nanobot/
│   ├── bot.py              # LLM agent for meal recommendations
│   └── README.md
├── docker/
│   └── (Docker configs)
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Multi-service orchestration
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT License
├── .gitignore
└── README.md
```

## Tech Stack
- **Backend**: Python 3.11
- **Database**: SQLite
- **Agent**: Custom nanobot with intent parsing
- **Web Scraping**: BeautifulSoup + Requests
- **OCR**: Tesseract (Russian + English)
- **Image Processing**: Pillow
- **Deployment**: Docker Compose
