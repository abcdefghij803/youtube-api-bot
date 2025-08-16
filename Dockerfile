# ---- Base Image ----
FROM python:3.11-slim

# ---- Set working directory ----
WORKDIR /app

# ---- Install system dependencies ----
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Copy project files ----
COPY . /app

# ---- Install Python dependencies ----
RUN pip install --no-cache-dir -r requirements.txt

# ---- Expose port ----
EXPOSE 8080

# ---- Start app ----
CMD ["python", "main.py"]
