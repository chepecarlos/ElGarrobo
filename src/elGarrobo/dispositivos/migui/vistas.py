"""Vistas previas de las teclas servidas por /vista/{hash} para que el navegador las guarde en caché"""

import base64
import hashlib
import io
import threading

from fastapi import Response

_vistas: dict[str, tuple[bytes, str]] = {}
"hash → (contenido, tipo) de las vistas previas de las teclas, las sirve /vista/{hash}"
_candadoVistas = threading.Lock()
"Los dispositivos redibujan la GUI desde sus hilos"
MAXIMO_VISTAS = 1024


def urlVista(imagen) -> str:
    """URL de la vista previa (imagen PIL o data URI de dibujarAnimado) con el hash de su contenido.

    El navegador la guarda en caché: al redibujar una pestaña solo viaja la ruta y no la imagen en base64
    """
    if isinstance(imagen, str):
        tipo, datos = imagen.removeprefix("data:").split(";base64,", 1)
        contenido = base64.b64decode(datos)
    else:
        buffer = io.BytesIO()
        imagen.save(buffer, "PNG")
        contenido, tipo = buffer.getvalue(), "image/png"
    nombre = hashlib.sha1(contenido).hexdigest()
    with _candadoVistas:
        _vistas.pop(nombre, None)
        _vistas[nombre] = (contenido, tipo)
        # ponytail: se borra la más vieja; una pestaña abierta mucho tiempo que no la tenga en caché la vería rota hasta redibujar
        if len(_vistas) > MAXIMO_VISTAS:
            del _vistas[next(iter(_vistas))]
    return f"/vista/{nombre}"


def servirVista(nombre: str) -> Response:
    vista = _vistas.get(nombre)
    if vista is None:
        return Response(status_code=404)
    # El nombre es el hash del contenido: nunca cambia, el navegador no vuelve a pedirla
    return Response(vista[0], media_type=vista[1], headers={"Cache-Control": "public, max-age=31536000, immutable"})
