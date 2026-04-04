FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper/ scraper/
COPY database/ database/
COPY nanobot/ nanobot/

CMD ["python", "-u", "nanobot/bot.py"]
