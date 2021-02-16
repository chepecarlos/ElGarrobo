import subprocess

from Extra.Depuracion import Imprimir


def EmpezarSubProceso(Comando):
    '''Crear nuevo Sub Proceso '''
    process = subprocess.Popen(Comando, stdout=subprocess.PIPE, universal_newlines=True)

    while True:
        output = process.stdout.readline()
        Imprimir(output.strip())
        # Do something else
        return_code = process.poll()
        if return_code is not None:
            Imprimir('RETURN CODE', return_code)
            # Process has finished, read rest of the output
            for output in process.stdout.readlines():
                Imprimir(output.strip())
            return return_code
            break
