import random

from paho.mqtt import client as mqtt_client

from src.logger import *


class MQTTclient:
    def __init__(
        self, ip: str, port: int, subscriptions: list[tuple[str, int]] | None = None
    ):
        client_id = f"publish-{random.randint(0, 1000)}"

        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                logi("Connected to MQTT Broker!")
                if subscriptions:
                    for topic, qos in subscriptions:
                        client.subscribe(topic, qos)
                        logd(f"Subscribed to `{topic}`")
            else:
                loge(f"Failed to connect, return code {reason_code}")

        self.client = mqtt_client.Client(
            client_id=client_id,
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        )
        # client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        self.client.connect(ip, port)
        self.client.loop_start()

    def set_on_message(self, callback):
        self.client.on_message = callback

    def publish(self, topic: str, msg: str | bytes):
        result = self.client.publish(topic, msg)
        status = result[0]
        if status == 0:
            logd(f"Sent to topic `{topic}`")
        else:
            loge(f"Failed to send message to topic {topic}")
