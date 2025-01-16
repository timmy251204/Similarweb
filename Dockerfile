# Use Python slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    xauth \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libxfixes3 \
    libxrender1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libasound2 \
    fonts-liberation \
    libappindicator1 \
    libnss3-dev \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libpango-1.0-0 \
    ca-certificates \
    --no-install-recommends

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r /app/requirements.txt
RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y xvfb
RUN apt-get install -qqy x11-apps
RUN apt-get install -y libnss3 \
                       libxss1 \
                       libasound2 \
                       fonts-noto-color-emoji
# Install Playwright and its browsers
RUN pip install playwright
RUN playwright install
RUN apt-get update && apt-get install -y xvfb
# Set the working directory
WORKDIR /app

# Copy the application code
COPY . /app
ENTRYPOINT ["/bin/sh", "-c", "/usr/bin/xvfb-run -a $@", ""]
# Add a display server (Xvfb) to support non-headless mode
CMD ["python crawler_tg.py ", ""]


