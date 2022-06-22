from time import sleep
import socketio
from loguru import logger
from datetime import datetime, timedelta

sio = socketio.Client()

@sio.event
def connect():
    logger.info('connection established')
    return "connected"

def print_img(data):
    logger.info(f"print img for: {data['status']}")

@sio.on("pushState")
def on_push(data):
    global lastpass
    logger.debug('I received a message!')
    logger.info(data)
    # time_diff_calls = datetime.now() - lastpass["lastcall"]
    # if "status" in data.keys() and time_diff_calls > timedelta(milliseconds=1500):
    #     sleep(1)
    #     lastpass = data
    #     lastpass["lastcall"] = datetime.now()
    #     lastpass["ready_to_print"] = True

    # if lastpass["ready_to_print"]:
    #     print_img(data)
    #     lastpass["ready_to_print"] = False
    # else:
    #     sio.emit("getState")

@sio.on('*')
def catch_all(event, data):
    logger.debug(event)

@sio.event
def disconnect():
    print('disconnected from server')

sio.connect('http://ztream.local:3000')

lastpass = {
    "artist": "none",
    "title": "none",
    "status": "none",
    "lastcall": datetime.now(),
    "ready_to_print": False,
}

def main():
    sio.emit("getState", "")
    sio.wait()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sio.disconnect()