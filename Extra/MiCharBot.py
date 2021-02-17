import telegram
from telegram import ParseMode

from Extra.FuncionesArchivos import ObtenerDato


def EnviarMensaje(Mensaje):
    Token = ObtenerDato("/Data/TelegramBot.json", 'Token_Telegram')
    ID_Chat = ObtenerDato("/Data/TelegramBot.json", 'ID_Chat')
    bot = telegram.Bot(token=Token)
    bot.send_message(chat_id=ID_Chat, text=Mensaje, parse_mode=ParseMode.HTML)
