import pytchat
import re
from Extra.FuncionesProyecto import GuardadDato
from Extra.MiMQTT import EnviarMQTTSimple

colores = ["rojo", "azul", "verde", "blanco", "gris", "aqua", "amarillo", "naranja", "morado"]
ExprecionColores = '\#[a-fA-f0-9][a-fA-f0-9][a-fA-f0-9][a-fA-f0-9][a-fA-f0-9][a-fA-f0-9]'


def ChatYoutube(IdVideo):
    chat = pytchat.create(video_id=IdVideo)
    while chat.is_alive():
        for c in chat.get().sync_items():
            if(c.author.isChatSponsor):
                print(f"Sponsor")
            if(c.type == "superChat"):
                print(f"Super chat {c.amountString}")
            print(f"{c.datetime} - [{c.type}] [{c.author.name}]- {c.message}")


def SalvarChatYoutube(Directorio, IdVideo):
    global colores
    global ExprecionColores
    print(f"El ID es {IdVideo}")
    ChatYoutube = pytchat.create(video_id=IdVideo)
    while ChatYoutube.is_alive():
        for Chat in ChatYoutube.get().sync_items():
            ChatData = {
                "Tiempo": Chat.datetime,
                "Tipo": Chat.type,
                "Nombre": Chat.author.name,
                "CanalID": Chat.author.channelId,
                "Mensaje": Chat.message
            }
            print(f"{Chat.datetime} [{Chat.author.name} - {Chat.type}]- {Chat.message}")
            GuardadDato(Directorio + "/9.Chat/ChatGeneral.json", ChatData)

            Filtro = "pregunta"
            if FiltranChat(Chat.message, Filtro):
                print(f"Filtro: {Filtro}")
                GuardadDato(Directorio + "/9.Chat/Chat" + Filtro + ".json", ChatData)
            if FiltranChat(Chat.message, "reiniciar"):
                print(f"Reiniciando gracias a {Chat.author.name}")
                GuardadDato(Directorio + "/9.Chat/Comandos.json", ChatData)
                EnviarMQTTSimple("fondo/reiniciar", "1")
            if FiltranChat(Chat.message, "color"):
                if FiltrarChatComando(Chat.message, colores) != 'no':
                    Color = FiltrarChatComando(Chat.message, colores)
                    print(f"Cambiando color gracias a {Chat.author.name}")
                    GuardadDato(Directorio + "/9.Chat/Comandos.json", ChatData)
                    EnviarMQTTSimple("fondo/color", Color)
                elif FiltrarExprecion(Chat.message, ExprecionColores):
                    Color = FiltrarExprecion(Chat.message, ExprecionColores)
                    GuardadDato(Directorio + "/9.Chat/Comandos.json", ChatData)
                    EnviarMQTTSimple("fondo/expresion/color", Color[0])
            if Chat.author.isChatSponsor:
                DatoExtra = {"Miembro": Chat.author.isChatSponsor}
                ChatData.append(DatoExtra)
                GuardadDato(Directorio + "/9.Chat/ChatMiembro.json", ChatData)
                print(f"Sponsor")
            if Chat.type == "superChat":
                DataExtra = {
                    "SuperChat": Chat.amountString,
                    "URL": Chat.author.channelUrl
                }
                ChatData.append(DataExtra)
                GuardadDato(Directorio + "/9.Chat/ChatSuperChat.json", ChatData)
                print(f"Super chat {Chat.amountString}")


def FiltranChat(Mensaje, Palabra):
    if Mensaje:
        Palabra = Palabra.lower()
        Mensaje = Mensaje.lower()
        if Palabra in Mensaje:
            return True
    return False


def FiltrarChatComando(Mensaje, Comandos):
    if Mensaje:
        for Comando in Comandos:
            if Comando in Mensaje:
                return Comando
    return 'no'


def FiltrarExprecion(Mensaje, Expresion):
    return re.findall(Expresion, Mensaje)

if __name__ == '__main__':
    print("Empezando prueba")
    # ChatYoutube("GfSidouUVlw")
    print(FiltranChat("Pregunta como encender led", "Pregunta"))
