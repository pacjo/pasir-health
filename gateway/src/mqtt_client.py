import random
import time

from paho.mqtt import client as mqtt_client


class MQTTclient:
    def __init__(self, ip: str, port: int):
        client_id = f'publish-{random.randint(0, 1000)}'

        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code == 0:
                print("Connected to MQTT Broker!")
            else:
                print(f"Failed to connect, return code {reason_code}")

        self.client = mqtt_client.Client(
            client_id=client_id,
            callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
        )
        # client.username_pw_set(username, password)
        self.client.on_connect = on_connect
        self.client.connect(ip, port)


    def publish(self, topic: str, msg: str):
        result = self.client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Sent `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")