# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Set shell to bash for better error handling
SHELL ["/bin/bash", "-c"]

# Install system dependencies and browser
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome/Chromium based on architecture
RUN if [ "$(uname -m)" = "x86_64" ]; then \
        # Install Google Chrome for x86_64
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
        && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update \
        && apt-get install -y google-chrome-stable \
        && rm -rf /var/lib/apt/lists/*; \
    else \
        # Install Chromium for ARM64 and other architectures
        apt-get update \
        && apt-get install -y chromium \
        && ln -s /usr/bin/chromium /usr/bin/google-chrome \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Install ChromeDriver
RUN if [ "$(uname -m)" = "x86_64" ]; then \
        # Use ChromeDriver for x86_64
        CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | awk -F'.' '{print $1}') \
        && echo "Chrome version: $CHROME_VERSION" \
        && wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION}" -O /tmp/chromedriver_version \
        && CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version) \
        && echo "ChromeDriver version: $CHROMEDRIVER_VERSION" \
        && wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
        && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
        && rm /tmp/chromedriver.zip /tmp/chromedriver_version \
        && chmod +x /usr/local/bin/chromedriver; \
    else \
        # Use system ChromeDriver for ARM64
        apt-get update \
        && apt-get install -y chromium-driver \
        && ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver \
        && rm -rf /var/lib/apt/lists/*; \
    fi \
    && chromedriver --version

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs

# Verify installations
RUN echo "=== Verification ===" \
    && python --version \
    && google-chrome --version \
    && chromedriver --version \
    && echo "=== All installations verified ==="

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port for FastAPI
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden)
CMD ["python", "app.py"]
