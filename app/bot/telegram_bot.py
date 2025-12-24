from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.utils.config import config
from app.utils.logger import logger
from app.database.session import engine, get_db
from app.database.models import Base
from app.bot.handlers.commands import (
    start_command, analyze_command, history_command,
    stats_command, feedback_command, help_command
)
from app.bot.handlers.photo_handler import handle_photo
from app.bot.handlers.settings import (
    settings_callback, set_timeframe_callback, set_indicators_callback,
    set_sensitivity_callback, set_language_callback,
    back_to_main_callback, back_to_settings_callback
)
from app.bot.handlers.feedback import feedback_callback

class TradingBot:
    def __init__(self):
        self.application = None
        
    async def post_init(self, application: Application):
        """Post initialization"""
        # Create database tables
        Base.metadata.create_all(bind=engine)
        
        # Get database session
        db = next(get_db())
        application.bot_data['db'] = db
        
        logger.info("Bot initialized successfully")
        
    def setup_handlers(self):
        """Setup all handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("analyze", analyze_command))
        self.application.add_handler(CommandHandler("history", history_command))
        self.application.add_handler(CommandHandler("stats", stats_command))
        self.application.add_handler(CommandHandler("feedback", feedback_command))
        self.application.add_handler(CommandHandler("help", help_command))
        
        # Photo handler
        self.application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(settings_callback, pattern='settings'))
        self.application.add_handler(CallbackQueryHandler(set_timeframe_callback, pattern='^timeframe_|set_timeframe$'))
        self.application.add_handler(CallbackQueryHandler(set_indicators_callback, pattern='^indicator_|set_indicators$'))
        self.application.add_handler(CallbackQueryHandler(set_sensitivity_callback, pattern='^sensitivity_|set_sensitivity$'))
        self.application.add_handler(CallbackQueryHandler(set_language_callback, pattern='^language_|set_language$'))
        self.application.add_handler(CallbackQueryHandler(feedback_callback, pattern='^feedback_'))
        self.application.add_handler(CallbackQueryHandler(back_to_main_callback, pattern='back_to_main'))
        self.application.add_handler(CallbackQueryHandler(back_to_settings_callback, pattern='back_to_settings'))
        
        # Default handler for unknown commands
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_unknown))
    
    async def handle_unknown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown messages"""
        await update.message.reply_text(
            "Я понимаю только команды и изображения графиков.\n"
            "Используйте /help для списка команд.",
            reply_markup=get_main_menu_keyboard()
        )
    
    def run(self):
        """Run the bot"""
        self.application = Application.builder()\
            .token(config.BOT_TOKEN)\
            .post_init(self.post_init)\
            .build()
        
        self.setup_handlers()
        
        logger.info("Starting bot polling...")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)