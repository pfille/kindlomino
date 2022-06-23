import pathlib
import subprocess
import threading
import time
import traceback
from os import path

import py3langid as langid
import yaml
from hyphen import Hyphenator
from hyphen.textwrap2 import fill, wrap
from loguru import logger
from PIL import Image, ImageChops, ImageDraw, ImageFont
from socketIO_client import LoggingNamespace, SocketIO


def simple_wrap(text):
    global max_chars
    global max_chars_per_line
    if len(text) > max_chars:
        text = text[: max_chars - 1]
        text = text[:-3] + "..."
    if len(text) > max_chars_per_line:
        line1 = text[: len(text) // 2]
        line2 = text[len(text) // 2 :]
        if not (line1[-1] == " " or line2[0] == " "):
            line1 = line1 + "-"
        text = "\n".join((line1, line2))
    return text


def smart_wrap(text):
    global hyphenators
    global max_chars_per_line
    estimated_lang = langid.classify(text)[0]
    if estimated_lang in hyphenators.keys() and len(text) > max_chars_per_line:
        text = wrap(
            text, width=max_chars_per_line, use_hyphenator=hyphenators[estimated_lang]
        )
        logger.debug(len(text[1]))
        if len(text) > 2:
            text[1] = text[1].ljust(max_chars_per_line, " ")
            text[1] = text[1][:-3] + "..."
        text = "\n".join((text[0], text[1]))
        logger.debug("estimated lang in dict: " + estimated_lang)
    elif len(text) > max_chars_per_line:
        text = simple_wrap(text)
        logger.debug("estimated lang not in dict: " + estimated_lang)
    return text


def display_data(data):
    global filepath
    global lastpass
    global font
    global separator
    global w_disp, h_disp
    wasplaying = bool(lastpass["status"] == "play")
    isplaying = bool(data["status"] == "play")
    logger.debug(f"wasplaying: {wasplaying}; isplaying: {isplaying}")
    if (data["title"] != lastpass["title"] or (wasplaying != isplaying)) and data[
        "status"
    ] != "stop":
        lastpass = data
        artist = smart_wrap(data["artist"])
        title = smart_wrap(data["title"])
        now_playing = Image.new("L", (w_disp, h_disp), "white")
        draw = ImageDraw.Draw(now_playing)
        w_artist, h_artist = draw.textsize(artist, font=font, stroke_width=0)
        w_title, h_title = draw.textsize(title, font=font, stroke_width=0)
        w_sep, h_sep = draw.textsize(separator, font=font, stroke_width=0)
        draw.text(
            ((w_disp - w_sep) / 2, (h_disp - h_sep) / 2 + 23),
            separator,
            fill=(0),
            font=font,
        )
        draw.text(
            ((w_disp - w_artist) / 2, (h_disp / 4 - h_artist / 2)),
            artist,
            fill=(0),
            spacing=line_spacing,
            align="center",
            font=font,
        )
        draw.text(
            ((w_disp - w_title) / 2, (3 * h_disp / 4 - h_title / 2)),
            title,
            fill=(0),
            spacing=line_spacing,
            align="center",
            font=font,
        )
        now_playing = now_playing.rotate(90, expand=True)
        now_playing_file = path.join(filepath, "images/now_playing.png")
        now_playing.save(now_playing_file)
        try:
            send_image_command = (
                "sshpass -p mario scp "
                + now_playing_file
                + " root@192.168.15.244:/tmp/root/now_playing.png"
            )
            send_image = subprocess.Popen(
                send_image_command.split(),
            )
            send_image.communicate()
            show_image_command = "sshpass -p mario ssh root@192.168.15.244"
            show_image = subprocess.Popen(
                show_image_command.split(),
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
            if data["status"] == "pause":
                logger.debug("display image for pause")
                show_image.stdin.write(
                    "/usr/sbin/eips -v -g /tmp/root/now_playing.png\n"
                )
            else:
                logger.debug("display image for play")
                show_image.stdin.write("/usr/sbin/eips -g /tmp/root/now_playing.png\n")
            show_image.stdin.write("exit\n")
            show_image.stdin.close()
        except Exception:
            traceback.print_exc()
    if data["status"] == "stop":
        logger.debug(f"display image for stop")
        try:
            pause_image_command = "sshpass -p mario ssh root@192.168.15.244"
            pause_image = subprocess.Popen(
                pause_image_command.split(),
                stdin=subprocess.PIPE,
                universal_newlines=True,
            )
            pause_image.stdin.write("/usr/sbin/eips -g /tmp/root/stopped.png\n")
            pause_image.stdin.write("exit\n")
            pause_image.stdin.close()
        except Exception:
            traceback.print_exc()


def on_connect():
    logger.info("connect")
    return "connected"


def on_push_state(*args):
    logger.debug(args[0])
    if "status" in args[0].keys():
        # improve display updates: for multiple quick pushes on status changes
        # by the volumio server the timer of the previous push is cencelled by
        # the next push and only the last one actually achieves to call the
        # func to update the display
        timer = threading.Timer(0.5, display_data, [args[0]])
        for thread in threading.enumerate():
            if type(thread) == threading.Timer:
                if thread.is_alive():
                    thread.cancel()
        timer.start()


# Init some stuff:
filepath = pathlib.Path(__file__).parent.resolve()
logger.debug(filepath)

configfile = path.join(filepath, "config.yaml")
with open(configfile) as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
logger.info("Read Config File")
logger.info(config)

# Init hyphenators that are called as the language estimates
language_dict_codes = {
    "en": "en_US",
    "de": "de_DE",
    "fr": "fr_FR",
    "pt": "pt_BR",
    "es": "es_ES",
}

hyphenators = {}
for lang in language_dict_codes.keys():
    logger.debug(lang, language_dict_codes[lang])
    hyphenators[lang] = Hyphenator(language_dict_codes[lang])
logger.debug(hyphenators)

# Make sure stopped.png is available on the kindle
send_stopped_image_command = (
    "sshpass -p mario scp "
    + path.join(filepath, "images", "stopped.png")
    + " root@192.168.15.244:/tmp/root/stopped.png"
)
logger.debug(send_stopped_image_command.split())
send_stopped_image = subprocess.Popen(
    send_stopped_image_command.split(),
)
send_stopped_image.communicate()

# Init connection to volumio server
servername = config["server"]["name"]
socketIO = SocketIO(servername, 3000)
socketIO.on("connect", on_connect)

# Init display settings
w_disp, h_disp = (config["display"]["width"], config["display"]["height"])
fontsize = config["display"]["fontsize"]
font = ImageFont.truetype(
    path.join(filepath, "fonts/ArbutusSlab-Regular.ttf"), fontsize
)
line_spacing = config["display"]["linespacing"]
max_chars = config["display"]["max_chars"]
max_chars_per_line = config["display"]["max_chars_per_line"]
separator = "*"

lastpass = {
    "artist": "none",
    "title": "none",
    "status": "none",
}


def main():
    while True:
        # connecting to socket
        socketIO.on("pushState", on_push_state)
        # get initial state
        socketIO.emit("getState", "", on_push_state)
        # now wait
        socketIO.wait()
        logger.info("Reconnection needed")
        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        socketIO.disconnect()
        pass
