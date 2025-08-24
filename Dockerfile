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
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Default command shows help
CMD ["python", "-m", "bac_hunter.cli", "--help"]