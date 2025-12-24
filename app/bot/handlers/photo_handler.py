from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.services.prediction_service import PredictionService
from app.database.crud import get_or_create_user
from app.utils.logger import logger
import asyncio

prediction_service = PredictionService()

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages"""
    user = update.effective_user
    db = context.bot_data['db']
    
    # Get or create user
    db_user = get_or_create_user(
        db, 
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name
    )
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        "⏳ Загружаю и обрабатываю изображение..."
    )
    
    try:
        # Get the photo file
        photo_file = await update.message.photo[-1].get_file()
        
        # Download photo
        photo_bytes = await photo_file.download_as_bytearray()
        
        # Update status
        await processing_msg.edit_text("🔍 Анализирую свечные паттерны...")
        
        # Get user settings
        settings = db_user.settings if db_user.settings else {}
        
        # Analyze image
        await processing_msg.edit_text("🤖 Запускаю ML модели...")
        
        result = await prediction_service.analyze_image(
            image_bytes=bytes(photo_bytes),
            user_id=db_user.id,
            db=db,
            user_settings=settings
        )
        
        # Format response
        if 'error' in result:
            await processing_msg.edit_text(result['error'])
            return
        
        # Format success response
        await processing_msg.edit_text("📊 Формирую отчет...")
        
        response_text = prediction_service.format_prediction_response(
            result, 
            result.get('prediction_id')
        )
        
        # Send final result
        await update.message.reply_text(
            response_text,
            parse_mode='Markdown',
            reply_markup=get_feedback_keyboard(result.get('prediction_id'))
        )
        
        # Delete processing message
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Photo handling error: {e}")
        await processing_msg.edit_text(
            f"❌ Ошибка при обработке изображения: {str(e)}\n"
            "Попробуйте другое изображение или обратитесь в поддержку."
        )