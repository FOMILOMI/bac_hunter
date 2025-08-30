# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# System deps for WeasyPrint (optional, non-fatal if not used)
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	libffi-dev \
	libpango-1.0-0 \
	libpangoft2-1.0-0 \
	libcairo2 \
	libgdk-pixbuf2.0-0 \
	libssl-dev \
	# For Playwright/Selenium chromium dependencies
	ca-certificates \
	wget \
	gnupg \
	libnss3 \
	libx11-6 \
	libx11-xcb1 \
	libxcb1 \
	libxcomposite1 \
	libxdamage1 \
	libxext6 \
	libxfixes3 \
	libxrandr2 \
	libgbm1 \
	libasound2 \
	libatk1.0-0 \
	libatk-bridge2.0-0 \
	libgtk-3-0 \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt \
	&& python -m playwright install --with-deps chromium || true

COPY . /app

# Expose API port
EXPOSE 9000

# Default command starts the web API
CMD ["python", "-m", "webapp.main"]