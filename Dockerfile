# Используем официальный образ Python 3.12 на базе Debian Linux
FROM python:3.12-slim

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости:
# - gcc, libpq-dev для psycopg2
# - другие возможные зависимости для Pillow, openpyxl, reportlab и т.д.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем Python-пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# (Опционально) собираем статику – если используется django.contrib.staticfiles
RUN python manage.py collectstatic --noinput

# Открываем порт (по умолчанию Gunicorn слушает 8000)
EXPOSE 8080

# Команда запуска: делаем миграции и стартуем сервер.
# Для продакшена лучше использовать gunicorn, для теста – runserver.
# Здесь оставим runserver на 0.0.0.0:8000, но с миграциями.
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 1bus.wsgi"]