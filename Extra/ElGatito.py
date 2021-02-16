from Extra.Depuracion import Imprimir

import Extra.TecladoMacro as TecladoMacros


class ElGatito(object):

    def __init__(self, Data):
        self.Data = Data
        Imprimir("Iniciando ElGatito")
        self.CargarTeclados()

    def CargarTeclados(self):
        if 'Teclados' in self.Data:
            self.ListaTeclados = []
            for Teclado in self.Data['Teclados']:
                TecladoActual = TecladoMacros.TecladoMacro(Teclado['Nombre'], Teclado['Input'], Teclado['File'])
                if TecladoActual.Conectar():
                    self.ListaTeclados.append(TecladoActual)
            self.ConfigurandoTeclados("")

    def ConfigurandoTeclados(self, Directorio):
        for Teclado in self.ListaTeclados:
            Teclado.ActualizarTeclas(Directorio)
