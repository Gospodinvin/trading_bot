from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from app.database.crud import get_or_create_user, get_user_predictions, get_bot_statistics
from app.bot.keyboards import get_main_menu_keyboard, get_feedback_keyboard
from app.utils.logger import logger

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    db = context.bot_data['db']
    
    # Register user in database
    db_user = get_or_create_user(
        db, 
        telegram_id=user.id, 
        username=user.username, 
        first_name=user.first_name, 
        last_name=user.last_name
    )
    
    welcome_text = f"""
👋 Привет, {user.first_name}! 

Я - AI-бот для анализа свечных графиков с использованием машинного обучения.

🎯 **Что я умею:**
• Анализировать фотографии свечных графиков
• Предсказывать движение цены с помощью ML моделей
• Давать рекомендации по риск-менеджменту
• Учитывать технические индикаторы

📸 **Как использовать:**
1. Отправьте мне фото свечного графика
2. Или используйте команду /analyze
3. Получите детальный анализ с предсказанием

⚙️ **Настройки:** /settings
📊 **История:** /history
📈 **Статистика:** /stats

Начните с отправки фото графика или используйте меню ниже👇
    """
    
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu_keyboard())

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /analyze command"""
    text = """
📊 **Анализ графика**

Отправьте мне фотографию свечного графика для анализа.

**Требования к изображению:**
• Четкое изображение графика
• Видны свечи и шкала цены
• Рекомендуется скриншот с TradingView

**Что будет проанализировано:**
1. Паттерны свечей
2. Технические индикаторы
3. Уровни поддержки/сопротивления
4. Тренд и волатильность

Отправьте фото сейчас👇
    """
    
    await update.message.reply_text(text)

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /history command"""
    user = update.effective_user
    db = context.bot_data['db']
    
    predictions = get_user_predictions(db, user.id, limit=5)
    
    if not predictions:
        await update.message.reply_text(
            "У вас пока нет истории предсказаний.\n"
            "Отправьте фото графика для первого анализа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    history_text = "📊 **Ваши последние предсказания:**\n\n"
    
    for pred in predictions:
        result_emoji = {
            None: "⏳",
            'correct': "✅",
            'incorrect': "❌",
            'partial': "⚠️"
        }
        
        actual = pred.actual_result if pred.actual_result else None
        emoji = result_emoji.get(actual, "⏳")
        
        history_text += f"""
{emoji} **#{pred.id}** - {pred.created_at.strftime('%d.%m %H:%M')}
• Направление: {pred.prediction}
• Уверенность: {pred.confidence*100:.1f}%
• Таймфрейм: {pred.timeframe}
• Результат: {pred.actual_result if pred.actual_result else 'Ожидает проверки'}
"""
    
    history_text += "\n📈 Для нового анализа отправьте фото графика!"
    
    await update.message.reply_text(history_text, reply_markup=get_main_menu_keyboard())

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command"""
    db = context.bot_data['db']
    stats = get_bot_statistics(db)
    
    stats_text = f"""
📈 **СТАТИСТИКА БОТА**

👥 Пользователей: {stats['users']}
📊 Всего анализов: {stats['total']}
✅ Правильных: {stats['correct']}
🎯 Точность: {stats['accuracy']}%

📅 Анализов сегодня: {stats['daily']}

📊 **ДОСТИЖЕНИЯ:**
• {stats['total'] // 100 * 100}+ анализов выполнено
• {stats['users'] // 50 * 50}+ активных пользователей
• {max(0, int(stats['accuracy'] // 10 * 10))}+% целевая точность

⚠️ *Точность рассчитывается только по проверенным предсказаниям*
"""
    
    await update.message.reply_text(stats_text, reply_markup=get_main_menu_keyboard())

async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /feedback command"""
    user = update.effective_user
    db = context.bot_data['db']
    
    predictions = get_user_predictions(db, user.id, limit=1)
    
    if not predictions:
        await update.message.reply_text(
            "У вас нет предсказаний для обратной связи.\n"
            "Сначала отправьте фото графика для анализа!",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    last_prediction = predictions[0]
    
    feedback_text = f"""
💬 **ОБРАТНАЯ СВЯЗЬ**

Помогите улучшить бота! Оцените точность последнего предсказания.

📊 **Предсказание #{last_prediction.id}**
• Дата: {last_prediction.created_at.strftime('%d.%m.%Y %H:%M')}
• Направление: {last_prediction.prediction}
• Уверенность: {last_prediction.confidence*100:.1f}%

🤔 **Было ли предсказание правильным?**

Ваш фидбек поможет улучшить ML модель!
"""
    
    await update.message.reply_text(
        feedback_text, 
        reply_markup=get_feedback_keyboard(last_prediction.id)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
🆘 **ПОМОЩЬ И ПОДДЕРЖКА**

**Основные команды:**
/start - Запуск бота
/analyze - Анализ графика
/settings - Настройки
/history - История предсказаний
/stats - Статистика бота
/feedback - Обратная связь
/help - Эта справка

**Как использовать:**
1. Отправьте фото свечного графика
2. Дождитесь анализа (10-15 секунд)
3. Получите детальный отчет с предсказанием
4. Оцените точность через /feedback

**Требования к фото:**
• Четкое изображение графика
• Видны свечи и оси
• Лучше всего скриншоты с TradingView

**ML модели:**
• CNN для распознавания паттернов
• LSTM для временных рядов
• Ensemble модель для финального предсказания

**Поддержка:**
По вопросам и предложениям: @ваш_админ

⚠️ **ВАЖНО:** Бот для образовательных целей. Торговые решения принимайте самостоятельно.
"""
    
    await update.message.reply_text(help_text, reply_markup=get_main_menu_keyboard())