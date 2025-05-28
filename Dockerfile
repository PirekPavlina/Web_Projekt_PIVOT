FROM python:3.12-slim

# Nastav proměnnou prostředí pro neinteraktivní režim instalace
ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Nainstaluj systémové závislosti + ODBC driver 18
RUN apt-get update && apt-get install -y \
    curl gnupg2 apt-transport-https gcc g++ \
    unixodbc-dev ca-certificates \
    libssl3 libgssapi-krb5-2 libicu67 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pracovní adresář
WORKDIR /app

# Kopíruj requirements a nainstaluj Python závislosti
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopíruj celý zbytek aplikace
COPY . .

# Vystav port
EXPOSE 5000

# Spuštění přes gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
