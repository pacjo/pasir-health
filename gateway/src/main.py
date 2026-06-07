import enum
import json
import socket
import struct
import time

from src.generated import (
    activity_message_pb2,
    heartbeat_message_pb2,
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
    HEARTBEAT = 0x0
    IDLE = 0x1
    ACTIVITY = 0x2
    SLEEP = 0x3
    REGISTRATION = 0x4
    NOT_REGISTERED = 0x5


# magic, see: https://docs.python.org/3.13/library/struct.html
FMT_REGISTRATION = "<BI"

FMT_HEARTBEAT = "<BB"
FMT_IDLE = "<BddH"
FMT_ACTIVITY = "<BBB"
FMT_SLEEP = "<BB"

# short topic segment per message type (int keys match the wire byte) - TODO: merge with MsgType
TYPE_NAMES: dict[int, str] = {
    MsgType.HEARTBEAT: "hr",
    MsgType.IDLE: "idle",
    MsgType.ACTIVITY: "act",
    MsgType.SLEEP: "slp",
}

# create UDP socket
sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

# mappings
## sensor_id <-> user_id
sensor_user_map: dict[int, int] = {}
## addr (ip, port) <-> sensor_id
addr_sensor_map: dict[tuple[str, int], int] = {}
## sensor_id <-> last-activity timestamp
sensor_last_seen_map: dict[int, float] = {}


def on_mapping_message(client, userdata, msg):
    global sensor_user_map
    mapping = json.loads(msg.payload)
    sensor_user_map = {
        int(sensor_id): info["user_id"]
        for sensor_id, info in mapping.get("sensors", {}).items()
    }
    logi(f"Mapping updated: {len(sensor_user_map)} sensor(s)")


client = MQTTclient("broker", 1883, subscriptions=[("mappings/config", 0)])
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


def publish_proto(sensor_id: int, msg_type: int, payload: bytes) -> None:
    type_name = TYPE_NAMES.get(msg_type)
    user_id = sensor_user_map.get(sensor_id)
    topic = f"{type_name}/{user_id}/{sensor_id}"

    client.publish(topic, payload)


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

    # actual data
    message = None
    try:
        match msg_type:
            case MsgType.HEARTBEAT:
                if len(data) < struct.calcsize(FMT_HEARTBEAT):
                    loge(f"Short heartbeat frame ({len(data)} B) from {addr}")
                    return
                _, heartbeat = struct.unpack(FMT_HEARTBEAT, data)
                message = heartbeat_message_pb2.HeartbeatMessage()
                message.heartbeat = heartbeat
                logd(
                    f"Heartbeat | sensor={sensor_id}"
                    f" user={sensor_user_map.get(sensor_id, '?')} bpm={heartbeat}"
                )

            case MsgType.IDLE:
                if len(data) < struct.calcsize(FMT_IDLE):
                    loge(f"Short idle frame ({len(data)} B) from {addr}")
                    return
                _, longitude, latitude, steps = struct.unpack(FMT_IDLE, data)
                message = idle_message_pb2.IdleMessage()
                message.longitude = longitude
                message.latitude = latitude
                message.steps_count = steps
                logd(
                    f"Idle | sensor={sensor_id}"
                    f" user={sensor_user_map.get(sensor_id, '?')}"
                    f" lon={longitude:.4f} lat={latitude:.4f} steps={steps}"
                )

            case MsgType.ACTIVITY:
                if len(data) < struct.calcsize(FMT_ACTIVITY):
                    loge(f"Short activity frame ({len(data)} B) from {addr}")
                    return
                _, burnt_cal, activity_val = struct.unpack(FMT_ACTIVITY, data)
                message = activity_message_pb2.ActivityMessage()
                message.burnt_calories = burnt_cal
                # Arduino activity_type enum values match ActivityType proto enum:
                #   SWIMMING=0, RUNNING=1, TENNIS=2, GOTHIC=3
                message.activity_type = activity_val
                logd(
                    f"Activity | sensor={sensor_id}"
                    f" user={sensor_user_map.get(sensor_id, '?')}"
                    f" cal={burnt_cal} type={activity_val}"
                )

            case MsgType.SLEEP:
                if len(data) < struct.calcsize(FMT_SLEEP):
                    loge(f"Short sleep frame ({len(data)} B) from {addr}")
                    return
                _, sleep_val = struct.unpack(FMT_SLEEP, data)
                message = sleep_message_pb2.SleepMessage()
                # Arduino sleep_type enum values match SleepMessage.sleep_type proto enum:
                #   AWAKE=0, LIGHT_SLEEP=1, DEEP_SLEEP=2, REM=3
                message.sleep_type = sleep_val
                logd(
                    f"Sleep | sensor={sensor_id}"
                    f" user={sensor_user_map.get(sensor_id, '?')}"
                    f" type={sleep_val}"
                )

            case _:
                logw(f"Unknown message type {msg_type:#04x} from {addr}")
                return

    except struct.error as e:
        loge(f"Unpack failed for type={msg_type:#04x} from {addr}: {e}")
        return

    else:
        publish_proto(sensor_id, msg_type, message.SerializeToString())


# TODO: use network byte-order


if __name__ == "__main__":
    logi("Gateway started")
    last_cleanup = time.monotonic()

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            logd(f"Received {len(data)} bytes from {addr}")
        except Exception as e:
            loge(f"Socket error: {e}")
            continue

        handle_data(data, addr)

        # run cleanup every ~10 seconds
        now = time.monotonic()
        if now - last_cleanup > 10:
            cleanup_stale_sensors()
            last_cleanup = now
