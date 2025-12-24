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

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Создаем заглушку для talib
RUN echo "import numpy as np
import pandas as pd

def RSI(close, timeperiod=14):
    return np.full_like(close, 50.0)

def SMA(close, timeperiod):
    return pd.Series(close).rolling(window=timeperiod).mean().values

def MACD(close, fastperiod=12, slowperiod=26, signalperiod=9):
    return np.zeros_like(close), np.zeros_like(close), np.zeros_like(close)

def EMA(close, timeperiod):
    return pd.Series(close).ewm(span=timeperiod, adjust=False).mean().values

def BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2):
    sma = pd.Series(close).rolling(window=timeperiod).mean()
    return sma.values, sma.values, sma.values

def STOCH(high, low, close, fastk_period=14):
    return np.full_like(close, 50.0), np.full_like(close, 50.0)

def ATR(high, low, close, timeperiod=14):
    return np.full_like(close, 0.01)" > /usr/local/lib/python3.11/site-packages/talib.py

# Создаем заглушку для tensorflow (если код его импортирует)
RUN echo "def __getattr__(name):
    return None" > /usr/local/lib/python3.11/site-packages/tensorflow.py

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
