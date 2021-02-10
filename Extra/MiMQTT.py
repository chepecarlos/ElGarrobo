import paho.mqtt.client as mqtt
from Extra.FuncionesProyecto import ObtenerDato


def EnviarMQTTSimple(Topic, Mensaje):
    Usuario = ObtenerDato("/Data/MQTT.json", "Usuario")
    Contrasenna = ObtenerDato("/Data/MQTT.json", "Contrasenna")
    MiMQTTSimple = mqtt.Client()
    MiMQTTSimple.username_pw_set(Usuario,  Contrasenna)
    MiMQTTSimple.connect("public.cloud.shiftr.io", 1883)
    MiMQTTSimple.publish(Topic, Mensaje)
