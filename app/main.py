from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.crud import get_bot_statistics
from app.utils.logger import logger
import threading
from app.bot.telegram_bot import TradingBot

bot = None
bot_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global bot, bot_thread
    
    logger.info("Starting application...")
    
    # Start bot in separate thread
    bot = TradingBot()
    bot_thread = threading.Thread(target=bot.run, daemon=True)
    bot_thread.start()
    
    logger.info("Bot thread started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    if bot and bot.application:
        await bot.application.shutdown()
        await bot.application.stop()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Trading Bot API",
    description="API for Trading Bot with ML predictions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Trading Bot API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "stats": "/stats",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "bot": "running" if bot_thread and bot_thread.is_alive() else "stopped"
    }

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    try:
        stats = get_bot_statistics(db)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/version")
async def get_version():
    return {
        "version": "1.0.0",
        "ml_models": ["CNN", "LSTM", "Ensemble"],
        "features": ["chart_analysis", "price_prediction", "risk_management"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)