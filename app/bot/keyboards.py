from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📊 Анализ графика", callback_data='analyze')],
        [InlineKeyboardButton("⚙️ Настройки", callback_data='settings'),
         InlineKeyboardButton("📈 История", callback_data='history')],
        [InlineKeyboardButton("📊 Статистика", callback_data='stats'),
         InlineKeyboardButton("💬 Обратная связь", callback_data='feedback')],
        [InlineKeyboardButton("🆘 Помощь", callback_data='help')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    keyboard = [
        [InlineKeyboardButton("📅 Таймфрейм", callback_data='set_timeframe')],
        [InlineKeyboardButton("📊 Индикаторы", callback_data='set_indicators')],
        [InlineKeyboardButton("🎯 Чувствительность", callback_data='set_sensitivity')],
        [InlineKeyboardButton("🌐 Язык", callback_data='set_language')],
        [InlineKeyboardButton("🔔 Уведомления", callback_data='set_notifications')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_timeframe_keyboard():
    keyboard = [
        [InlineKeyboardButton("1 минута", callback_data='timeframe_1m'),
         InlineKeyboardButton("5 минут", callback_data='timeframe_5m')],
        [InlineKeyboardButton("15 минут", callback_data='timeframe_15m'),
         InlineKeyboardButton("30 минут", callback_data='timeframe_30m')],
        [InlineKeyboardButton("1 час", callback_data='timeframe_1h'),
         InlineKeyboardButton("4 часа", callback_data='timeframe_4h')],
        [InlineKeyboardButton("1 день", callback_data='timeframe_1d')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_to_settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_indicators_keyboard(selected_indicators=None):
    if selected_indicators is None:
        selected_indicators = []
    
    indicators = [
        ('RSI', 'indicator_rsi'),
        ('MACD', 'indicator_macd'),
        ('SMA', 'indicator_sma'),
        ('EMA', 'indicator_ema'),
        ('Bollinger', 'indicator_bb'),
        ('Stochastic', 'indicator_stoch'),
        ('Ichimoku', 'indicator_ichi'),
        ('ATR', 'indicator_atr')
    ]
    
    keyboard = []
    row = []
    for i, (name, callback) in enumerate(indicators):
        prefix = "✅ " if name in selected_indicators else ""
        row.append(InlineKeyboardButton(f"{prefix}{name}", callback_data=callback))
        if len(row) == 2 or i == len(indicators) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([
        InlineKeyboardButton("✅ Выбрать все", callback_data='indicators_all'),
        InlineKeyboardButton("❌ Очистить", callback_data='indicators_none')
    ])
    keyboard.append([InlineKeyboardButton("↩️ Назад", callback_data='back_to_settings')])
    
    return InlineKeyboardMarkup(keyboard)

def get_sensitivity_keyboard():
    keyboard = [
        [InlineKeyboardButton("🟢 Низкая", callback_data='sensitivity_low')],
        [InlineKeyboardButton("🟡 Средняя", callback_data='sensitivity_medium')],
        [InlineKeyboardButton("🔴 Высокая", callback_data='sensitivity_high')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_to_settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard():
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='language_ru')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='language_en')],
        [InlineKeyboardButton("🇪🇸 Español", callback_data='language_es')],
        [InlineKeyboardButton("🇨🇳 中文", callback_data='language_zh')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_to_settings')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_feedback_keyboard(prediction_id):
    keyboard = [
        [InlineKeyboardButton("✅ Правильно", callback_data=f'feedback_{prediction_id}_correct')],
        [InlineKeyboardButton("❌ Неправильно", callback_data=f'feedback_{prediction_id}_incorrect')],
        [InlineKeyboardButton("➡️ Частично правильно", callback_data=f'feedback_{prediction_id}_partial')],
        [InlineKeyboardButton("↩️ Назад", callback_data='back_to_main')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard():
    keyboard = [[InlineKeyboardButton("↩️ Назад", callback_data='back_to_main')]]
    return InlineKeyboardMarkup(keyboard)