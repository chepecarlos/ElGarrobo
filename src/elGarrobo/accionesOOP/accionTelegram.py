from .accionBase import accionBase
from elGarrobo.miLibrerias import EnviarMensajeTelegram

from elGarrobo.miLibrerias import ConfigurarLogging

Logger = ConfigurarLogging(__name__)


class accionTelegram(accionBase):
    def __init__(self) -> None:
        nombre = "TelegramBot"
        comando = "telegram"
        descripcion = "Envia un mensaje por TelegramBot"
        super().__init__(nombre, comando, descripcion)

        propiedadMensaje = {
            "nombre": "Mensaje",
            "tipo": str,
            "obligatorio": True,
            "atributo": "mensaje",
            "descripcion": "Mensaje a enviar",
            "ejemplo": "Hola amigo",
        }

        propiedadTokenBot = {
            "nombre": "TokenBot",
            "tipo": str,
            "obligatorio": False,
            "atributo": "token",
            "descripcion": "Token para controlar Bot",
            "ejemplo": "1234:ABCD",
            "defecto": "Usando data/TelegramBot.json - Token_Telegram",
        }

        propiedadIdChat = {
            "nombre": "IdChat",
            "tipo": str,
            "obligatorio": False,
            "atributo": "id",
            "descripcion": "Token para controlar Bot",
            "ejemplo": "1234:ABCD",
            "defecto": "Usando data/TelegramBot.json - ID_Chat"
        }

        self.agregarPropiedad(propiedadMensaje)
        self.agregarPropiedad(propiedadTokenBot)
        self.agregarPropiedad(propiedadIdChat)

        self.funcion = self.mensajeTelegram

    def mensajeTelegram(self):
        mensaje = self.obtenerValor("mensaje")
        tokenBot = self.obtenerValor("token")
        idChat = self.obtenerValor("id")

        if mensaje is None:
            return
      
        EnviarMensajeTelegram(mensaje, tokenBot, idChat)
