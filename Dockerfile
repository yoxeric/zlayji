FROM node:20-bookworm

USER root

ENV DEBIAN_FRONTEND=noninteractive

# 1. Install system dependencies for Playwright/Chromium and Python 3.11
# Debian Bookworm comes with Python 3.11, which meets crawl4ai's requirement (3.10+)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv python3-dev build-essential libffi-dev \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 fonts-freefont-ttf curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Install n8n globally
RUN npm install -g n8n@latest

# 3. Create a virtual environment for Python (Best practice to avoid conflicts)
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 4. Install scraping libraries
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir crawl4ai instagrapi gallery-dl playwright
# Install chromium for Playwright
RUN playwright install chromium

# 5. Set environment variables for n8n
ENV N8N_PYTHON_INTERPRETER=$VIRTUAL_ENV/bin/python

# 6. Set up a compatibility script for the official entrypoint
# This allows us to keep the docker-compose.yml 'command' unchanged
RUN echo '#!/bin/sh\nexec n8n "$@"' > /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# 7. Copy Python worker scripts
COPY --chown=node:node scripts/ /opt/scripts/
RUN chmod +x /opt/scripts/*.py

# Set working directory to n8n default
WORKDIR /home/node
USER node

# Expose n8n port
EXPOSE 5678

ENTRYPOINT ["/docker-entrypoint.sh"]