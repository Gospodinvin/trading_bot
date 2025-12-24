import uuid
import os
from datetime import datetime
from app.ml.image_processor import ImageProcessor
from app.ml.predictor import predictor
from app.database.crud import create_prediction
from app.utils.logger import logger

class PredictionService:
    def __init__(self, upload_dir="uploads"):
        self.image_processor = ImageProcessor()
        self.upload_dir = upload_dir
        
        # Create upload directory if not exists
        os.makedirs(upload_dir, exist_ok=True)
    
    async def analyze_image(self, image_bytes, user_id, db, user_settings):
        """Main service method to analyze image"""
        try:
            # Save image
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(self.upload_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_bytes)
            
            # Process image
            gray_image, color_image = self.image_processor.preprocess_image(image_bytes)
            
            # Detect if it's a chart
            is_chart = self.image_processor.detect_chart_grid(gray_image)
            if not is_chart:
                return {
                    "error": "Изображение не содержит свечной график. Пожалуйста, отправьте изображение с четким графиком свечей."
                }
            
            # Detect candles
            candles = self.image_processor.detect_candles(gray_image, color_image)
            
            if len(candles) < 10:
                return {
                    "error": "Не удалось обнаружить достаточное количество свечей. Убедитесь, что график четкий и содержит не менее 10 свечей."
                }
            
            # Prepare for CNN
            cnn_input = self.image_processor.prepare_for_cnn(gray_image)
            
            # Get prediction
            timeframe = user_settings.get('timeframe', '5m')
            indicators = user_settings.get('indicators', ['RSI', 'MACD'])
            sensitivity = user_settings.get('sensitivity', 'medium')
            
            result = predictor.predict(
                cnn_input,
                timeframe=timeframe,
                indicators=indicators,
                sensitivity=sensitivity
            )
            
            # Save to database
            prediction_record = create_prediction(
                db=db,
                user_id=user_id,
                image_path=filepath,
                timeframe=timeframe,
                indicators=indicators,
                prediction=result['direction'],
                confidence=result['confidence'],
                take_profit=result['take_profit'],
                stop_loss=result['stop_loss'],
                support=result['support'],
                resistance=result['resistance'],
                pivot=result['pivot']
            )
            
            result['prediction_id'] = prediction_record.id
            
            return result
            
        except Exception as e:
            logger.error(f"Service error: {e}")
            return {
                "error": f"Ошибка при анализе: {str(e)}"
            }
    
    def format_prediction_response(self, result, prediction_id=None):
        """Format prediction result for Telegram response"""
        if 'error' in result:
            return result['error']
        
        direction_emoji = {
            'UP': '📈',
            'DOWN': '📉',
            'SIDEWAYS': '➡️'
        }
        
        risk_emoji = {
            'Low': '🟢',
            'Medium-Low': '🟡',
            'Medium': '🟠',
            'Medium-High': '🟠',
            'High': '🔴'
        }
        
        prediction_id_str = f"#{prediction_id}" if prediction_id else "#NEW"
        
        response = f"""
🎯 **АНАЛИЗ ГРАФИКА** {prediction_id_str}

📊 **ПАРАМЕТРЫ:**
• Таймфрейм: {result.get('timeframe', '5m')}
• Индикаторы: {', '.join(result.get('indicators', ['RSI', 'MACD']))}
• Модель: CNN + Ensemble
• Чувствительность: {result.get('sensitivity', 'medium').capitalize()}

📈 **ПРЕДСКАЗАНИЕ:**
• Направление: {result['direction']} {direction_emoji.get(result['direction'], '')}
• Вероятность: {result['confidence']*100:.1f}%
• Целевой уровень: +{result['take_profit']}%
• Стоп-лосс: -{result['stop_loss']}%
• Рекомендуемый объем: {result['volume_recommendation']}% от депозита

⚠️ **РИСКИ:**
• Уровень риска: {risk_emoji.get(result['risk_level'], '🟡')} {result['risk_level']}
• Волатильность: {'Высокая' if result.get('features', {}).get('atr_pct', 1) > 2 else 'Средняя' if result.get('features', {}).get('atr_pct', 1) > 1 else 'Низкая'}

📊 **ТЕХНИЧЕСКИЕ УРОВНИ:**
• Support: ${result['support']:.2f}
• Resistance: ${result['resistance']:.2f}
• Pivot Point: ${result['pivot']:.2f}

⏰ **СРОК ДЕЙСТВИЯ:** {self._get_expiration_time(result.get('timeframe', '5m'))} минут
🔄 **СЛЕДУЮЩИЙ АНАЛИЗ ЧЕРЕЗ:** {self._get_next_analysis_time(result.get('timeframe', '5m'))}

📝 **ПРИМЕЧАНИЕ:** Это автоматический анализ. Всегда проводите собственный анализ перед принятием торговых решений.
"""
        
        return response
    
    def _get_expiration_time(self, timeframe):
        """Get expiration time based on timeframe"""
        timeframes = {
            '1m': 5, '5m': 15, '15m': 45,
            '30m': 90, '1h': 180, '4h': 720, '1d': 1440
        }
        return timeframes.get(timeframe, 15)
    
    def _get_next_analysis_time(self, timeframe):
        """Get next analysis time"""
        timeframes = {
            '1m': 1, '5m': 5, '15m': 15,
            '30m': 30, '1h': 60, '4h': 240, '1d': 1440
        }
        return timeframes.get(timeframe, 5)