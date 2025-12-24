"""
Упрощенный предсказатель без TensorFlow для обратной совместимости
"""
import numpy as np
from app.utils.logger import logger

class PricePredictor:
    def __init__(self):
        logger.info("Using mock predictor (TensorFlow disabled)")
        
    def predict(self, image_data, timeframe='5m', indicators=None, sensitivity='medium'):
        """Мок-предсказатель для тестирования"""
        try:
            # Простое детерминированное предсказание на основе хеша
            import hashlib
            seed = int(hashlib.md5(str(image_data.shape).encode()).hexdigest()[:8], 16)
            np.random.seed(seed % 1000)
            
            directions = ['UP', 'DOWN', 'SIDEWAYS']
            direction = np.random.choice(directions, p=[0.4, 0.4, 0.2])
            confidence = np.random.uniform(0.6, 0.9)
            
            # Расчет уровней
            base_price = 100
            timeframe_multiplier = {'1m': 0.5, '5m': 1.0, '15m': 1.5, '30m': 2.0, '1h': 2.5, '4h': 3.0, '1d': 4.0}
            multiplier = timeframe_multiplier.get(timeframe, 1.0)
            
            if direction == 'UP':
                take_profit = 1.5 * multiplier * confidence
                stop_loss = 0.8 * multiplier * (1 - confidence * 0.5)
                support = base_price * (1 - 0.01 * multiplier)
                resistance = base_price * (1 + 0.02 * multiplier)
            elif direction == 'DOWN':
                take_profit = 1.5 * multiplier * confidence
                stop_loss = 0.8 * multiplier * (1 - confidence * 0.5)
                support = base_price * (1 - 0.02 * multiplier)
                resistance = base_price * (1 + 0.01 * multiplier)
            else:
                take_profit = 0.5 * multiplier
                stop_loss = 0.3 * multiplier
                support = base_price * (1 - 0.01 * multiplier)
                resistance = base_price * (1 + 0.01 * multiplier)
            
            pivot = (support + resistance) / 2
            
            return {
                'direction': direction,
                'confidence': round(confidence, 2),
                'take_profit': round(take_profit, 2),
                'stop_loss': round(stop_loss, 2),
                'support': round(support, 2),
                'resistance': round(resistance, 2),
                'pivot': round(pivot, 2),
                'risk_level': 'Medium',
                'volume_recommendation': round(2.0 * confidence, 2),
                'timeframe': timeframe,
                'indicators': indicators or ['RSI', 'MACD'],
                'sensitivity': sensitivity
            }
            
        except Exception as e:
            logger.error(f"Mock prediction error: {e}")
            return {
                'direction': 'SIDEWAYS',
                'confidence': 0.5,
                'take_profit': 0.5,
                'stop_loss': 0.3,
                'support': 99.5,
                'resistance': 100.5,
                'pivot': 100.0,
                'risk_level': 'Medium',
                'volume_recommendation': 1.0,
                'timeframe': timeframe,
                'indicators': indicators or ['RSI', 'MACD'],
                'sensitivity': sensitivity
            }

# Создаем глобальный инстанс
predictor = PricePredictor()
