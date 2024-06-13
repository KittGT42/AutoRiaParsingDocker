# Используйте подходящий базовый образ
FROM python:3.12-slim

# Установите системные зависимости, включая gcc, libpq-dev и другие необходимые пакеты
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg2 \
    libpq-dev \
    build-essential \
    postgresql-client \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Установите Poetry
RUN pip install poetry

# Скопируйте файлы для Poetry
COPY pyproject.toml poetry.lock /app/
WORKDIR /app

# Установите зависимости проекта с использованием правильной команды
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Скопируйте все файлы приложения
COPY . /app

# Установите Chrome и ChromeDriver для Selenium
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -y google-chrome-stable && rm -rf /var/lib/apt/lists/*
RUN wget https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip && mv chromedriver /usr/local/bin/chromedriver && chmod +x /usr/local/bin/chromedriver && rm chromedriver_linux64.zip

# Установите необходимые Python пакеты
RUN pip install selenium requests beautifulsoup4 psycopg2-binary schedule

# Определите точку входа
CMD ["poetry", "run", "python", "main1.py"]
