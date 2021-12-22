from sys import modules
from MiLibrerias import ConfigurarLogging, ObtenerArchivo, SalvarValor

logger = ConfigurarLogging(__name__)


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
        print("-"*40)
        print(f"{Nombre}[{Tipo}] Actual({Estado})")
        print(f"Descripcion: {Descripcion}")
        print("Activar?(Si/No)")
        Modulo["nuevo_estado"] = Respuesta(Estado)
    for Modulo in Data_Modulos:
        Atributo = Modulo["atributo"]
        Estado = Estado_Modulos[Modulo["atributo"]]
        Estado_nuevo = Modulo["nuevo_estado"]
        if Estado != Estado_nuevo:
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
