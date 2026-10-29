from unittest.mock import MagicMock, patch

import requests

from elGarrobo.modulos.fdmMonster.moduloFdmMonster import moduloFdmMonster


def _error401():
    return requests.HTTPError("401 Client Error", response=MagicMock(status_code=401))


def test_token_vencido_renueva_sesion_sin_error():
    modulo = moduloFdmMonster({"url": "http://x", "usuario": "u"})
    modulo.activo = True
    # 1er ciclo bien, 2do token vencido, 3ro (sesión nueva) bien y detiene
    consultas = [None, _error401(), None]

    def consultar(*_):
        resultado = consultas.pop(0)
        if not consultas:
            modulo.activo = False
        if resultado:
            raise resultado

    with (
        patch.object(modulo, "_iniciar_sesion", return_value=MagicMock()) as login,
        patch.object(modulo, "_consultar_impresoras", side_effect=consultar),
        patch.object(modulo, "_revisar_trabajos"),
        patch("elGarrobo.modulos.fdmMonster.moduloFdmMonster.time.sleep") as dormir,
        patch("elGarrobo.modulos.fdmMonster.moduloFdmMonster.logger") as log,
    ):
        modulo._monitorear_estado("http://x/api/v2", 5, 30, 3)

    assert login.call_count == 2
    assert dormir.call_count == 2  # el reintento tras el 401 no espera
    log.error.assert_not_called()


def test_401_con_sesion_nueva_si_es_error():
    modulo = moduloFdmMonster({"url": "http://x", "usuario": "u"})
    modulo.activo = True

    def consultar(*_):
        modulo.activo = False
        raise _error401()

    with (
        patch.object(modulo, "_iniciar_sesion", return_value=MagicMock()),
        patch.object(modulo, "_consultar_impresoras", side_effect=consultar),
        patch("elGarrobo.modulos.fdmMonster.moduloFdmMonster.time.sleep"),
        patch("elGarrobo.modulos.fdmMonster.moduloFdmMonster.logger") as log,
    ):
        modulo._monitorear_estado("http://x/api/v2", 5, 30, 3)

    log.error.assert_called_once()
