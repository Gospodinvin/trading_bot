from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from app.bot.keyboards import (
    get_main_menu_keyboard, get_settings_keyboard, get_timeframe_keyboard,
    get_indicators_keyboard, get_sensitivity_keyboard, get_language_keyboard
)
from app.database.crud import update_user_settings, get_or_create_user
from app.utils.logger import logger

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callback"""
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    user = update.effective_user
    
    db_user = get_or_create_user(db, telegram_id=user.id)
    settings = db_user.settings or {}
    
    settings_text = f"""
⚙️ **НАСТРОЙКИ**

Текущие настройки:
• Таймфрейм: {settings.get('timeframe', '5m')}
• Индикаторы: {', '.join(settings.get('indicators', ['RSI', 'MACD']))}
• Чувствительность: {settings.get('sensitivity', 'medium').capitalize()}
• Язык: {settings.get('language', 'ru').upper()}
• Уведомления: {'✅ Вкл' if settings.get('notifications', True) else '❌ Выкл'}

Выберите параметр для изменения:
"""
    
    await query.edit_message_text(
        settings_text,
        reply_markup=get_settings_keyboard()
    )

async def set_timeframe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle timeframe selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('timeframe_'):
        timeframe = query.data.split('_')[1]
        
        db = context.bot_data['db']
        user = update.effective_user
        
        db_user = get_or_create_user(db, telegram_id=user.id)
        update_user_settings(db, db_user.id, {'timeframe': timeframe})
        
        await query.edit_message_text(
            f"✅ Таймфрейм изменен на: {timeframe}",
            reply_markup=get_timeframe_keyboard()
        )
    else:
        await query.edit_message_text(
            "📅 Выберите таймфрейм для анализа:",
            reply_markup=get_timeframe_keyboard()
        )

async def set_indicators_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle indicators selection"""
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    user = update.effective_user
    
    db_user = get_or_create_user(db, telegram_id=user.id)
    settings = db_user.settings or {}
    current_indicators = settings.get('indicators', ['RSI', 'MACD'])
    
    if query.data.startswith('indicator_'):
        indicator_name = query.data.split('_')[1]
        
        if indicator_name == 'all':
            new_indicators = ['RSI', 'MACD', 'SMA', 'EMA', 'Bollinger', 'Stochastic', 'Ichimoku', 'ATR']
        elif indicator_name == 'none':
            new_indicators = []
        else:
            # Toggle indicator
            indicator_map = {
                'rsi': 'RSI',
                'macd': 'MACD',
                'sma': 'SMA',
                'ema': 'EMA',
                'bb': 'Bollinger',
                'stoch': 'Stochastic',
                'ichi': 'Ichimoku',
                'atr': 'ATR'
            }
            
            indicator = indicator_map.get(indicator_name)
            if indicator in current_indicators:
                new_indicators = [i for i in current_indicators if i != indicator]
            else:
                new_indicators = current_indicators + [indicator]
        
        update_user_settings(db, db_user.id, {'indicators': new_indicators})
        
        await query.edit_message_text(
            f"✅ Индикаторы обновлены: {', '.join(new_indicators) if new_indicators else 'Нет'}",
            reply_markup=get_indicators_keyboard(new_indicators)
        )
    else:
        await query.edit_message_text(
            "📊 Выберите технические индикаторы:",
            reply_markup=get_indicators_keyboard(current_indicators)
        )

async def set_sensitivity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle sensitivity selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('sensitivity_'):
        sensitivity = query.data.split('_')[1]
        
        db = context.bot_data['db']
        user = update.effective_user
        
        db_user = get_or_create_user(db, telegram_id=user.id)
        update_user_settings(db, db_user.id, {'sensitivity': sensitivity})
        
        sensitivity_names = {
            'low': 'Низкая',
            'medium': 'Средняя',
            'high': 'Высокая'
        }
        
        await query.edit_message_text(
            f"✅ Чувствительность изменена на: {sensitivity_names.get(sensitivity, sensitivity)}",
            reply_markup=get_sensitivity_keyboard()
        )
    else:
        await query.edit_message_text(
            "🎯 Выберите чувствительность модели:",
            reply_markup=get_sensitivity_keyboard()
        )

async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('language_'):
        language = query.data.split('_')[1]
        
        db = context.bot_data['db']
        user = update.effective_user
        
        db_user = get_or_create_user(db, telegram_id=user.id)
        update_user_settings(db, db_user.id, {'language': language})
        
        language_names = {
            'ru': 'Русский',
            'en': 'English',
            'es': 'Español',
            'zh': '中文'
        }
        
        await query.edit_message_text(
            f"✅ Язык изменен на: {language_names.get(language, language)}",
            reply_markup=get_language_keyboard()
        )
    else:
        await query.edit_message_text(
            "🌐 Выберите язык интерфейса:",
            reply_markup=get_language_keyboard()
        )

async def back_to_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to main menu"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "Главное меню:",
        reply_markup=get_main_menu_keyboard()
    )

async def back_to_settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to settings"""
    query = update.callback_query
    await query.answer()
    
    await settings_callback(update, context)