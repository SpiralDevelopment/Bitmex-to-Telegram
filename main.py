from bot_manager import TelegramBot

bot_mgr = TelegramBot()

if bot_mgr.is_initialized:
    bot_mgr.run()
