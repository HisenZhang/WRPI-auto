import logging
import time
from os.path import join
import random as rnd

from pygame import mixer

from .audio import virtualMixerWrapper, effect
from .config import *
from .util import fsUtil


class control:
    def __init__(self, m: virtualMixerWrapper) -> None:
        self.mixer = m.mixer
        self.channelMap = m.channelMap
        self.channelLastPlayed = m.channelLastPlayed
        self.cyclic_queue = []  # For play_loop use
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
            selected = rnd.choice(fsUtil.list_sound(t))
            file = join(LIB_BASE, t, selected)
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
            self.cyclic_queue.extend(fsUtil.list_sound(t))
            time.sleep(1)
        else:
            if not self.channelMap[t].get_busy():
                file = join(LIB_BASE, t, self.cyclic_queue[-1])
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
            time.sleep(1)
        effect.fadeIn(self.channelMap['show'], vol)
        logging.info("Station ID sent.")
        pass
