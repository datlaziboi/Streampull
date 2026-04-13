FROM python:3.12-slim

# Install system dependencies: ffmpeg for yt-dlp merging
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Output directory will be mounted as a volume
RUN mkdir -p /output

EXPOSE 5000

CMD ["python", "app.py"]
