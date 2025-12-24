import pandas as pd
import ta
import numpy as np
from app.utils.logger import logger

class FeatureExtractor:
    def __init__(self):
        self.indicators_map = {
            'RSI': self._add_rsi,
            'MACD': self._add_macd,
            'SMA': self._add_sma,
            'EMA': self._add_ema,
            'Bollinger': self._add_bollinger_bands,
            'Stochastic': self._add_stochastic,
            'Ichimoku': self._add_ichimoku,
            'ATR': self._add_atr,
            'Volume': self._add_volume_profile
        }
    
    def extract_features(self, ohlc_data, selected_indicators=None):
        """Extract technical indicators from OHLC data"""
        if not ohlc_data or len(ohlc_data) < 50:
            logger.warning("Insufficient data for feature extraction")
            return self._get_default_features()
        
        df = pd.DataFrame(ohlc_data)
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_cols):
            return self._get_default_features()
        
        # Convert to numpy arrays
        opens = df['open'].values.astype(float)
        highs = df['high'].values.astype(float)
        lows = df['low'].values.astype(float)
        closes = df['close'].values.astype(float)
        
        features = {}
        
        # Always add basic features
        features.update(self._get_basic_features(closes, highs, lows))
        
        # Add selected indicators
        if selected_indicators:
            for indicator in selected_indicators:
                if indicator in self.indicators_map:
                    try:
                        self.indicators_map[indicator](features, closes, highs, lows)
                    except Exception as e:
                        logger.error(f"Error calculating {indicator}: {e}")
                        continue
        
        # Add price action patterns
        features.update(self._detect_candle_patterns(opens, highs, lows, closes))
        
        # Add trend features
        features.update(self._calculate_trend_features(closes))
        
        # Add volatility features
        features.update(self._calculate_volatility_features(highs, lows, closes))
        
        return features
    
    def _get_basic_features(self, closes, highs, lows):
        """Calculate basic price features"""
        features = {}
        
        if len(closes) >= 2:
            features['price_change'] = closes[-1] - closes[-2]
            features['price_change_pct'] = ((closes[-1] - closes[-2]) / closes[-2]) * 100
        
        if len(closes) >= 20:
            # Recent momentum
            features['momentum_5'] = closes[-1] - closes[-6]
            features['momentum_10'] = closes[-1] - closes[-11]
            features['momentum_20'] = closes[-1] - closes[-21]
            
            # High/low ranges
            features['high_20'] = np.max(highs[-20:])
            features['low_20'] = np.min(lows[-20:])
            features['range_20_pct'] = ((features['high_20'] - features['low_20']) / features['low_20']) * 100
        
        return features
    
    def _add_rsi(self, features, closes, highs, lows):
        """Add RSI indicator"""
        if len(closes) >= 14:
            rsi_series = ta.momentum.RSIIndicator(pd.Series(closes), window=14).rsi()
            if not rsi_series.empty:
                features['rsi'] = rsi_series.iloc[-1]
            if not np.isnan(rsi[-1]):
                features['rsi'] = rsi[-1]
                features['rsi_overbought'] = 1 if rsi[-1] > 70 else 0
                features['rsi_oversold'] = 1 if rsi[-1] < 30 else 0
    
    def _add_macd(self, features, closes, highs, lows):
        """Add MACD indicator"""
        if len(closes) >= 26:
            macd_indicator = ta.trend.MACD(pd.Series(closes))
            features['macd'] = macd_indicator.macd().iloc[-1]
            features['macd_signal'] = macd_indicator.macd_signal().iloc[-1]
            features['macd_hist'] = macd_indicator.macd_diff().iloc[-1]
                fastperiod=12, 
                slowperiod=26, 
                signalperiod=9
            )
            if not np.isnan(macd[-1]):
                features['macd'] = macd[-1]
                features['macd_signal'] = macd_signal[-1] if not np.isnan(macd_signal[-1]) else 0
                features['macd_hist'] = macd_hist[-1] if not np.isnan(macd_hist[-1]) else 0
                features['macd_crossover'] = 1 if macd[-1] > macd_signal[-1] else -1
    
    def _add_sma(self, features, closes, highs, lows):
        """Add Simple Moving Averages"""
        if len(closes) >= 50:
            sma_series = ta.trend.SMAIndicator(pd.Series(closes), window=20).sma_indicator()
            if not sma_series.empty:
                features['sma_20'] = sma_series.iloc[-1]
            
            # Price position relative to SMAs
            if not np.isnan(features['sma_20']):
                features['price_vs_sma20'] = ((closes[-1] - features['sma_20']) / features['sma_20']) * 100
    
    def _add_ema(self, features, closes, highs, lows):
        """Add Exponential Moving Averages"""
        if len(closes) >= 50:
            features['ema_12'] = talib.EMA(closes, timeperiod=12)[-1]
            features['ema_26'] = talib.EMA(closes, timeperiod=26)[-1]
            
            # EMA crossover
            if not np.isnan(features['ema_12']) and not np.isnan(features['ema_26']):
                features['ema_crossover'] = 1 if features['ema_12'] > features['ema_26'] else -1
    
    def _add_bollinger_bands(self, features, closes, highs, lows):
        """Add Bollinger Bands"""
        if len(closes) >= 20:
            upper, middle, lower = talib.BBANDS(
                closes, 
                timeperiod=20, 
                nbdevup=2, 
                nbdevdn=2
            )
            
            if not np.isnan(upper[-1]):
                features['bb_upper'] = upper[-1]
                features['bb_middle'] = middle[-1]
                features['bb_lower'] = lower[-1]
                
                # Bollinger Band position
                bb_width = (features['bb_upper'] - features['bb_lower']) / features['bb_middle']
                features['bb_width_pct'] = bb_width * 100
                features['bb_position'] = (closes[-1] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
    
    def _add_stochastic(self, features, closes, highs, lows):
        """Add Stochastic oscillator"""
        if len(closes) >= 14:
            slowk, slowd = talib.STOCH(
                highs, lows, closes,
                fastk_period=14,
                slowk_period=3,
                slowk_matype=0,
                slowd_period=3,
                slowd_matype=0
            )
            
            if not np.isnan(slowk[-1]):
                features['stoch_k'] = slowk[-1]
                features['stoch_d'] = slowd[-1] if not np.isnan(slowd[-1]) else 0
                features['stoch_overbought'] = 1 if slowk[-1] > 80 else 0
                features['stoch_oversold'] = 1 if slowk[-1] < 20 else 0
    
    def _add_ichimoku(self, features, closes, highs, lows):
        """Add Ichimoku Cloud"""
        if len(closes) >= 52:
            tenkan_sen = (np.max(highs[-9:]) + np.min(lows[-9:])) / 2
            kijun_sen = (np.max(highs[-26:]) + np.min(lows[-26:])) / 2
            senkou_span_a = (tenkan_sen + kijun_sen) / 2
            senkou_span_b = (np.max(highs[-52:]) + np.min(lows[-52:])) / 2
            
            features['ichimoku_tenkan'] = tenkan_sen
            features['ichimoku_kijun'] = kijun_sen
            features['ichimoku_senkou_a'] = senkou_span_a
            features['ichimoku_senkou_b'] = senkou_span_b
            features['ichimoku_cloud_position'] = 1 if closes[-1] > max(senkou_span_a, senkou_span_b) else -1
    
    def _add_atr(self, features, closes, highs, lows):
        """Add Average True Range"""
        if len(closes) >= 14:
            atr = talib.ATR(highs, lows, closes, timeperiod=14)
            if not np.isnan(atr[-1]):
                features['atr'] = atr[-1]
                features['atr_pct'] = (atr[-1] / closes[-1]) * 100
    
    def _add_volume_profile(self, features, closes, highs, lows):
        """Add volume profile (simulated)"""
        # In real implementation, you would use actual volume data
        if len(closes) >= 20:
            price_range = np.max(closes[-20:]) - np.min(closes[-20:])
            features['volatility'] = price_range / np.mean(closes[-20:])
    
    def _detect_candle_patterns(self, opens, highs, lows, closes):
        """Detect common candlestick patterns"""
        patterns = {}
        
        if len(closes) >= 3:
            # Doji pattern
            body_size = abs(closes[-1] - opens[-1])
            total_range = highs[-1] - lows[-1]
            if total_range > 0:
                doji_ratio = body_size / total_range
                patterns['is_doji'] = 1 if doji_ratio < 0.1 else 0
            
            # Hammer pattern
            if len(closes) >= 5:
                lower_shadow = min(opens[-1], closes[-1]) - lows[-1]
                upper_shadow = highs[-1] - max(opens[-1], closes[-1])
                body_size = abs(closes[-1] - opens[-1])
                
                if lower_shadow > 2 * body_size and upper_shadow < body_size * 0.3:
                    patterns['is_hammer'] = 1 if closes[-1] > opens[-1] else -1
        
        return patterns
    
    def _calculate_trend_features(self, closes):
        """Calculate trend features"""
        features = {}
        
        if len(closes) >= 20:
            # Simple linear regression for trend
            x = np.arange(len(closes[-20:]))
            y = closes[-20:]
            slope, _ = np.polyfit(x, y, 1)
            
            features['trend_slope'] = slope
            features['trend_strength'] = abs(slope) / np.mean(y)
            
            # Moving average slope
            ma_5 = talib.SMA(closes, timeperiod=5)[-5:]
            ma_20 = talib.SMA(closes, timeperiod=20)[-5:]
            
            if len(ma_5) >= 2 and len(ma_20) >= 2:
                ma_5_slope = ma_5[-1] - ma_5[0]
                ma_20_slope = ma_20[-1] - ma_20[0]
                features['ma_trend_alignment'] = 1 if ma_5_slope * ma_20_slope > 0 else 0
        
        return features
    
    def _calculate_volatility_features(self, highs, lows, closes):
        """Calculate volatility features"""
        features = {}
        
        if len(closes) >= 20:
            # Historical volatility
            returns = np.diff(np.log(closes[-20:]))
            features['hist_volatility'] = np.std(returns) * np.sqrt(252)  # Annualized
            
            # Average true range percentage
            atr = talib.ATR(highs, lows, closes, timeperiod=14)
            if not np.isnan(atr[-1]):
                features['atr_volatility'] = (atr[-1] / closes[-1]) * 100
        
        return features
    
    def _get_default_features(self):
        """Return default features when data is insufficient"""
        return {
            'price_change': 0,
            'rsi': 50,
            'macd': 0,
            'trend_slope': 0,
            'volatility': 0.01,
            'bb_position': 0.5
        }
