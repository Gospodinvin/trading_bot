from sqlalchemy.orm import Session
from app.database.models import User, Prediction, BotStatistics
from datetime import datetime, timedelta
import json

def get_or_create_user(db: Session, telegram_id: int, username: str = None, 
                       first_name: str = None, last_name: str = None):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=tele_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Update statistics
        stats = db.query(BotStatistics).first()
        if not stats:
            stats = BotStatistics()
            db.add(stats)
        stats.total_users += 1
        db.commit()
    return user

def create_prediction(db: Session, user_id: int, image_path: str, timeframe: str, 
                     indicators: list, prediction: str, confidence: float,
                     take_profit: float, stop_loss: float, support: float,
                     resistance: float, pivot: float):
    
    prediction_record = Prediction(
        user_id=user_id,
        image_path=image_path,
        timeframe=timeframe,
        indicators=indicators,
        prediction=prediction,
        confidence=confidence,
        take_profit=take_profit,
        stop_loss=stop_loss,
        support_level=support,
        resistance_level=resistance,
        pivot_point=pivot
    )
    db.add(prediction_record)
    
    # Update statistics
    stats = db.query(BotStatistics).first()
    if not stats:
        stats = BotStatistics()
        db.add(stats)
    stats.total_predictions += 1
    stats.daily_requests += 1
    
    db.commit()
    db.refresh(prediction_record)
    return prediction_record

def update_prediction_feedback(db: Session, prediction_id: int, 
                             actual_result: str, feedback: str = None):
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if prediction:
        prediction.actual_result = actual_result
        prediction.feedback = feedback
        
        # Update statistics if result provided
        if actual_result == prediction.prediction:
            stats = db.query(BotStatistics).first()
            if stats:
                stats.correct_predictions += 1
        
        db.commit()
        db.refresh(prediction)
    return prediction

def get_user_predictions(db: Session, user_id: int, limit: int = 10):
    return db.query(Prediction).filter(
        Prediction.user_id == user_id
    ).order_by(Prediction.created_at.desc()).limit(limit).all()

def get_bot_statistics(db: Session):
    stats = db.query(BotStatistics).first()
    if not stats:
        return {"total": 0, "accuracy": 0, "users": 0, "daily": 0}
    
    accuracy = (stats.correct_predictions / stats.total_predictions * 100) if stats.total_predictions > 0 else 0
    
    return {
        "total": stats.total_predictions,
        "correct": stats.correct_predictions,
        "accuracy": round(accuracy, 2),
        "users": stats.total_users,
        "daily": stats.daily_requests
    }

def update_user_settings(db: Session, user_id: int, settings: dict):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.settings = {**user.settings, **settings}
        db.commit()
        db.refresh(user)
    return user