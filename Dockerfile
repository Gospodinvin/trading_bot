FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости для OpenCV
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

COPY . .

# Создаем заглушку для talib если не установлен
RUN python -c "
import os
if not os.path.exists('/usr/local/lib/python3.11/site-packages/talib.py'):
    stub = '''
import numpy as np
import pandas as pd

def RSI(close, timeperiod=14):
    if len(close) < timeperiod:
        return np.full_like(close, 50.0)
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    avg_gain = pd.Series(gain).rolling(timeperiod).mean().values
    avg_loss = pd.Series(loss).rolling(timeperiod).mean().values
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def SMA(close, timeperiod):
    return pd.Series(close).rolling(window=timeperiod).mean().values

def MACD(close, fastperiod=12, slowperiod=26, signalperiod=9):
    ema_fast = pd.Series(close).ewm(span=fastperiod).mean()
    ema_slow = pd.Series(close).ewm(span=slowperiod).mean()
    macd = ema_fast - ema_slow
    signal = macd.ewm(span=signalperiod).mean()
    hist = macd - signal
    return macd.values, signal.values, hist.values

def EMA(close, timeperiod):
    return pd.Series(close).ewm(span=timeperiod, adjust=False).mean().values

def BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2):
    sma = pd.Series(close).rolling(window=timeperiod).mean()
    std = pd.Series(close).rolling(window=timeperiod).std()
    upper = sma + (std * nbdevup)
    lower = sma - (std * nbdevdn)
    return upper.values, sma.values, lower.values

def STOCH(high, low, close, fastk_period=14):
    lowest_low = pd.Series(low).rolling(fastk_period).min()
    highest_high = pd.Series(high).rolling(fastk_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(3).mean()
    return k.values, d.values

def ATR(high, low, close, timeperiod=14):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(timeperiod).mean()
    return atr.values
'''
    with open('/usr/local/lib/python3.11/site-packages/talib.py', 'w') as f:
        f.write(stub)
"

# Устанавливаем порт по умолчанию
ENV PORT=8000

# Запускаем через Python
CMD ["python", "start.py"]
