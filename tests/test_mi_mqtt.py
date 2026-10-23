from elGarrobo.dispositivos.mimqtt.mi_mqtt import MiMQTT


def test_broker_como_url_o_ip():
    """Una URL mqtt:// se separa en host y puerto; sin puerto en la URL queda el de 'puerto'"""
    assert (lambda m: (m.dispositivo, m.puerto))(MiMQTT({"dispositivo": "mqtt://casa.local:8883"})) == ("casa.local", 8883)
    assert (lambda m: (m.dispositivo, m.puerto))(MiMQTT({"dispositivo": "mqtt://casa.local", "puerto": 1884})) == ("casa.local", 1884)
    assert (lambda m: (m.dispositivo, m.puerto))(MiMQTT({"dispositivo": "192.168.50.200"})) == ("192.168.50.200", 1883)
