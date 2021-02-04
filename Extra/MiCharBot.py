import telegram
from telegram import ParseMode


def EnviarMensaje(MiToken, MiID,  mensaje):
    bot = telegram.Bot(token=MiToken)
    bot.send_message(chat_id=MiID, text=mensaje, parse_mode=ParseMode.HTML)
