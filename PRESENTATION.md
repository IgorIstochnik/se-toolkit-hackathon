# Matrix Cafe Menu Helper - Presentation Slides

## Slide 1: Title

**Matrix Cafe Menu Helper**
- Your Name
- your.name@innopolis.university
- Group XXX

---

## Slide 2: Context

**End User:** Innopolis University students eating at Matrix cafe

**Problem:** Hard to choose which meals to take when you come to the cafe

**Product Idea:** A chatbot that helps students choose meals by showing the cafe menu with prices and recommending balanced combos

---

## Slide 3: Implementation

**How we built it:**
- **Scraper:** Python + BeautifulSoup for menu parsing
- **Database:** SQLite for storing menu items with prices, types, ingredients
- **Agent:** Custom nanobot with intent parsing and recommendation logic

**Version 1:**
- Menu parser with sample data
- SQLite database
- Interactive CLI nanobot for meal recommendations

**Version 2:**
- Balanced meal combo generator (salad + soup + main + drink)
- Budget-aware recommendations
- Menu scheduler for auto-refresh
- Docker configuration for all services

**TA Feedback Addressed:**
- Made combo logic budget-aware
- Added filtering by meal type and price range
- Dockerized all services for easy deployment

---

## Slide 4: Demo

**[Pre-recorded video with voice-over - max 2 minutes]**

Show:
1. Starting the bot
2. Asking for today's menu
3. Requesting a combo under 300₽
4. Filtering by meal type (salads)
5. Budget query (cheap options)

---

## Slide 5: Links

**GitHub Repository:**
- URL: https://github.com/YOUR_USERNAME/se-toolkit-hackathon
- QR Code: [Generate QR code for repo URL]

**Deployed Product:**
- URL: http://YOUR_VM_IP:PORT
- QR Code: [Generate QR code for deployed product]
