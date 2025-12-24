import tensorflow as tf
import torch
import pickle
import numpy as np
from app.utils.config import config
from app.utils.logger import logger
import os

class ModelLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        try:
            # Load TensorFlow CNN model for pattern recognition
            if os.path.exists(config.MODEL_PATH):
                self.candle_model = tf.keras.models.load_model(config.MODEL_PATH)
                logger.info("Candle pattern model loaded successfully")
            else:
                self.candle_model = self._create_default_cnn_model()
                logger.warning("Using default CNN model")
        except Exception as e:
            logger.error(f"Failed to load candle model: {e}")
            self.candle_model = self._create_default_cnn_model()
        
        try:
            # Load PyTorch LSTM model
            self.lstm_model = self._create_lstm_model()
            logger.info("LSTM model initialized")
        except Exception as e:
            logger.error(f"Failed to load LSTM model: {e}")
            self.lstm_model = None
        
        try:
            # Load scaler and ensemble model
            if os.path.exists('models/scaler.pkl'):
                with open('models/scaler.pkl', 'rb') as f:
                    self.scaler = pickle.load(f)
            else:
                self.scaler = None
            
            if os.path.exists('models/price_predictor.pkl'):
                with open('models/price_predictor.pkl', 'rb') as f:
                    self.ensemble_model = pickle.load(f)
            else:
                self.ensemble_model = self._create_default_ensemble()
                
            logger.info("Ensemble models loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ensemble models: {e}")
            self.scaler = None
            self.ensemble_model = self._create_default_ensemble()
    
    def _create_default_cnn_model(self):
        """Create a simple CNN model for candle pattern recognition"""
        model = tf.keras.Sequential([
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu', input_shape=(64, 64, 1)),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu'),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(3, activation='softmax')  # UP, DOWN, SIDEWAYS
        ])
        
        model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def _create_lstm_model(self):
        """Create a simple LSTM model for time series prediction"""
        class LSTMModel(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm1 = torch.nn.LSTM(10, 50, batch_first=True)
                self.dropout1 = torch.nn.Dropout(0.2)
                self.lstm2 = torch.nn.LSTM(50, 25, batch_first=True)
                self.dropout2 = torch.nn.Dropout(0.2)
                self.linear = torch.nn.Linear(25, 3)
                
            def forward(self, x):
                x, _ = self.lstm1(x)
                x = self.dropout1(x)
                x, _ = self.lstm2(x)
                x = self.dropout2(x[:, -1, :])
                return self.linear(x)
        
        return LSTMModel()
    
    def _create_default_ensemble(self):
        """Create default Random Forest ensemble"""
        from sklearn.ensemble import RandomForestClassifier
        
        return RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

model_loader = ModelLoader()