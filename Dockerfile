FROM python:3.12-slim

WORKDIR /app

# Instalace závislostí + přidání Microsoft klíče správně
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    apt-transport-https \
    gcc \
    g++ \
    unixodbc-dev \
    ca-certificates \
    libssl3 \
    libgssapi-krb5-2 \
    libicu72 \
 && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && apt-get install -y msodbcsql18 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
