# Matrix Cafe Menu Helper

An LLM-powered nanobot that helps Innopolis University students choose meals at the Matrix cafe by parsing menus, showing prices, and recommending balanced meal combos.

## Demo

The bot displays today's Matrix cafe menu with prices, weights, and ingredients:

```
**SALAD**:
  • Салат Днестровский - 60₽ 120г
  • Салат Зеленый с ветчиной - 75₽ 120г
  • Салат Шопский - 175₽ 120г
  • Салат с курицей и ананасом - 150₽ 120г

**SOUP**:
  • Суп картофельный с горохом и курицей - 100₽ 250г
  • Щи Зеленые со шпинатом и яйцом - 115₽ 250г
  • Лагман с говядиной - 200₽ 250г

**MAIN COURSE**:
  • Голубцы - 110₽ 100г
  • Котлета куриная - 120₽ 100г
  • Чахохбили тушеная курица с овощами - 125₽ 125г
  • Свинина на шпажках в медовой глазури - 195₽ 100г
  • Филе горбуши с овощами - 250₽ 100г

**SIDE DISH**:
  • Перловка с зеленым горошком - 150₽ 150г
  • Рис отварной - 150₽ 150г

**DRINK**:
  • Напиток на выбор - 45₽

**BREAD**:
  • Хлеб Пшеничный - 0₽ 50г
  • Хлеб Сельский - 0₽ 50г
```

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
- ✅ Menu scraper with Telegram channel image extraction (`@matrixfood`)
- ✅ Menu image download and OCR processing pipeline
- ✅ Text-based menu parser supporting Russian cuisine format
- ✅ SQLite database storing menu items with prices, weights, and ingredients
- ✅ Multi-day menu support (04-07, 04-08, 04-09 populated)
- ✅ Interactive CLI nanobot for meal queries
- ✅ Filter by meal type (salad, soup, main course, side dish, drink, bread)
- ✅ Filter by budget
- ✅ Weight display (e.g., 120г, 250г)

### Implemented (Version 2)
- ✅ Balanced meal combo generator with budget awareness
- ✅ Ingredient display for each dish
- ✅ Menu scheduler for periodic auto-refresh
- ✅ Vision LLM OCR option (GPT-4o) for higher accuracy
- ✅ Docker configuration for all services
- ✅ Deployment script (`./deploy.sh`)
- ✅ Real data: 3 days of actual Matrix cafe menus (44+ unique items)

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

2. Install system dependencies (Tesseract OCR):
   ```bash
   sudo apt update
   sudo apt install -y tesseract-ocr tesseract-ocr-rus tesseract-ocr-eng
   ```

3. Create a virtual environment and install Python dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   > **Note:** If `python3 -m venv` is not available, install it first:
   > ```bash
   > sudo apt install python3.12-venv
   > ```

4. Run the bot:
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
- **Backend**: Python 3.12
- **Database**: SQLite (multi-day menu storage)
- **Agent**: Custom nanobot with intent parsing and combo generation
- **Web Scraping**: BeautifulSoup + Requests (Telegram channel `t.me/s/matrixfood`)
- **OCR**: Tesseract (rus+eng) + optional GPT-4o Vision API
- **Image Processing**: Pillow
- **Deployment**: Docker Compose (Tesseract + Python)
