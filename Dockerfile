FROM python:3.12-slim

# Nastavení pracovního adresáře
WORKDIR /app

# Instalace potřebných balíčků pro pyodbc a ODBC driver 18
RUN apt-get update && apt-get install -y \
    curl gnupg2 apt-transport-https gcc g++ \
    unixodbc-dev \
 && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
 && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Zkopírování requirements.txt a instalace závislostí
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Zkopírování celé aplikace
COPY . .

# Otevření portu (Heroku nastavuje proměnnou PORT automaticky)
EXPOSE 5000

# Spuštění aplikace pomocí gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
