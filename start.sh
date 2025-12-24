#!/bin/bash
# Получаем порт или используем 8000 по умолчанию
PORT=${PORT:-8080}
echo "Starting server on port: $PORT"
exec gunicorn app.main:app \
  --workers 2 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:$PORT
