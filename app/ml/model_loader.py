import pickle
import numpy as np
from app.utils.config import config
from app.utils.logger import logger

class ModelLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance._load_models()
        return cls._instance
    
    def _load_models(self):
        """Заглушка для загрузки моделей"""
        logger.info("Using mock model loader")
        
        # Создаем заглушечные модели
        self.candle_model = None
        self.lstm_model = None
        self.scaler = None
        self.ensemble_model = None
        
        logger.info("Mock models initialized")

model_loader = ModelLoader()
