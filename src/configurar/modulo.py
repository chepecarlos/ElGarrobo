from sys import modules

from elGarrobo.miLibrerias import ConfigurarLogging, ObtenerArchivo, SalvarValor

logger = ConfigurarLogging(__name__)


class color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def ConfigurarModulos():
    print("Configurar el Sistema")
    Data_Modulos = ObtenerArchivo("modulos/configurar.json")
    Estado_Modulos = ObtenerArchivo("modulos/modulos.json")

    for Modulo in Data_Modulos:
        Nombre = Modulo["nombre"]
        Tipo = Modulo["tipo"]
        Estado = False
        Descripcion = ""

        if Modulo["atributo"] in Estado_Modulos:
            Estado = Estado_Modulos[Modulo["atributo"]]
        if "descripcion" in Modulo:
            Descripcion = Modulo["descripcion"]

        Mensaje_Estado = "Activo" if Estado else "Apagado"
        print("-" * 80)
        print(f"{Nombre}[{Tipo}] - {Mensaje_Estado}")
        print(f"Descripcion: {Descripcion}")
        print(f"Activar?[{color.BOLD}Si/No{color.END}]", end="")
        Modulo["nuevo_estado"] = Respuesta(Estado)

    for Modulo in Data_Modulos:
        Atributo = Modulo["atributo"]
        Estado_nuevo = Modulo["nuevo_estado"]
        if Atributo in Estado_Modulos:
            Estado = Estado_Modulos[Modulo["atributo"]]
            if Estado != Estado_nuevo:
                print(f"Actualizando[{Atributo}] {Estado_nuevo}")
                SalvarValor("modulos/modulos.json", Atributo, Estado_nuevo)
        else:
            print(f"Actualizando[{Atributo}] {Estado_nuevo}")
            SalvarValor("modulos/modulos.json", Atributo, Estado_nuevo)


def Respuesta(Estado):
    RespuestraTrue = {"si", "yes", "s", "y"}
    Respuesta = str(input())
    Respuesta = Respuesta.lower()
    if Respuesta in RespuestraTrue:
        return True
    elif Respuesta == "":
        return Estado
    return False
