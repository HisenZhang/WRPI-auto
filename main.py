from os.path import isfile, join
from os import listdir
from pygame import mixer
import schedule
import time
import random
import logging

# Configs

# number of channels in virtual mixer. 48 is more than sufficient.
NUM_CHANNEL = 48
# transition time in ms.
TRANSITION_LENGTH = 1000    
# how much lower the audio should be when being surpressed (e.g. during Station ID)
SURPRESSION_FACTOR = 0.3

lib_base = 'lib'

# Logging

LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(message)s"
logFormatter = logging.Formatter(LOG_FORMAT)
rootLogger = logging.getLogger()
rootLogger.level = logging.INFO

fileHandler = logging.FileHandler("WRPI.log")
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

# Initialize virtual mixer

mixer.init()
mixer.set_num_channels(NUM_CHANNEL)
mixer.music.set_volume(1)

# Define channels

channelMap = {
    "master": mixer.music,
    "stationID": mixer.Channel(0),
    "show": mixer.Channel(1),
    "fill": mixer.Channel(2),
    "PSA": mixer.Channel(3),
}

# Utilities


def fadeOut(chan, v=0):
    vol = chan.get_volume()
    for i in range(1, TRANSITION_LENGTH):
        time.sleep(0.001)
        chan.set_volume((TRANSITION_LENGTH-i)/TRANSITION_LENGTH*(vol-v)+v)


def fadeIn(chan, v=1):
    vol = chan.get_volume()
    for i in range(1, TRANSITION_LENGTH):
        time.sleep(0.001)
        chan.set_volume(i/TRANSITION_LENGTH*(v-vol)+vol)


def list_dir(t):
    p = join(lib_base, t)
    return [f for f in listdir(p) if isfile(join(p, f))]

# Audio player


def play_file(f, chan):
    try:
        s = mixer.Sound(f)
    except:
        logging.error("Cannot load sound " + f)
    try:
        chan.play(s, fade_ms=TRANSITION_LENGTH)
        logging.info("Playing " + f)
    except:
        logging.error("Cannot play sound " + f)


def play_random(t):
    selected = random.choice(list_dir(t))
    play_file(join(lib_base, t, selected), channelMap[t])


cyclic_queue = []


def play_loop(t):
    if len(cyclic_queue) == 0:
        cyclic_queue.extend(list_dir(t))
    else:
        if not channelMap[t].get_busy():
            play_file(join(lib_base, t, cyclic_queue[-1]), channelMap[t])
            cyclic_queue.pop()


def play_stationID():
    """Lower show volume during station ID
    """
    vol = channelMap['show'].get_volume()
    fadeOut(channelMap['show'], SURPRESSION_FACTOR*vol)
    play_random('stationID')
    while channelMap['stationID'].get_busy():
        time.sleep(.1)
    fadeIn(channelMap['show'], vol)
    logging.info("Station ID announced")
    pass


def close():
    mixer.stop()
    mixer.quit()

# Defining station behavior

def routine():
    # startup
    logging.info("WRPI automation started")
    play_stationID()

    # schedule
    # schedule.every().hour.at(":00").do(play_stationID)
    schedule.every().minute.at(":00").do(play_stationID)

    # loop
    while True:
        schedule.run_pending()
        play_loop('show')
        time.sleep(1)
        pass

    # shutdown
    close()
    logging.info("Resourced unloaded. Bye.")


routine()
