# Use a suitable ARM base image for Raspberry Pi
FROM balenalib/raspberrypi3-debian:latest

# Update system and install required system packages including Python, pip, gcc, g++, cmake, and ninja
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    gcc \
    g++ \
    cmake \
    ninja-build \
    libstdc++6 \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libopenjp2-7 \
    libopenexr-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libgtk-3-0 \
    liblapack-dev \
    libblas-dev \
    libatlas-base-dev \
    libopenblas-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies using pypi.org as the index
COPY requirements.txt .
RUN pip3 install --no-cache-dir --index-url https://pypi.org/simple -r requirements.txt

# Copy your application code
COPY app /app
WORKDIR /app

# Copy all .tflite files from the root directory into the /app directory
COPY *.tflite /app/

# Set the command to run your application
CMD ["python3", "./app.py"]


