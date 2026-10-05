import sys

from elGarrobo.accionesOOP.accionMQTT import accionMQTT

modulo = sys.modules[accionMQTT.__module__]


class clienteFalso:
    def __init__(self, *args):
        self.publicados = []

    def username_pw_set(self, usuario, contraseña):
        pass

    def connect_async(self, servidor, puerto):
        pass

    def max_queued_messages_set(self, cola):
        self.cola = cola

    def loop_start(self):
        pass

    def publish(self, topic, mensaje, qos=0):
        self.publicados.append((topic, mensaje))


def enviar(servidor, puerto, mensaje):
    acción = accionMQTT()
    acción.configurar({"mensaje": mensaje, "topic": "t", "servidor": servidor, "puerto": puerto})
    acción.ejecutar()


def test_reusa_conexion_con_mismos_datos(monkeypatch):
    monkeypatch.setattr(modulo.mqtt, "Client", clienteFalso)
    monkeypatch.setattr(accionMQTT, "clientes", {})
    monkeypatch.setattr(modulo, "ObtenerValor", lambda archivo, clave: None)

    enviar("a", 1, "uno")
    enviar("a", 1, {"dos": 2})
    enviar("b", 1, "tres")

    assert len(accionMQTT.clientes) == 2
    assert accionMQTT.clientes[("a", 1, None, None)].publicados == [("t", "uno"), ("t", '{"dos": 2}')]


def test_cola_desde_data_mqtt(monkeypatch):
    monkeypatch.setattr(modulo.mqtt, "Client", clienteFalso)
    monkeypatch.setattr(accionMQTT, "clientes", {})
    monkeypatch.setattr(modulo, "ObtenerValor", lambda archivo, clave: 5 if clave == "cola" else None)

    enviar("a", 1, "uno")

    assert accionMQTT.clientes[("a", 1, None, None)].cola == 5
