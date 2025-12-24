import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./trading_bot.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(','))) if os.getenv("ADMIN_IDS") else []
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    MODEL_PATH = os.getenv("MODEL_PATH", "models/candle_cnn.h5")
    
config = Config()