FROM debian:trixie-slim

RUN echo "deb [trusted=yes] http://archive.raspberrypi.org/debian/ trixie main" > /etc/apt/sources.list.d/raspberrypi.list

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3 \
    python3-pip \
    python3-dev \
    python3-smbus \
    python3-lgpio \
    python3-picamera2 \
    libgl1 \
    libglib2.0-0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    libcamera-tools \
    gstreamer1.0-libcamera \
    gpiod \
    libgpiod-dev \
    i2c-tools \
    libi2c-dev \
    swig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

COPY . .

ENV MAVLINK20=1
ENV PYTHONUNBUFFERED=1

CMD ["python3", "main.py"]