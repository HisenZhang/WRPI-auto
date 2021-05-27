# $$\      $$\ $$$$$$$\  $$$$$$$\ $$$$$$\        $$$$$$\  $$\   $$\ $$$$$$$$\  $$$$$$\
# $$ | $\  $$ |$$  __$$\ $$  __$$\\_$$  _|      $$  __$$\ $$ |  $$ |\__$$  __|$$  __$$\
# $$ |$$$\ $$ |$$ |  $$ |$$ |  $$ | $$ |        $$ /  $$ |$$ |  $$ |   $$ |   $$ /  $$ |
# $$ $$ $$\$$ |$$$$$$$  |$$$$$$$  | $$ |        $$$$$$$$ |$$ |  $$ |   $$ |   $$ |  $$ |
# $$$$  _$$$$ |$$  __$$< $$  ____/  $$ |        $$  __$$ |$$ |  $$ |   $$ |   $$ |  $$ |
# $$$  / \$$$ |$$ |  $$ |$$ |       $$ |        $$ |  $$ |$$ |  $$ |   $$ |   $$ |  $$ |
# $$  /   \$$ |$$ |  $$ |$$ |     $$$$$$\       $$ |  $$ |\$$$$$$  |   $$ |    $$$$$$  |
# \__/     \__|\__|  \__|\__|     \______|      \__|  \__| \______/    \__|    \______/

# Author: Hisen Zhang <hisen@hisenz.com>

# MIT LICENSE
# Copyright (c) 2012-2021 Scott Chacon and others

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


from os.path import join
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
# how much lower the audio should be when being surpressed (e.g. during a Station ID)
SURPRESSION_FACTOR = 0.3
# format supported
SOUND_FORMAT = ('.mp3','.wav','.ogg')

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


def fadeOut(chan:mixer.Channel, desired_vol:int=0):
    """Fade out effect

    Args:
        chan (mixer.Channel): the channel affected
        desired_vol (int, optional): the vol after fading. Assumed lower than original. Defaults to 0.
    """
    vol = chan.get_volume()
    for i in range(1, TRANSITION_LENGTH):
        time.sleep(0.001)
        chan.set_volume((TRANSITION_LENGTH-i)/TRANSITION_LENGTH*(vol-desired_vol)+desired_vol)


def fadeIn(chan:mixer.Channel, desired_vol:int=1):
    """Fade in effect

    Args:
        chan (mixer.Channel): the channel affected
        desired_vol (int, optional): the vol after fading. Assumed higher than original. Defaults to 1.
    """
    vol = chan.get_volume()
    for i in range(1, TRANSITION_LENGTH):
        time.sleep(0.001)
        chan.set_volume(i/TRANSITION_LENGTH*(desired_vol-vol)+vol)


def list_sound(t:str)->list:
    """list sound files of the given type

    Args:
        t (str): type of sound

    Returns:
        list: a list of sound files
    """
    return [f for f in listdir(join(lib_base, t)) if f.lower().endswith(SOUND_FORMAT)]

# Audio player


def play_file(f:str, chan:mixer.Channel):
    """Play a sound in a channel.

    Args:
        f (str): path to sound file, i.e. "lib/show/abc.mp3"
        chan (Mixer.Channel): [description]
    """
    try:
        s = mixer.Sound(f)
    except IOError:
        logging.error("Cannot load sound " + f)
    try:
        chan.play(s, fade_ms=TRANSITION_LENGTH)
        logging.info("Playing " + f)
    except:
        logging.error("Cannot play sound " + f)


def play_random(t:str):
    """Play a randomly picked sound from a given type

    Args:
        t (str): type of sound
    """
    try:
        selected = random.choice(list_sound(t))
        play_file(join(lib_base, t, selected), channelMap[t])
    except IndexError:
        logging.error("Empty playlist. Not playing.")

# For play_loop use, global var
cyclic_queue = []


def play_loop(t:str):
    """Loop playing all sounds in that type. Needs to be called every time in the main loop.

    Args:
        t (str): type of sound
    """
    if len(cyclic_queue) == 0:
        cyclic_queue.extend(list_sound(t))
    else:
        if not channelMap[t].get_busy():
            play_file(join(lib_base, t, cyclic_queue[-1]), channelMap[t])
            cyclic_queue.pop()


def play_stationID():
    """Play randomly selected stationID. Lower show volume during station ID.
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
    """Release resources.
    """
    mixer.stop()
    mixer.quit()

# Defining station behavior


def routine():
    """Defining station routine.
    """
    # At startup
    logging.info("WRPI automation started")
    play_stationID()

    # Register schedule
    # schedule.every().hour.at(":00").do(play_stationID) # real business here
    schedule.every().minute.at(":00").do(play_stationID)  # debugging

    # loop
    while True:
        schedule.run_pending()
        play_loop('show')
        time.sleep(1)
        pass

    # t shutdown
    close()
    logging.info("Resourced unloaded. Bye.")


routine()
