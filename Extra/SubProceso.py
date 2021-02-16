import subprocess

from Extra.Depuracion import Imprimir


def EmpezarSubProceso(Comando):
    '''Crear nuevo Sub Proceso '''
    process = subprocess.Popen(Comando, stdout=subprocess.PIPE, universal_newlines=True)

    while True:
        output = process.stdout.readline()
        Imprimir(output.strip())
        return_code = process.poll()
        if return_code is not None:
            Imprimir(f'RETURN CODE {return_code}')
            for output in process.stdout.readlines():
                Imprimir(output.strip())
            return return_code
            break
