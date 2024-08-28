#FROM balenalib/raspberrypi3-debian-python:3.7
FROM balenalib/raspberrypi3

RUN [ "cross-build-start" ]

RUN install_packages \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    libopenjp2-7-dev \
    zlib1g-dev \
    libatlas-base-dev \
    wget \
    libboost-python1.74.0 \
    curl \
    libcurl4-openssl-dev \
    libldap2-dev \
    libgtkmm-3.0-dev \
    libarchive-dev \
    libcurl4-openssl-dev \
    intltool \
    # Added from tensor flow support
    g++-10
# Required for OpenCV
#RUN install_packages \
    # Hierarchical Data Format
#    libhdf5-dev libhdf5-serial-dev \
    # for image files
#    libjpeg-dev libtiff5-dev libjasper-dev libpng-dev \
    # for video files
#    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    # for gui
#    libqt4-test libqtgui4 libqtwebkit4 libgtk2.0-dev \
    # high def image processing
#    libilmbase-dev libopenexr-dev

# Required for OpenCV
RUN install_packages \
    # Hierarchical Data Format
    libhdf5-dev libhdf5-serial-dev \
    # for image files
    libjpeg-dev libtiff5-dev libjasper-dev libpng-dev \
    # for video files
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    # for gui
    libqt5test5 libqt5gui5 libqt5webkit5 libgtk2.0-dev \
    # high def image processing
    libilmbase-dev libopenexr-dev \
    # Added
    libopenblas-base libopenblas-dev

# Install Python packages
COPY /requirements_pinwheel.txt ./
COPY /requirements.txt ./
#RUN python3 -m ensurepip
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade setuptools
RUN pip3 install --trusted-host www.piwheels.org --index-url=https://www.piwheels.org/simple -r requirements_pinwheel.txt
#RUN pip3 install --trusted-host pypi.org --index-url=https://pypi.org/simple -r requirements_pinwheel.txt
#RUN pip3 install --trusted-host www.piwheels.org --index-url=https://www.piwheels.org/simple -r requirements.txt
RUN pip3 install --trusted-host pypi.org --index-url=https://pypi.org/simple -r requirements.txt

COPY app /app

# Expose the port
EXPOSE 80

# Set the working directory
WORKDIR /app

RUN [ "cross-build-end" ]

# Run the flask server for the endpoints
#CMD python -u app.py

ENTRYPOINT [ "python3", "-u", "./app.py" ]
