import telegram
from telegram import ParseMode
from Extra.CargarData import CargarData


def EnviarMensaje(ChatID,  Mensaje):
    Token = CargarData("Recursos/TelegramBot.json")
    bot = telegram.Bot(token=Token['Token_Telegram'])
    bot.send_message(chat_id=ChatID, text=Mensaje, parse_mode=ParseMode.HTML)
