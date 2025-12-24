from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.database.crud import update_prediction_feedback
from app.bot.keyboards import get_main_menu_keyboard
from app.utils.logger import logger

async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle feedback callback"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('feedback_'):
        try:
            # Parse feedback data: feedback_<prediction_id>_<result>
            parts = query.data.split('_')
            if len(parts) >= 3:
                prediction_id = int(parts[1])
                result = parts[2]
                
                db = context.bot_data['db']
                
                # Map result to actual result
                result_map = {
                    'correct': 'correct',
                    'incorrect': 'incorrect',
                    'partial': 'partial'
                }
                
                actual_result = result_map.get(result, 'partial')
                
                # Update prediction with feedback
                update_prediction_feedback(
                    db, 
                    prediction_id, 
                    actual_result,
                    f"Feedback via button: {result}"
                )
                
                # Send thank you message
                await query.edit_message_text(
                    f"🙏 Спасибо за обратную связь!\n"
                    f"Ваша оценка поможет улучшить ML модель.\n\n"
                    f"Предсказание #{prediction_id} отмечено как: "
                    f"{'✅ Правильно' if result == 'correct' else '❌ Неправильно' if result == 'incorrect' else '⚠️ Частично правильно'}",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await query.edit_message_text(
                    "❌ Ошибка обработки фидбека",
                    reply_markup=get_main_menu_keyboard()
                )
                
        except Exception as e:
            logger.error(f"Feedback error: {e}")
            await query.edit_message_text(
                "❌ Ошибка при сохранении фидбека",
                reply_markup=get_main_menu_keyboard()
            )