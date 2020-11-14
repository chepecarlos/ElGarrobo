import pytchat
from Extra.FuncionesProyecto import GuardadDato


def ChatYoutube(IdVideo):
    chat = pytchat.create(video_id=IdVideo)
    while chat.is_alive():
        for c in chat.get().sync_items():
            if(c.author.isChatSponsor):
                print(f"Sponsor")
            if(c.type == "superChat"):
                print(f"Super chat {c.amountString}")
            print(f"{c.datetime} - [{c.type}] [{c.author.name}]- {c.message}")


def SalvarChatYoutube(IdVideo):
    print(f"El ID es {IdVideo}")
    ChatYoutube = pytchat.create(video_id=IdVideo)
    while ChatYoutube.is_alive():
        for Chat in ChatYoutube.get().sync_items():
            ChatData = {
                "Tiempo": Chat.datetime,
                "Tipo": Chat.type,
                "Nombre": Chat.author.name,
                "Mensaje": Chat.message
            }
            print(f"{Chat.datetime} [{Chat.author.name} - {Chat.type}]- {Chat.message}")
            GuardadDato("ChatGeneral.md", ChatData)

            if(Chat.author.isChatSponsor):
                DatoExtra ={"Publicidad": Chat.author.isChatSponsor }
                ChatData.append(DatoExtra)
                GuardadDato("ChatSponsor.md", ChatData)
                print(f"Sponsor")
            if(Chat.type == "superChat"):
                DataExtra ={
                    "SuperChat": Chat.amountString,
                    "URL": Chat.author.channelUrl
                }
                ChatData.append(DatoExtra)
                GuardadDato("ChatSuperChat.md", ChatData)
                print(f"Super chat {c.amountString}")


if __name__=='__main__':
    ChatYoutube("GfSidouUVlw")
