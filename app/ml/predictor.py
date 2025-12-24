import numpy as np
import tensorflow as tf
import torch
from app.ml.model_loader import model_loader
from app.ml.feature_extractor import FeatureExtractor
from app.utils.logger import logger

class PricePredictor:
    def __init__(self):
        self.candle_model = model_loader.candle_model
        self.lstm_model = model_loader.lstm_model
        self.ensemble_model = model_loader.ensemble_model
        self.scaler = model_loader.scaler
        self.feature_extractor = FeatureExtractor()
        
        if self.lstm_model:
            self.lstm_model.eval()
    
    def predict(self, image_data, timeframe='5m', indicators=None, sensitivity='medium'):
        """Main prediction function"""
        try:
            # Preprocess image for CNN
            cnn_input = image_data
            
            # CNN prediction for pattern recognition
            cnn_prediction = None
            if self.candle_model is not None:
                cnn_pred = self.candle_model.predict(cnn_input, verbose=0)[0]
                cnn_prediction = {
                    'direction': ['UP', 'DOWN', 'SIDEWAYS'][np.argmax(cnn_pred)],
                    'confidence': float(np.max(cnn_pred))
                }
            
            # Extract features for ensemble model
            features = self.feature_extractor.extract_features(
                None,  # In real implementation, pass OHLC data
                indicators
            )
            
            # Prepare features for ensemble
            feature_vector = self._prepare_feature_vector(features)
            
            # Ensemble prediction
            ensemble_pred = self._ensemble_predict(feature_vector)
            
            # Combine predictions
            final_prediction = self._combine_predictions(
                cnn_prediction, ensemble_pred, sensitivity
            )
            
            # Calculate targets and levels
            targets = self._calculate_targets(final_prediction, features, timeframe)
            
            # Prepare final result
            result = {
                **final_prediction,
                **targets,
                'timeframe': timeframe,
                'indicators': indicators or ['RSI', 'MACD'],
                'sensitivity': sensitivity,
                'features': {k: float(v) for k, v in features.items() if isinstance(v, (int, float, np.number))}
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._get_fallback_prediction(timeframe)
    
    def _prepare_feature_vector(self, features):
        """Prepare feature vector for ensemble model"""
        # Select key features
        key_features = [
            'rsi', 'macd', 'price_change_pct', 'trend_slope',
            'bb_position', 'atr_pct', 'stoch_k'
        ]
        
        vector = []
        for feat in key_features:
            vector.append(features.get(feat, 0))
        
        # Pad with zeros if needed
        while len(vector) < 20:
            vector.append(0)
        
        return np.array(vector[:20]).reshape(1, -1)
    
    def _ensemble_predict(self, feature_vector):
        """Get prediction from ensemble model"""
        try:
            if self.ensemble_model is not None:
                if hasattr(self.ensemble_model, 'predict_proba'):
                    proba = self.ensemble_model.predict_proba(feature_vector)[0]
                    
                    # Map to directions (adjust based on your model)
                    directions = ['UP', 'DOWN', 'SIDEWAYS']
                    if len(proba) >= 3:
                        idx = np.argmax(proba)
                        return {
                            'direction': directions[idx],
                            'confidence': float(proba[idx])
                        }
            
            # Fallback prediction
            return {
                'direction': 'SIDEWAYS',
                'confidence': 0.5
            }
            
        except Exception as e:
            logger.error(f"Ensemble prediction error: {e}")
            return {
                'direction': 'SIDEWAYS',
                'confidence': 0.5
            }
    
    def _combine_predictions(self, cnn_pred, ensemble_pred, sensitivity):
        """Combine CNN and ensemble predictions"""
        if cnn_pred is None:
            return ensemble_pred
        
        # Weight predictions based on sensitivity
        sensitivity_weights = {
            'low': {'cnn': 0.3, 'ensemble': 0.7},
            'medium': {'cnn': 0.5, 'ensemble': 0.5},
            'high': {'cnn': 0.7, 'ensemble': 0.3}
        }
        
        weights = sensitivity_weights.get(sensitivity, sensitivity_weights['medium'])
        
        # Map directions to indices
        direction_map = {'UP': 0, 'DOWN': 1, 'SIDEWAYS': 2}
        
        # Create combined probability vector
        combined_probs = np.zeros(3)
        
        # Add CNN prediction
        cnn_idx = direction_map.get(cnn_pred['direction'], 2)
        combined_probs[cnn_idx] += cnn_pred['confidence'] * weights['cnn']
        
        # Add ensemble prediction
        ensemble_idx = direction_map.get(ensemble_pred['direction'], 2)
        combined_probs[ensemble_idx] += ensemble_pred['confidence'] * weights['ensemble']
        
        # Get final prediction
        final_idx = np.argmax(combined_probs)
        directions = ['UP', 'DOWN', 'SIDEWAYS']
        
        return {
            'direction': directions[final_idx],
            'confidence': float(combined_probs[final_idx])
        }
    
    def _calculate_targets(self, prediction, features, timeframe):
        """Calculate take-profit, stop-loss, and support/resistance levels"""
        base_price = 100  # In real implementation, use actual price
        
        # Adjust risk based on confidence and timeframe
        timeframe_multiplier = {
            '1m': 0.5, '5m': 1.0, '15m': 1.5,
            '30m': 2.0, '1h': 2.5, '4h': 3.0, '1d': 4.0
        }
        
        multiplier = timeframe_multiplier.get(timeframe, 1.0)
        confidence_multiplier = prediction['confidence']
        
        if prediction['direction'] == 'UP':
            take_profit_pct = 1.5 * multiplier * confidence_multiplier
            stop_loss_pct = 0.8 * multiplier * (1 - confidence_multiplier * 0.5)
            
            # Calculate levels
            support = base_price * (1 - 0.01 * multiplier)
            resistance = base_price * (1 + 0.02 * multiplier)
            pivot = (support + resistance) / 2
            
        elif prediction['direction'] == 'DOWN':
            take_profit_pct = 1.5 * multiplier * confidence_multiplier
            stop_loss_pct = 0.8 * multiplier * (1 - confidence_multiplier * 0.5)
            
            # Calculate levels
            support = base_price * (1 - 0.02 * multiplier)
            resistance = base_price * (1 + 0.01 * multiplier)
            pivot = (support + resistance) / 2
            
        else:  # SIDEWAYS
            take_profit_pct = 0.5 * multiplier
            stop_loss_pct = 0.3 * multiplier
            
            # Calculate levels
            volatility = features.get('atr_pct', 1) / 100
            support = base_price * (1 - volatility)
            resistance = base_price * (1 + volatility)
            pivot = base_price
        
        # Adjust based on volatility
        volatility = features.get('atr_pct', 1) / 100
        take_profit_pct *= (1 + volatility)
        stop_loss_pct *= (1 + volatility)
        
        return {
            'take_profit': round(take_profit_pct, 2),
            'stop_loss': round(stop_loss_pct, 2),
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'pivot': round(pivot, 2),
            'risk_level': self._calculate_risk_level(prediction['confidence'], volatility),
            'volume_recommendation': self._calculate_volume_recommendation(
                prediction['confidence'], features
            )
        }
    
    def _calculate_risk_level(self, confidence, volatility):
        """Calculate risk level (1-5)"""
        risk_score = (1 - confidence) * 5 + volatility * 10
        
        if risk_score < 2:
            return 'Low'
        elif risk_score < 3:
            return 'Medium-Low'
        elif risk_score < 4:
            return 'Medium'
        elif risk_score < 5:
            return 'Medium-High'
        else:
            return 'High'
    
    def _calculate_volume_recommendation(self, confidence, features):
        """Calculate recommended position size"""
        base_volume = 2.0  # 2% of portfolio
        
        # Adjust based on confidence
        volume = base_volume * confidence
        
        # Adjust based on RSI
        rsi = features.get('rsi', 50)
        if rsi > 70 or rsi < 30:
            volume *= 0.5  # Reduce volume at extremes
        
        # Adjust based on volatility
        volatility = features.get('atr_pct', 1) / 100
        if volatility > 0.03:
            volume *= 0.7  # Reduce volume in high volatility
        
        return round(volume, 2)
    
    def _get_fallback_prediction(self, timeframe):
        """Fallback prediction when model fails"""
        return {
            'direction': 'SIDEWAYS',
            'confidence': 0.5,
            'take_profit': 0.5,
            'stop_loss': 0.3,
            'support': 0,
            'resistance': 0,
            'pivot': 0,
            'risk_level': 'Medium',
            'volume_recommendation': 1.0,
            'timeframe': timeframe,
            'indicators': ['RSI', 'MACD'],
            'sensitivity': 'medium'
        }

# Singleton instance
predictor = PricePredictor()