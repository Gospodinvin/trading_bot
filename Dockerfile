FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем простую заглушку для talib
RUN echo 'import numpy as np
import pandas as pd

def RSI(close, timeperiod=14):
    return 50.0

def SMA(close, timeperiod):
    if len(close) < timeperiod:
        return np.mean(close) if len(close) > 0 else 0
    return np.mean(close[-timeperiod:])

def MACD(close, fastperiod=12, slowperiod=26, signalperiod=9):
    return 0.0, 0.0, 0.0

def EMA(close, timeperiod):
    if len(close) < timeperiod:
        return np.mean(close) if len(close) > 0 else 0
    return np.mean(close[-timeperiod:])

def BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2):
    if len(close) < timeperiod:
        avg = np.mean(close) if len(close) > 0 else 0
        return avg, avg, avg
    sma = np.mean(close[-timeperiod:])
    std = np.std(close[-timeperiod:])
    return sma + std*2, sma, sma - std*2

def STOCH(high, low, close, fastk_period=14):
    return 50.0, 50.0

def ATR(high, low, close, timeperiod=14):
    return 0.01' > /usr/local/lib/python3.11/site-packages/talib.py

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
