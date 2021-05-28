import time
from pygame import mixer
from os.path import join
from os import listdir
import logging

import random as rnd

from .config import *


class effect:
    def fadeOut(chan: mixer.Channel, desired_vol: int = 0):
        """Fade out effect

        Args:
            chan (mixer.Channel): the channel affected
            desired_vol (int, optional): the vol after fading. Assumed lower than original. Defaults to 0.
        """
        vol = chan.get_volume()
        for i in range(1, TRANSITION_LENGTH):
            time.sleep(1/TRANSITION_LENGTH)
            chan.set_volume((TRANSITION_LENGTH-i) /
                            TRANSITION_LENGTH*(vol-desired_vol)+desired_vol)

    def fadeIn(chan: mixer.Channel, desired_vol: int = 1):
        """Fade in effect

        Args:
            chan (mixer.Channel): the channel affected
            desired_vol (int, optional): the vol after fading. Assumed higher than original. Defaults to 1.
        """
        vol = chan.get_volume()
        for i in range(1, TRANSITION_LENGTH):
            time.sleep(1/TRANSITION_LENGTH)
            chan.set_volume(i/TRANSITION_LENGTH*(desired_vol-vol)+vol)

class virtualMixerWrapper:
    def __init__(self) -> None:
        self.mixer = mixer
        self.mixer.init()
        self.mixer.set_num_channels(NUM_CHANNEL)
        self.mixer.music.set_volume(1)
        self.channelMap = {
            "master": mixer.music,
            "stationID": mixer.Channel(0),
            "show": mixer.Channel(1),
            "fill": mixer.Channel(2),
            "PSA": mixer.Channel(3),
        }
        self.channelLastPlayed = {}

    def digest(self):
        """What's playing in each channel.
        """
        stringBuffer = ['Mixer digest:']
        for chan, sound in self.channelLastPlayed.items():
            if self.channelMap[chan].get_busy():
                stringBuffer.append('[')
                stringBuffer.append(chan)
                stringBuffer.append(']')
                stringBuffer.append('-')
                stringBuffer.append(sound)
        logging.info(' '.join(stringBuffer))



class util:
    def list_sound(t: str) -> list:
        """list sound files of the given type

        Args:
            t (str): type of sound

        Returns:
            list: a list of sound files
        """
        return [f for f in listdir(join(lib_base, t)) if f.lower().endswith(SOUND_FORMAT)]

class control:
    def __init__(self, m:virtualMixerWrapper) -> None:
        self.mixer = m.mixer
        self.channelMap = m.channelMap
        self.channelLastPlayed = m.channelLastPlayed            
        self.cyclic_queue = [] # For play_loop use
        pass

    def play_file(self, f: str, chan: mixer.Channel):
        """Play a sound in a channel. This is a low level function.

        Args:
            f (str): path to sound file, i.e. "lib/show/abc.mp3"
            chan (Mixer.Channel): [description]
        """
        try:
            s = self.mixer.Sound(f)
        except IOError:
            logging.error("Cannot load sound " + f)
        try:
            chan.play(s, fade_ms=TRANSITION_LENGTH)
            logging.info("Playing " + f)
        except:
            logging.error("Cannot play sound " + f)


    def random(self, t: str):
        """Play a randomly picked sound from a given type

        Args:
            t (str): type of sound
        """
        try:
            selected = rnd.choice(util.list_sound(t))
            file = join(lib_base, t, selected)
            self.play_file(file, self.channelMap[t])
            self.channelLastPlayed[t] = file
        except IndexError:
            logging.error("Empty playlist. Not playing.")



    def loop(self, t: str):
        """Loop playing all sounds in that type. Needs to be called every time in the main loop.

        Args:
            t (str): type of sound
        """
        if len(self.cyclic_queue) == 0:
            self.cyclic_queue.extend(util.list_sound(t))
        else:
            if not self.channelMap[t].get_busy():
                file = join(lib_base, t, self.cyclic_queue[-1])
                self.play_file(file, self.channelMap[t])
                self.channelLastPlayed[t] = file
                self.cyclic_queue.pop()
    
    def stationID(self):
        """Play randomly selected stationID. Lower show volume during station ID.
        """
        vol = self.channelMap['show'].get_volume()
        effect.fadeOut(self.channelMap['show'], SURPRESSION_FACTOR*vol)
        self.random('stationID')
        while self.channelMap['stationID'].get_busy():
            time.sleep(.1)
        effect.fadeIn(self.channelMap['show'], vol)
        logging.info("Station ID sent.")
        pass