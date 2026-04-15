import importlib
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))


def cargar_modulo_mi_obs():
    return importlib.import_module("src.elGarrobo.modulos.mi_obs")


def crear_instancia_segura(monkeypatch, modulo_mi_obs):
    monkeypatch.setattr(modulo_mi_obs, "SalvarArchivo", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(modulo_mi_obs, "SalvarValor", lambda *_args, **_kwargs: None)
    return modulo_mi_obs.MiOBS()


class TestMiOBS:
    def test_notificar_llama_callback_con_alerta(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        callback = MagicMock()
        mi_obs.notificaciones = callback
        mi_obs.alertaOBS = {"topic": "alsw/alerta"}

        mi_obs.Notificar("OBS-Conectado")

        callback.assert_called_once_with("OBS-Conectado", {"topic": "alsw/alerta"})

    def test_notificar_no_hace_nada_si_no_hay_callback(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        mi_obs.notificaciones = None
        mi_obs.alertaOBS = {"topic": "alsw/alerta"}

        mi_obs.Notificar("OBS-Conectado")

        assert mi_obs.notificaciones is None

    def test_iniciar_acciones_registra_acciones_clave(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        acciones = {}

        mi_obs.IniciarAcciones(acciones)

        assert acciones["obs_conectar"] == mi_obs.conectar
        assert acciones["obs_desconectar"] == mi_obs.desconectar
        assert acciones["obs_grabar"] == mi_obs.cambiarGrabacion
        assert acciones["obs_envivo"] == mi_obs.cambiarEnVivo
        assert acciones["obs_escena"] == mi_obs.cambiarEscena

    def test_conectar_retorna_false_si_ya_esta_conectado(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        notificar = MagicMock()
        mi_obs.Notificar = notificar
        mi_obs.conectado = True

        resultado = mi_obs.conectar({})

        assert resultado is False
        notificar.assert_called_once_with("OBS-Ya-Conectado")
        mi_obs.conectado = False

    def test_conectar_exitoso_configura_clientes_y_monitoreo_audio(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        req_client = MagicMock()
        evt_client = MagicMock()
        req_ctor = MagicMock(return_value=req_client)
        evt_ctor = MagicMock(return_value=evt_client)

        monkeypatch.setattr(modulo_mi_obs.obs, "ReqClient", req_ctor)
        monkeypatch.setattr(modulo_mi_obs.obs, "EventClient", evt_ctor)
        monkeypatch.setattr(modulo_mi_obs.time, "sleep", lambda *_args, **_kwargs: None)

        def leer_data_falso(ruta):
            if ruta == "modulos":
                return {"obs_monitor_audio": True}
            if ruta == "modulos/audio_obs/audio":
                return ["Mic"]
            if ruta == "modulos/audio_obs/mqtt":
                return {"topic": "alsw/audio"}
            return {}

        monkeypatch.setattr(modulo_mi_obs, "leerData", leer_data_falso)

        mi_obs.Notificar = MagicMock()
        mi_obs.configurarEventos = MagicMock()
        mi_obs.salvarEstadoActual = MagicMock()
        mi_obs.empezarConsultaTiempo = MagicMock()

        resultado = mi_obs.conectar({"servidor": "127.0.0.1", "puerto": 4456, "password": "clave"})

        assert resultado is True
        assert mi_obs.conectado is True
        assert mi_obs.audioMonitoriar == ["Mic"]
        assert mi_obs.audioTopico == "alsw/audio"
        req_ctor.assert_called_once_with(host="127.0.0.1", port=4456, password="clave")

        esperado_subs = modulo_mi_obs.obs.Subs.LOW_VOLUME | modulo_mi_obs.obs.Subs.INPUTVOLUMEMETERS
        evt_ctor.assert_called_once_with(host="127.0.0.1", port=4456, password="clave", subs=esperado_subs)

        mi_obs.Notificar.assert_called_once_with("OBS-Conectado")
        mi_obs.configurarEventos.assert_called_once()
        mi_obs.salvarEstadoActual.assert_called_once()
        mi_obs.empezarConsultaTiempo.assert_called_once()
        mi_obs.conectado = False

    def test_conectar_falla_por_connection_refused(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        monkeypatch.setattr(modulo_mi_obs.obs, "ReqClient", MagicMock(side_effect=ConnectionRefusedError))
        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        monkeypatch.setattr(modulo_mi_obs, "leerData", lambda _ruta: {})

        mi_obs.Notificar = MagicMock()
        mi_obs.LimpiarTemporales = MagicMock()

        resultado = mi_obs.conectar({})

        assert resultado is False
        assert mi_obs.conectado is False
        assert mi_obs.clienteConsultas is None
        assert mi_obs.clienteEvento is None
        mi_obs.Notificar.assert_called_once_with("OBS-No-Encontrado")
        mi_obs.LimpiarTemporales.assert_called_once()
        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_conectar", False)

    def test_conectar_falla_por_excepcion_generica(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        monkeypatch.setattr(modulo_mi_obs.obs, "ReqClient", MagicMock(side_effect=RuntimeError("fallo")))
        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        monkeypatch.setattr(modulo_mi_obs, "leerData", lambda _ruta: {})

        mi_obs.Notificar = MagicMock()
        mi_obs.LimpiarTemporales = MagicMock()

        resultado = mi_obs.conectar({"servidor": "localhost", "puerto": 4455})

        assert resultado is False
        assert mi_obs.conectado is False
        assert mi_obs.clienteConsultas is None
        assert mi_obs.clienteEvento is None
        mi_obs.Notificar.assert_called_once_with("OBS-No-Encontrado")
        mi_obs.LimpiarTemporales.assert_called_once()
        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_conectar", False)

    def test_agregar_notificacion_guarda_funcion_y_alerta(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        monkeypatch.setattr(modulo_mi_obs, "leerData", lambda ruta: {"topic": ruta})
        callback = MagicMock()

        mi_obs.AgregarNotificacion(callback)

        assert mi_obs.notificaciones is callback
        assert mi_obs.alertaOBS == {"topic": "modulos/alerta_obs/mqtt"}

    def test_evento_stream_activo_notifica_y_guarda_estado(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.Notificar = MagicMock()
        mi_obs.actualizarDeck = MagicMock()

        mensaje = SimpleNamespace(output_active=True)
        mi_obs.on_stream_state_changed(mensaje)

        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_envivo", True)
        mi_obs.Notificar.assert_called_once_with("OBS-EnVivo")
        mi_obs.actualizarDeck.assert_called_once()
        assert mi_obs.envivo is True

    def test_evento_stream_inactivo_notifica_y_guarda_estado(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.Notificar = MagicMock()
        mi_obs.actualizarDeck = MagicMock()

        mensaje = SimpleNamespace(output_active=False)
        mi_obs.on_stream_state_changed(mensaje)

        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_envivo", False)
        mi_obs.Notificar.assert_called_once_with("OBS-No-EnVivo")
        mi_obs.actualizarDeck.assert_called_once()
        assert mi_obs.envivo is False

    def test_evento_grabacion_iniciada_actualiza_estado(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.Notificar = MagicMock()
        mi_obs.actualizarDeck = MagicMock()
        mi_obs.pausado = False

        mensaje = SimpleNamespace(output_state="OBS_WEBSOCKET_OUTPUT_STARTED")
        mi_obs.on_record_state_changed(mensaje)

        mi_obs.Notificar.assert_called_once_with("OBS-Grabando")
        assert mi_obs.grabando is True
        salvar_valor.assert_any_call(mi_obs.archivoEstado, "obs_grabar", True)
        salvar_valor.assert_any_call(mi_obs.archivoEstado, "obs_pausar", False)
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_grabacion_pausada_actualiza_estado(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.Notificar = MagicMock()
        mi_obs.actualizarDeck = MagicMock()
        mi_obs.grabando = True
        mi_obs.pausado = False

        mensaje = SimpleNamespace(output_state="OBS_WEBSOCKET_OUTPUT_PAUSED")
        mi_obs.on_record_state_changed(mensaje)

        mi_obs.Notificar.assert_called_once_with("OBS-Pause-Grabando")
        assert mi_obs.grabando is True
        assert mi_obs.pausado is True
        salvar_valor.assert_any_call(mi_obs.archivoEstado, "obs_grabar", True)
        salvar_valor.assert_any_call(mi_obs.archivoEstado, "obs_pausar", True)
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_escena_actualizada_guarda_estado_y_refresca(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.salvarFuente = MagicMock()
        mi_obs.actualizarDeck = MagicMock()

        mi_obs.on_current_program_scene_changed(SimpleNamespace(scene_name="Escena A"))

        assert mi_obs.escenaActual == "Escena A"
        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_escena", "Escena A")
        mi_obs.salvarFuente.assert_called_once()
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_virtualcam_activa_notifica_y_guarda(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.Notificar = MagicMock()
        mi_obs.actualizarDeck = MagicMock()

        mi_obs.on_virtualcam_state_changed(SimpleNamespace(output_active=True))

        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_camara_virtual", True)
        mi_obs.Notificar.assert_called_once_with("OBS-WebCamara")
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_filtro_fuente_guarda_y_refresca(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.actualizarDeck = MagicMock()

        mi_obs.on_source_filter_enable_state_changed(SimpleNamespace(filter_name="Color", source_name="Camara", filter_enabled=True))

        salvar_valor.assert_called_once_with("data/obs/obs_filtro", ["Camara", "Color"], True, depuracion=True)
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_visibilidad_fuente_guarda_y_refresca(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        monkeypatch.setattr(modulo_mi_obs, "ObtenerValor", lambda *_args, **_kwargs: "Camara")
        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.actualizarDeck = MagicMock()

        mi_obs.on_scene_item_enable_state_changed(SimpleNamespace(scene_name="Escena A", scene_item_id=9, scene_item_enabled=False))

        salvar_valor.assert_called_once_with("data/obs/obs_fuente", "Camara", False)
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_vendor_vertical_redirige_a_evento_vertical(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        mi_obs.eventoVertical = MagicMock()

        mensaje = SimpleNamespace(vendor_name="aitum-vertical-canvas", event_type="switch_scene")
        mi_obs.on_vendor_event(mensaje)

        mi_obs.eventoVertical.assert_called_once_with(mensaje)

    def test_evento_vertical_switch_scene_guarda_estado(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.actualizarDeck = MagicMock()

        mensaje = SimpleNamespace(event_type="switch_scene", event_data={"new_scene": "Vertical A"})
        mi_obs.eventoVertical(mensaje)

        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_escena_vertical", "Vertical A")
        mi_obs.actualizarDeck.assert_called_once()

    def test_evento_vertical_recording_started_notifica(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)
        mi_obs.Notificar = MagicMock()
        mi_obs.actualizarDeck = MagicMock()

        mi_obs.eventoVertical(SimpleNamespace(event_type="recording_started", event_data={}))

        mi_obs.Notificar.assert_called_once_with("obs-grabando-vertival")
        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_grabar_vertical", True)
        mi_obs.actualizarDeck.assert_called_once()

    def test_cambiar_escena_no_conectado_notifica(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        mi_obs.conectado = False
        mi_obs.Notificar = MagicMock()

        mi_obs.cambiarEscena({"escena": "Escena A"})

        mi_obs.Notificar.assert_called_once_with("OBS-No-Encontrado")

    def test_cambiar_escena_conectado_ejecuta_cliente(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        cliente = MagicMock()
        mi_obs.clienteConsultas = cliente
        mi_obs.conectado = True

        mi_obs.cambiarEscena({"escena": "Escena A"})

        cliente.set_current_program_scene.assert_called_once_with("Escena A")
        mi_obs.conectado = False

    def test_cambiar_filtro_conectado_toma_estado_inverso(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        monkeypatch.setattr(modulo_mi_obs, "ObtenerValor", lambda *_args, **_kwargs: True)
        cliente = MagicMock()
        mi_obs.clienteConsultas = cliente
        mi_obs.conectado = True

        mi_obs.cambiarFiltro({"fuente": "Camara", "filtro": "Color"})

        cliente.set_source_filter_enabled.assert_called_once_with("Camara", "Color", False)
        mi_obs.conectado = False

    def test_cambiar_grabacion_no_conectado_notifica(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        mi_obs.Notificar = MagicMock()
        mi_obs.conectado = False

        mi_obs.cambiarGrabacion()

        mi_obs.Notificar.assert_called_once_with("OBS-No-Conectado")

    def test_cambiar_grabacion_conectado_ejecuta_toggle(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        cliente = MagicMock()
        mi_obs.clienteConsultas = cliente
        mi_obs.conectado = True

        mi_obs.cambiarGrabacion()

        cliente.toggle_record.assert_called_once()
        mi_obs.conectado = False

    def test_desconectar_conectado_cierra_clientes_y_limpia(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        salvar_valor = MagicMock()
        monkeypatch.setattr(modulo_mi_obs, "SalvarValor", salvar_valor)

        mi_obs.Notificar = MagicMock()
        mi_obs.LimpiarTemporales = MagicMock()
        mi_obs.actualizarDeck = MagicMock()
        mi_obs.clienteConsultas = MagicMock()
        mi_obs.clienteEvento = MagicMock()
        mi_obs.conectado = True

        mi_obs.desconectar()

        mi_obs.Notificar.assert_called_once_with("OBS-No-Conectado")
        mi_obs.clienteConsultas.disconnect.assert_called_once()
        mi_obs.clienteEvento.disconnect.assert_called_once()
        mi_obs.LimpiarTemporales.assert_called_once()
        salvar_valor.assert_called_once_with(mi_obs.archivoEstado, "obs_conectar", False)
        mi_obs.actualizarDeck.assert_called_once()

    def test_estado_obs_notifica_todos_los_estados(self, monkeypatch):
        modulo_mi_obs = cargar_modulo_mi_obs()
        mi_obs = crear_instancia_segura(monkeypatch, modulo_mi_obs)

        valores = {
            "obs_conectar": True,
            "obs_grabar": False,
            "obs_envivo": True,
            "obs_webcamara": False,
        }
        monkeypatch.setattr(modulo_mi_obs, "ObtenerValor", lambda _a, key: valores.get(key))
        mi_obs.Notificar = MagicMock()

        mi_obs.EstadoOBS({})

        mi_obs.Notificar.assert_any_call("OBS-Conectado")
        mi_obs.Notificar.assert_any_call("OBS-No-Grabando")
        mi_obs.Notificar.assert_any_call("OBS-EnVivo")
        mi_obs.Notificar.assert_any_call("OBS-No-WebCamara")
        assert mi_obs.Notificar.call_count == 4
