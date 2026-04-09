FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper/ scraper/
COPY database/ database/
COPY nanobot/ nanobot/
COPY web/ web/

EXPOSE 8080
CMD ["python", "-u", "web/app.py", "--host", "0.0.0.0", "--port", "8080"]
