FROM python:3.12-slim-bookworm

ENV ACCEPT_EULA=Y
ENV DEBIAN_FRONTEND=noninteractive

# Závislosti + přidání MS repa (moderní způsob přidání klíče)
RUN apt-get update && apt-get install -y \
    curl gnupg2 apt-transport-https gcc g++ \
    unixodbc-dev ca-certificates libssl3 libgssapi-krb5-2 libicu72 \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor \
        | tee /etc/apt/trusted.gpg.d/microsoft.gpg > /dev/null \
    && curl -sSL https://packages.microsoft.com/config/debian/12/prod.list \
        -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pracovní adresář
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD gunicorn --bind 0.0.0.0:${PORT:-5000} app:app
