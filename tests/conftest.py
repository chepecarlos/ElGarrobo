"""HOME temporal para todos los tests: ObtenerFolderConfig usa Path.home() y los tests no deben escribir en ~/.config/elgarrobo"""

import os
import tempfile

# Aquí y no en un fixture: los módulos configuran el log en la carpeta de config al importarse
# ponytail: la carpeta temporal no se borra al terminar, el sistema limpia /tmp
os.environ["HOME"] = tempfile.mkdtemp(prefix="elgarrobo-tests-")
