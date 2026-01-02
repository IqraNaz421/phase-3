# FROM python:3.13-slim

# WORKDIR /app

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# COPY . .

# EXPOSE 8000

# CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]





# Stable Python version use karte hain
FROM python:3.11-slim

# System dependencies install karein (gcc aur build tools)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements copy aur install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki code copy karein
COPY . .

# Hugging Face default port 7860 use karta hai
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]