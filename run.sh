#!/bin/bash
# Получаем порт из переменной окружения или используем 8000 по умолчанию
PORT=${PORT:-8000}

echo "Starting server on port: $PORT"

# Запускаем Gunicorn
exec gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT
