FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Yahan 'backend/' lagana zaroori hai agar file root mein nahi hai
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pura backend folder copy karein
COPY backend/ .

#src folder ke andar main.py hai toh path ye hoga
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]