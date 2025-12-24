import pandas as pd
import numpy as np

class SimpleIndicators:
    """Упрощенные реализации технических индикаторов"""
    
    @staticmethod
    def rsi(prices, period=14):
        """RSI индикатор"""
        if len(prices) < period:
            return 50.0
        
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        for i in range(period, len(deltas)):
            delta = deltas[i]
            if delta >= 0:
                up = (up * (period - 1) + delta) / period
                down = (down * (period - 1)) / period
            else:
                up = (up * (period - 1)) / period
                down = (down * (period - 1) - delta) / period
        
        if down == 0:
            return 100.0
        rs = up / down
        return 100.0 - (100.0 / (1.0 + rs))
    
    @staticmethod
    def sma(prices, period):
        """Простое скользящее среднее"""
        if len(prices) < period:
            return np.mean(prices) if len(prices) > 0 else 0
        return np.mean(prices[-period:])
    
    @staticmethod
    def ema(prices, period):
        """Экспоненциальное скользящее среднее"""
        if len(prices) < period:
            return np.mean(prices) if len(prices) > 0 else 0
        
        alpha = 2 / (period + 1)
        ema_val = prices[0]
        
        for price in prices[1:]:
            ema_val = price * alpha + ema_val * (1 - alpha)
        
        return ema_val
    
    @staticmethod
    def macd(prices, fast=12, slow=26, signal=9):
        """MACD индикатор"""
        if len(prices) < slow:
            return 0, 0, 0
        
        ema_fast = SimpleIndicators._ema_series(prices, fast)
        ema_slow = SimpleIndicators._ema_series(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = SimpleIndicators._ema_series(macd_line, signal)
        histogram = macd_line - signal_line
        
        return macd_line[-1], signal_line[-1], histogram[-1]
    
    @staticmethod
    def _ema_series(data, period):
        """Вспомогательная функция для расчета EMA ряда"""
        alpha = 2 / (period + 1)
        ema_vals = np.zeros_like(data, dtype=float)
        ema_vals[0] = data[0]
        
        for i in range(1, len(data)):
            ema_vals[i] = data[i] * alpha + ema_vals[i-1] * (1 - alpha)
        
        return ema_vals
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """Полосы Боллинджера"""
        if len(prices) < period:
            sma = np.mean(prices) if len(prices) > 0 else 0
            return sma, sma, sma
        
        sma = SimpleIndicators.sma(prices, period)
        std = np.std(prices[-period:])
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower

# Создаем глобальный экземпляр
indicators = SimpleIndicators()
