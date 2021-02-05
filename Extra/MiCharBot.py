import telegram
from telegram import ParseMode
from Extra.CargarData import CargarData


def EnviarMensaje(Mensaje):
    Token = CargarData("Recursos/TelegramBot.json")
    bot = telegram.Bot(token=Token['Token_Telegram'])
    bot.send_message(chat_id=Token['ID_Chat'], text=Mensaje, parse_mode=ParseMode.HTML)
