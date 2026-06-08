import enum
import json
import random
import socket
import struct
import time

from src.generated import (
    activity_message_pb2,
    alert_message_pb2,
    heartrate_message_pb2,
    idle_message_pb2,
    sleep_message_pb2,
)
from src.logger import *
from src.mqtt_client import MQTTclient

# gateway settings
HOST = "0.0.0.0"
PORT = 5000

BUFFER_SIZE = 1024

# drop sensors that haven't sent anything in this many seconds
STALE_TIMEOUT_SECONDS = 60


# message types
class MsgType(enum.IntEnum):
    ACTIVITY = 0x0, "act"
    ALERT = 0x1, "alt"
    HEARTRATE = 0x2, "hrt"
    IDLE = 0x3, "idl"
    SLEEP = 0x4, "slp"

    # don't have a proto counterpart
    REGISTRATION = 0x5, None
    NOT_REGISTERED = 0x6, None

    # python magic to make topic_name available as attribute
    topic_name: str | None

    def __new__(cls, value, topic_name=None):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.topic_name = topic_name
        return obj


# magic, see: https://docs.python.org/3.13/library/struct.html
FMT_ACTIVITY = "<BBB"
FMT_ALERT = "<BB"
FMT_HEARTRATE = "<BB"
FMT_IDLE = "<BffH"
FMT_SLEEP = "<BB"
FMT_REGISTRATION = "<BI"

# create UDP socket
sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1.0)
sock.bind((HOST, PORT))

# mappings
## sensor_id <-> user_id
sensor_user_map: dict[int, int] = {}
## addr (ip, port) <-> sensor_id
addr_sensor_map: dict[tuple[str, int], int] = {}
## sensor_id <-> last-activity timestamp
sensor_last_seen_map: dict[int, float] = {}

# per-user accumulated state (sensor sends deltas, we track totals)
user_state: dict[int, dict] = {}


def on_mapping_message(client, userdata, msg):
    global sensor_user_map
    mapping = json.loads(msg.payload)
    sensor_user_map = {
        int(sensor_id): info["user_id"]
        for sensor_id, info in mapping.get("sensors", {}).items()
    }
    logi(f"Mapping updated: {len(sensor_user_map)} sensor(s)")


client = MQTTclient("broker", 1883, subscriptions=[("management/mappings", 0)])
# we only ever expect to receive mapping updates
client.set_on_message(on_mapping_message)


def get_sensor_id_for_addr(addr) -> int | None:
    key = (addr[0], addr[1])
    return addr_sensor_map.get(key)


def mark_sensor_as_seen(sensor_id: int) -> None:
    sensor_last_seen_map[sensor_id] = time.monotonic()


def cleanup_stale_sensors() -> None:
    now = time.monotonic()
    stale = [
        key
        for key, sensor_id in addr_sensor_map.items()
        if now - sensor_last_seen_map.get(sensor_id, 0) > STALE_TIMEOUT_SECONDS
    ]
    for key in stale:
        sensor_id = addr_sensor_map.pop(key)
        sensor_last_seen_map.pop(sensor_id, None)
        logw(
            f"Removed stale sensor {sensor_id} ({key[0]}:{key[1]}) — no traffic for {STALE_TIMEOUT_SECONDS}s"
        )


def get_user_state(user_id: int) -> dict:
    if user_id not in user_state:
        user_state[user_id] = {"steps": 0}
    return user_state[user_id]


def aggregate(
    msg_type: int, data: bytes, user_id: int, sensor_id: int, addr
) -> object | None:
    try:
        match msg_type:
            case MsgType.ACTIVITY:
                if len(data) < struct.calcsize(FMT_ACTIVITY):
                    loge(f"Short activity frame ({len(data)} B) from {addr}")
                    return None
                _, burnt_cal, activity_val = struct.unpack(FMT_ACTIVITY, data)
                msg = activity_message_pb2.ActivityMessage()
                msg.burnt_calories = burnt_cal
                msg.activity_type = activity_val
                logd(
                    f"Activity | sensor={sensor_id}"
                    f" user={user_id} cal={burnt_cal} type={activity_val}"
                )
                return msg

            case MsgType.HEARTRATE:
                if len(data) < struct.calcsize(FMT_HEARTRATE):
                    loge(f"Short heartrate frame ({len(data)} B) from {addr}")
                    return None
                if random.randint(0, 100) < 10:
                    # we're doing an alert
                    msg = alert_message_pb2.AlertMessage()
                    msg.alert_type = (
                        alert_message_pb2.AlertMessage.AlertType.HEART_ATTACK
                    )
                    encode_and_publish(sensor_id, MsgType.ALERT, msg)
                    logd(f"Alert | sensor={sensor_id} type={msg.alert_type}")
                    return None

                _, heartrate = struct.unpack(FMT_HEARTRATE, data)
                msg = heartrate_message_pb2.HeartrateMessage()
                msg.heartrate = heartrate
                logd(f"Heartrate | sensor={sensor_id} user={user_id} bpm={heartrate}")
                return msg

            case MsgType.IDLE:
                if len(data) < struct.calcsize(FMT_IDLE):
                    loge(f"Short idle frame ({len(data)} B) from {addr}")
                    return None
                if random.randint(0, 100) < 10:
                    # we're doing an alert
                    msg = alert_message_pb2.AlertMessage()
                    msg.alert_type = alert_message_pb2.AlertMessage.AlertType.LOCALIZATION_OUT_OF_BOUNDS
                    encode_and_publish(sensor_id, MsgType.ALERT, msg)
                    logd(f"Alert | sensor={sensor_id} type={msg.alert_type}")
                    return None

                _, longitude, latitude, delta_steps = struct.unpack(FMT_IDLE, data)
                state = get_user_state(user_id)
                state["steps"] += delta_steps
                msg = idle_message_pb2.IdleMessage()
                msg.longitude = longitude
                msg.latitude = latitude
                msg.steps_count = state["steps"]
                logd(
                    f"Idle | sensor={sensor_id}"
                    f" user={user_id}"
                    f" lon={longitude:.4f} lat={latitude:.4f}"
                    f" +{delta_steps} steps (total={state['steps']})"
                )
                return msg

            case MsgType.SLEEP:
                if len(data) < struct.calcsize(FMT_SLEEP):
                    loge(f"Short sleep frame ({len(data)} B) from {addr}")
                    return None
                _, sleep_val = struct.unpack(FMT_SLEEP, data)
                msg = sleep_message_pb2.SleepMessage()
                msg.sleep_type = sleep_val
                logd(f"Sleep | sensor={sensor_id} user={user_id} type={sleep_val}")
                return msg

            case _:
                logw(f"Unknown message type {msg_type:#04x} from {addr}")
                return None

    except struct.error as e:
        loge(f"Unpack failed for type={msg_type:#04x} from {addr}: {e}")
        return None


def encode_and_publish(sensor_id: int, msg_type: int, message) -> None:
    type_name = MsgType(msg_type).topic_name
    user_id = sensor_user_map.get(sensor_id)
    topic = f"{type_name}/{user_id}/{sensor_id}"
    client.publish(topic, message.SerializeToString())


def handle_data(data: bytes, addr) -> None:
    if len(data) < 1:
        loge(f"Dropped empty datagram from {addr}")
        return

    msg_type = data[0]

    # registration
    if msg_type == MsgType.REGISTRATION:
        if len(data) < struct.calcsize(FMT_REGISTRATION):
            loge(f"Short registration frame ({len(data)} B) from {addr}")
            return
        _, sensor_id = struct.unpack(FMT_REGISTRATION, data)
        if sensor_id not in sensor_user_map:
            logw(
                f"Rejected registration from unknown sensor {sensor_id} ({addr[0]}:{addr[1]})"
            )
            return
        key = (addr[0], addr[1])
        old = addr_sensor_map.get(key)
        addr_sensor_map[key] = sensor_id
        mark_sensor_as_seen(sensor_id)
        if old is not None and old != sensor_id:
            logi(f"Re-registered {addr[0]}:{addr[1]} sensor {old} → {sensor_id}")
        else:
            logi(f"Registered sensor {sensor_id} at {addr[0]}:{addr[1]}")
        return

    sensor_id = get_sensor_id_for_addr(addr)
    if sensor_id is None:
        logw(f"Unregistered sender {addr[0]}:{addr[1]} — sending response")
        sock.sendto(bytes([MsgType.NOT_REGISTERED]), addr)
        return

    mark_sensor_as_seen(sensor_id)
    user_id = sensor_user_map.get(sensor_id)

    message = aggregate(msg_type, data, user_id, sensor_id, addr)
    if message is not None:
        encode_and_publish(sensor_id, msg_type, message)


# TODO: use network byte-order


if __name__ == "__main__":
    logi("Gateway started")
    last_cleanup = time.monotonic()

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            logd(f"Received {len(data)} bytes from {addr}")
        except socket.timeout:
            # no data arrived, move to cleanup
            pass
        except Exception as e:
            loge(f"Socket error: {e}")
            continue
        else:
            handle_data(data, addr)

        # run cleanup every ~10 seconds
        now = time.monotonic()
        if now - last_cleanup > 10:
            cleanup_stale_sensors()
            last_cleanup = now
