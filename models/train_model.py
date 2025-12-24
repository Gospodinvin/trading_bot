import numpy as np
import pandas as pd
import yfinance as yf
import ccxt
from datetime import datetime, timedelta
import talib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D, Flatten
from tensorflow.keras.optimizers import Adam
import joblib
import warnings
warnings.filterwarnings('ignore')

class ModelTrainer:
    def __init__(self):
        self.data = None
        self.features = None
        self.labels = None
        self.scaler = StandardScaler()
        
    def fetch_data(self, symbol='BTC-USD', period='2y', interval='5m'):
        """Fetch historical data from Yahoo Finance"""
        print(f"Fetching data for {symbol}...")
        
        try:
            # Try Yahoo Finance first
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                # Fallback to Binance via ccxt
                exchange = ccxt.binance()
                since = exchange.parse8601((datetime.now() - timedelta(days=730)).isoformat())
                ohlcv = exchange.fetch_ohlcv(symbol.replace('-', '/'), interval, since)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
            
            print(f"Fetched {len(df)} candles")
            return df
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            
            # Generate synthetic data for testing
            print("Generating synthetic data...")
            dates = pd.date_range(end=datetime.now(), periods=10000, freq='5min')
            np.random.seed(42)
            prices = np.cumsum(np.random.randn(10000) * 0.001) + 100
            df = pd.DataFrame({
                'open': prices + np.random.randn(10000) * 0.1,
                'high': prices + np.abs(np.random.randn(10000) * 0.2),
                'low': prices - np.abs(np.random.randn(10000) * 0.2),
                'close': prices,
                'volume': np.random.randint(1000, 10000, 10000)
            }, index=dates)
            
            return df
    
    def create_features(self, df):
        """Create technical indicators and features"""
        print("Creating features...")
        
        # Basic price features
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Volatility
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Moving averages
        df['sma_10'] = talib.SMA(df['close'], timeperiod=10)
        df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
        df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
        df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
        df['ema_26'] = talib.EMA(df['close'], timeperiod=26)
        
        # RSI
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        
        # MACD
        macd, macd_signal, macd_hist = talib.MACD(df['close'])
        df['macd'] = macd
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(df['close'])
        df['bb_upper'] = upper
        df['bb_middle'] = middle
        df['bb_lower'] = lower
        df['bb_width'] = (upper - lower) / middle
        df['bb_position'] = (df['close'] - lower) / (upper - lower)
        
        # Stochastic
        slowk, slowd = talib.STOCH(df['high'], df['low'], df['close'])
        df['stoch_k'] = slowk
        df['stoch_d'] = slowd
        
        # ATR
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
        
        # Volume indicators
        df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma']
        
        # Price patterns (simplified)
        df['is_hammer'] = self._detect_hammer(df)
        df['is_doji'] = self._detect_doji(df)
        
        # Target variable: future price movement (1 = up, 0 = down)
        df['target'] = (df['close'].shift(-5) > df['close']).astype(int)
        
        # Drop NaN values
        df = df.dropna()
        
        print(f"Created {len(df.columns)} features")
        return df
    
    def _detect_hammer(self, df):
        """Detect hammer candlestick pattern"""
        body = abs(df['close'] - df['open'])
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)
        
        is_hammer = (
            (lower_shadow > 2 * body) & 
            (upper_shadow < body * 0.3) &
            (df['close'] > df['open'])  # Bullish hammer
        )
        
        return is_hammer.astype(int)
    
    def _detect_doji(self, df):
        """Detect doji candlestick pattern"""
        body = abs(df['close'] - df['open'])
        total_range = df['high'] - df['low']
        
        is_doji = (body / total_range < 0.1) & (total_range > 0)
        
        return is_doji.astype(int)
    
    def prepare_data(self, df, sequence_length=50):
        """Prepare data for ML models"""
        print("Preparing data...")
        
        # Feature columns
        feature_cols = [
            'returns', 'volatility', 'rsi', 'macd', 'macd_hist',
            'bb_position', 'bb_width', 'stoch_k', 'atr',
            'volume_ratio', 'is_hammer', 'is_doji'
        ]
        
        # Ensure all columns exist
        available_cols = [col for col in feature_cols if col in df.columns]
        
        # Feature matrix
        X = df[available_cols].values
        
        # Target
        y = df['target'].values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Create sequences for LSTM
        X_sequences = []
        y_sequences = []
        
        for i in range(sequence_length, len(X_scaled)):
            X_sequences.append(X_scaled[i-sequence_length:i])
            y_sequences.append(y[i])
        
        X_sequences = np.array(X_sequences)
        y_sequences = np.array(y_sequences)
        
        print(f"Created {len(X_sequences)} sequences")
        return X_sequences, y_sequences, X_scaled, y
    
    def train_ensemble_model(self, X, y):
        """Train ensemble model"""
        print("Training ensemble model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        # Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        rf_score = rf.score(X_test, y_test)
        print(f"Random Forest accuracy: {rf_score:.4f}")
        
        # Gradient Boosting
        gb = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        gb.fit(X_train, y_train)
        gb_score = gb.score(X_test, y_test)
        print(f"Gradient Boosting accuracy: {gb_score:.4f}")
        
        # Support Vector Machine
        svm = SVC(probability=True, random_state=42)
        svm.fit(X_train, y_train)
        svm_score = svm.score(X_test, y_test)
        print(f"SVM accuracy: {svm_score:.4f}")
        
        # Ensemble voting (simple average)
        from sklearn.ensemble import VotingClassifier
        
        ensemble = VotingClassifier(
            estimators=[
                ('rf', rf),
                ('gb', gb),
                ('svm', svm)
            ],
            voting='soft'
        )
        ensemble.fit(X_train, y_train)
        ensemble_score = ensemble.score(X_test, y_test)
        print(f"Ensemble accuracy: {ensemble_score:.4f}")
        
        return ensemble
    
    def train_lstm_model(self, X_sequences, y_sequences):
        """Train LSTM model"""
        print("Training LSTM model...")
        
        # Split data
        split_idx = int(len(X_sequences) * 0.8)
        X_train_seq = X_sequences[:split_idx]
        X_test_seq = X_sequences[split_idx:]
        y_train_seq = y_sequences[:split_idx]
        y_test_seq = y_sequences[split_idx:]
        
        # Build LSTM model
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(X_train_seq.shape[1], X_train_seq.shape[2])),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Train
        history = model.fit(
            X_train_seq, y_train_seq,
            epochs=20,
            batch_size=32,
            validation_split=0.1,
            verbose=1
        )
        
        # Evaluate
        loss, accuracy = model.evaluate(X_test_seq, y_test_seq, verbose=0)
        print(f"LSTM accuracy: {accuracy:.4f}")
        
        return model
    
    def train_cnn_model(self, X_sequences, y_sequences):
        """Train 1D CNN model"""
        print("Training CNN model...")
        
        # Split data
        split_idx = int(len(X_sequences) * 0.8)
        X_train_seq = X_sequences[:split_idx]
        X_test_seq = X_sequences[split_idx:]
        y_train_seq = y_sequences[:split_idx]
        y_test_seq = y_sequences[split_idx:]
        
        # Build CNN model
        model = Sequential([
            Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(X_train_seq.shape[1], X_train_seq.shape[2])),
            MaxPooling1D(pool_size=2),
            Conv1D(filters=32, kernel_size=3, activation='relu'),
            MaxPooling1D(pool_size=2),
            Flatten(),
            Dense(50, activation='relu'),
            Dropout(0.5),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        # Train
        history = model.fit(
            X_train_seq, y_train_seq,
            epochs=15,
            batch_size=32,
            validation_split=0.1,
            verbose=1
        )
        
        # Evaluate
        loss, accuracy = model.evaluate(X_test_seq, y_test_seq, verbose=0)
        print(f"CNN accuracy: {accuracy:.4f}")
        
        return model
    
    def save_models(self, ensemble_model, lstm_model, cnn_model):
        """Save trained models"""
        import os
        os.makedirs('models', exist_ok=True)
        
        # Save ensemble model
        joblib.dump(ensemble_model, 'models/price_predictor.pkl')
        
        # Save scaler
        joblib.dump(self.scaler, 'models/scaler.pkl')
        
        # Save LSTM model
        lstm_model.save('models/lstm_model.h5')
        
        # Save CNN model
        cnn_model.save('models/candle_cnn.h5')
        
        print("Models saved successfully!")
    
    def train_all(self):
        """Train all models"""
        print("Starting model training...")
        
        # Fetch data
        df = self.fetch_data()
        
        # Create features
        df = self.create_features(df)
        
        # Prepare data
        X_sequences, y_sequences, X, y = self.prepare_data(df)
        
        # Train models
        ensemble_model = self.train_ensemble_model(X, y)
        lstm_model = self.train_lstm_model(X_sequences, y_sequences)
        cnn_model = self.train_cnn_model(X_sequences, y_sequences)
        
        # Save models
        self.save_models(ensemble_model, lstm_model, cnn_model)
        
        print("Training completed!")

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_all()