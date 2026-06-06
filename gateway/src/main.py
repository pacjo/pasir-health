import socket

from .logger import *

HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 1024

# create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))


def handle_data(data: bytes, addr) -> None:
    return  # TODO: implement


if __name__ == "__main__":
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            logd(f"Received data from {addr}: {data.decode()}")
        except Exception as e:
            loge(f"Error: {e}")
        else:
            handle_data(data, addr)
