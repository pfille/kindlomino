import threading

import socketio
from loguru import logger

sio = socketio.Client()


@sio.event
def connect():
    logger.info("connection established")
    return "connected"


def print_state(status):
    logger.info(f"print state: {status}")

@sio.on("pushState")
def on_push(data):
    global timer
    logger.debug("I received a message!")
    logger.info(data)
    timer = threading.Timer(0.5, print_state, [data["status"]])
    for thread in threading.enumerate():
        if type(thread) == threading.Timer:
            if thread.is_alive():
                thread.cancel()
    timer.start()


@sio.on("*")
def catch_all(event, data):
    logger.debug(event)


@sio.event
def disconnect():
    print("disconnected from server")

sio.connect("http://ztream.local:3000")


def main():
    sio.emit("getState", "")
    sio.wait()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sio.disconnect()
