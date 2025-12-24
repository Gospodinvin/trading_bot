from sqlalchemy import Column, Integer, String, BigInteger, Float, DateTime, JSON, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    language = Column(String(10), default='en')
    settings = Column(JSON, default={
        'timeframe': '5m',
        'indicators': ['RSI', 'MACD'],
        'sensitivity': 'medium',
        'notifications': True,
        'risk_level': 'medium'
    })
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    predictions = relationship("Prediction", back_populates="user")

class Prediction(Base):
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image_path = Column(String(500))
    timeframe = Column(String(10))
    indicators = Column(JSON)
    prediction = Column(String(20))  # 'UP', 'DOWN', 'SIDEWAYS'
    confidence = Column(Float)
    take_profit = Column(Float)
    stop_loss = Column(Float)
    support_level = Column(Float)
    resistance_level = Column(Float)
    pivot_point = Column(Float)
    actual_result = Column(String(20), nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="predictions")

class BotStatistics(Base):
    __tablename__ = 'bot_statistics'
    
    id = Column(Integer, primary_key=True)
    total_predictions = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    total_users = Column(Integer, default=0)
    daily_requests = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)