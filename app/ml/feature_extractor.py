import pandas as pd
import numpy as np

class FeatureExtractor:
    def __init__(self):
        pass
    
    def extract_features(self, ohlc_data, selected_indicators=None):
        """Упрощенная версия для тестирования"""
        if not ohlc_data:
            return self._get_default_features()
        
        features = {}
        
        # Базовые фичи
        if len(ohlc_data) >= 2:
            features['price_change'] = ohlc_data[-1]['close'] - ohlc_data[-2]['close']
            features['price_change_pct'] = features['price_change'] / ohlc_data[-2]['close'] * 100
        
        # Простые индикаторы
        closes = [c['close'] for c in ohlc_data[-20:]]
        if len(closes) >= 10:
            features['sma_10'] = np.mean(closes[-10:])
            features['sma_20'] = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        
        # Всегда добавляем значения по умолчанию
        features.update(self._get_default_features())
        
        return features
    
    def _get_default_features(self):
        """Возвращает значения по умолчанию"""
        return {
            'rsi': 50.0,
            'macd': 0.0,
            'macd_signal': 0.0,
            'macd_hist': 0.0,
            'bb_position': 0.5,
            'atr_pct': 1.0,
            'stoch_k': 50.0,
            'stoch_d': 50.0,
            'volatility': 0.01
        }
