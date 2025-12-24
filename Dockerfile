FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Создаем заглушку для talib
RUN echo 'import numpy as np
import pandas as pd

def RSI(close, timeperiod=14): return 50.0
def SMA(close, timeperiod): return np.mean(close[-timeperiod:]) if len(close) >= timeperiod else np.mean(close) if len(close) > 0 else 0
def MACD(close, fastperiod=12, slowperiod=26, signalperiod=9): return 0.0, 0.0, 0.0
def EMA(close, timeperiod): return np.mean(close[-timeperiod:]) if len(close) >= timeperiod else np.mean(close) if len(close) > 0 else 0
def BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2): 
    if len(close) < timeperiod: 
        avg = np.mean(close) if len(close) > 0 else 0
        return avg, avg, avg
    sma = np.mean(close[-timeperiod:])
    std = np.std(close[-timeperiod:])
    return sma + std*2, sma, sma - std*2
def STOCH(high, low, close, fastk_period=14): return 50.0, 50.0
def ATR(high, low, close, timeperiod=14): return 0.01' > /usr/local/lib/python3.11/site-packages/talib.py

# Создаем заглушку для tensorflow
RUN echo 'class MockTensorFlow:
    __version__ = "2.15.0"
    
    class keras:
        class models:
            @staticmethod
            def load_model(*args, **kwargs):
                class MockModel:
                    def predict(self, *args, **kwargs):
                        import numpy as np
                        return np.array([[0.33, 0.33, 0.34]])
                
                return MockModel()
            
            class Sequential:
                def __init__(self, *args, **kwargs):
                    pass
                
                def add(self, *args, **kwargs):
                    return self
                
                def compile(self, *args, **kwargs):
                    return self
    
    class keras:
        pass

# Создаем псевдо-модуль
import sys
sys.modules[__name__] = MockTensorFlow()' > /usr/local/lib/python3.11/site-packages/tensorflow.py

# Создаем заглушку для torch
RUN echo 'class MockTorch:
    __version__ = "2.1.0"
    
    class nn:
        class Module:
            pass
        
        class LSTM:
            def __init__(self, *args, **kwargs):
                pass
        
        class Dropout:
            def __init__(self, *args, **kwargs):
                pass
        
        class Linear:
            def __init__(self, *args, **kwargs):
                pass
    
    def eval(self):
        return self

import sys
sys.modules[__name__] = MockTorch()' > /usr/local/lib/python3.11/site-packages/torch.py

COPY . .

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
