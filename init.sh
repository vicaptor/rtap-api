#!/bin/bash

# Instalacja zależności systemowych
sudo dnf install -y \
    ffmpeg-devel \
    pkgconfig \
    gcc \
    python3-devel \
    redhat-rpm-config \
    zlib-devel \
    python3-pip \
    python3-venv

# Tworzenie wirtualnego środowiska
python3 -m venv venv
source venv/bin/activate

# Aktualizacja pip
pip install --upgrade pip setuptools wheel

# Instalacja zależności Python
pip install \
    aiohttp==3.9.3 \
    websockets==12.0 \
    opencv-python==4.9.0.80 \
    numpy==1.26.4 \
    PyYAML==6.0.1 \
    python-dotenv==1.0.1 \
    av==11.0.0

# Sprawdzenie instalacji
python3 -c "import av; print('PyAV installed successfully')"