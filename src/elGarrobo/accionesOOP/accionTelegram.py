"""Manda un mensaje por TelegramBot"""

from elGarrobo.miLibrerias import ConfigurarLogging, EnviarMensajeTelegram

from .accion import accion, propiedadAccion

Logger = ConfigurarLogging(__name__)


class accionTelegram(accion):
    """Manda un mensaje por TelegramBot"""

    nombre = "TelegramBot"
    comando = "telegram"
    descripcion = "Envia un mensaje por TelegramBot"

    def __init__(self) -> None:
        super().__init__(self.nombre, self.comando, self.descripcion)

        propiedadMensaje = propiedadAccion(
            nombre="Mensaje",
            tipo=str,
            obligatorio=True,
            atributo="mensaje",
            descripcion="Mensaje a enviar",
            ejemplo="Hola amigo",
        )

        propiedadTokenBot = propiedadAccion(
            nombre="TokenBot",
            tipo=str,
            obligatorio=False,
            atributo="token",
            descripcion="Token para controlar Bot",
            ejemplo="1234:ABCD",
            defecto="Usando data/TelegramBot.json - Token_Telegram",
        )

        propiedadIdChat = propiedadAccion(
            nombre="IdChat",
            tipo=str,
            obligatorio=False,
            atributo="id",
            descripcion="Token para controlar Bot",
            ejemplo="1234:ABCD",
            defecto="Usando data/TelegramBot.json - ID_Chat",
        )

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
