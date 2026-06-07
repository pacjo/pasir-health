import enum
import socket
import struct

import paho

from src.generated import (
    activity_message_pb2,
    heartbeat_message_pb2,
    idle_message_pb2,
    sleep_message_pb2,
)
from src.logger import *

# gateway settings
HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 1024


# message types
class MsgType(enum.IntEnum):
    HEARTBEAT = 0x0
    IDLE = 0x1
    ACTIVITY = 0x2
    SLEEP = 0x3


# magic, see: https://docs.python.org/3.13/library/struct.html
FMT_HEARTBEAT = "<BHB"
FMT_IDLE = "<BHddH"
FMT_ACTIVITY = "<BHBB"
FMT_SLEEP = "<BHB"

# create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

# TODO: use network byte-order


def handle_data(data: bytes, addr) -> None:
    if len(data) < 1:
        loge(f"Dropped empty datagram from {addr}")
        return

    msg_type = data[0]

    try:
        match msg_type:
            case MsgType.HEARTBEAT:
                if len(data) < struct.calcsize(FMT_HEARTBEAT):
                    loge(f"Short heartbeat frame ({len(data)} B) from {addr}")
                    return
                _, user_id, heartbeat = struct.unpack(FMT_HEARTBEAT, data)
                message = heartbeat_message_pb2.HeartbeatMessage()
                message.heartbeat = heartbeat
                logd(f"Heartbeat | user={user_id} bpm={heartbeat}")

            case MsgType.IDLE:
                if len(data) < struct.calcsize(FMT_IDLE):
                    loge(f"Short idle frame ({len(data)} B) from {addr}")
                    return
                _, user_id, longitude, latitude, steps = struct.unpack(FMT_IDLE, data)
                message = idle_message_pb2.IdleMessage()
                message.longitude = longitude
                message.latitude = latitude
                message.stepsCount = steps
                logd(
                    f"Idle | user={user_id} lon={longitude:.4f} lat={latitude:.4f} steps={steps}"
                )

            case MsgType.ACTIVITY:
                if len(data) < struct.calcsize(FMT_ACTIVITY):
                    loge(f"Short activity frame ({len(data)} B) from {addr}")
                    return
                _, user_id, burnt_cal, activity_val = struct.unpack(FMT_ACTIVITY, data)
                message = activity_message_pb2.ActivityMessage()
                message.burntCalories = burnt_cal
                # Arduino activity_type enum values match ActivityType proto enum:
                #   SWIMMING=0, RUNNING=1, TENNIS=2, GOTHIC=3
                message.activityType = activity_val
                logd(f"Activity | user={user_id} cal={burnt_cal} type={activity_val}")

            case MsgType.SLEEP:
                if len(data) < struct.calcsize(FMT_SLEEP):
                    loge(f"Short sleep frame ({len(data)} B) from {addr}")
                    return
                _, user_id, sleep_val = struct.unpack(FMT_SLEEP, data)
                message = sleep_message_pb2.SleepMessage()
                # Arduino sleep_type enum values match SleepMessage.sleep_type proto enum:
                #   AWAKE=0, LIGHT_SLEEP=1, DEEP_SLEEP=2, REM=3
                message.sleepType = sleep_val
                logd(f"Sleep | user={user_id} type={sleep_val}")

            case _:
                logw(f"Unknown message type {msg_type:#04x} from {addr}")
                return

    except struct.error as e:
        loge(f"Unpack failed for type={msg_type:#04x} from {addr}: {e}")
        return

    else:
        paho.mqtt.publish.single(
            "test", message, hostname="mqtt.pasir.studia.pacjo.ovh"
        )


if __name__ == "__main__":
    logi("Gateway started")
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            logd(f"Received {len(data)} bytes from {addr}")
        except Exception as e:
            loge(f"Socket error: {e}")
        else:
            handle_data(data, addr)
