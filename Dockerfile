FROM python:3.9-slim

# Instalacja wymaganych pakietów systemowych
RUN apt-get update && apt-get install -y \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libopencv-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Utworzenie katalogu aplikacji
WORKDIR /app

# Kopiowanie plików projektu
COPY requirements.txt .
COPY rtap.py .

# Instalacja zależności Pythona
RUN pip install --no-cache-dir -r requirements.txt

# Uruchomienie serwera RTAP
CMD ["python", "rtap.py"]