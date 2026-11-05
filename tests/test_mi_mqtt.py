from elGarrobo.dispositivos.mimqtt.mi_mqtt import MiMQTT


def test_broker_como_url_o_ip():
    """Una URL mqtt:// se separa en host y puerto; sin puerto en la URL queda el de 'puerto'"""
    assert (lambda m: (m.dispositivo, m.puerto))(MiMQTT({"dispositivo": "mqtt://casa.local:8883"})) == ("casa.local", 8883)
    assert (lambda m: (m.dispositivo, m.puerto))(MiMQTT({"dispositivo": "mqtt://casa.local", "puerto": 1884})) == ("casa.local", 1884)
    assert (lambda m: (m.dispositivo, m.puerto))(MiMQTT({"dispositivo": "192.168.50.200"})) == ("192.168.50.200", 1883)


def test_suscribe_titulo_agregado_despues(monkeypatch):
    """Una tecla con título MQTT agregada después de arrancar (GUI, folder o página) se suscribe al actualizar"""
    from elGarrobo.dispositivos.dispositivo import dispositivo
    from elGarrobo.elGarrobo import elGarrobo

    mqtt = MiMQTT({"dispositivo": "192.168.50.200"})
    monkeypatch.setattr(MiMQTT, "listaTopicTitulo", [])
    deck = dispositivo({})
    deck.tipo, deck.listaAcciones = "deck", []
    garrobo = elGarrobo.__new__(elGarrobo)
    garrobo.listaDispositivos = [mqtt, deck]
    monkeypatch.setattr(dispositivo, "accionesCambiadas", garrobo.actualizarTitulosMQTT)

    deck.listaAcciones.append({"key": 43, "titulo_opciones": {"mqtt": "estado_octoprint/maomao/tiempo"}})
    deck.actualizar()
    assert mqtt.listaTopicTitulo == ["estado_octoprint/maomao/tiempo"]
