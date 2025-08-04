# Dockerfile for Railway deployment
FROM python:3.9-slim

# Install Chrome dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install all dependencies including webdriver-manager
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir webdriver-manager && \
    python -c "from webdriver_manager.chrome import ChromeDriverManager; print('webdriver-manager installed successfully')"

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TZ=Pacific/Auckland
ENV WDM_LOG_LEVEL=0
ENV WDM_LOCAL=1

# Create necessary directories
RUN mkdir -p onsen_exports fallback_logs debug_output

# Run the scheduler
CMD ["python3", "scheduler_fixed.py"]
