import datetime
import logging
import threading
import time
from os.path import join
import random as rnd

from pygame import mixer

from .audio import virtualMixerWrapper, effect, sound
from .config import LIB_BASE, TRANSITION_LENGTH, SURPRESSION_FACTOR
from .util import fsUtil


class control:
    def __init__(self, m: virtualMixerWrapper) -> None:
        self.mixer = m.mixer
        self.channelMap = m.channelMap
        self.channelLastPlayed = m.channelLastPlayed
        self.cyclic_queue = []  # For play_loop use
        pass

    def play_file(self, s: sound, chan: mixer.Channel):
        """Play a sound in a channel. This is a low level function.

        Args:
            f (str): path to sound file, i.e. "lib/show/abc.mp3"
            chan (Mixer.Channel): [description]
        """
        try:
            chan.play(s.data, fade_ms=TRANSITION_LENGTH)
            logging.info("Playing \"" + s.path + "\" Length " + s.strDuration())
        except:
            logging.error("Cannot play sound " + s.path)

    def random(self, t: str):
        """Play a randomly picked sound from a given type

        Args:
            t (str): type of sound
        """
        try:
            selected = sound(rnd.choice(fsUtil.list_sound(t)))
            self.play_file(selected, self.channelMap[t])
            self.channelLastPlayed[t] = selected
        except IndexError:
            logging.error("Empty playlist. Not playing.")

    def loop(self, t: str):
        """Loop playing all sounds in that type. Needs to be called every time in the main loop.

        Args:
            t (str): type of sound
        """
        if len(self.cyclic_queue) == 0:
            self.cyclic_queue.extend([sound(f) for f in fsUtil.list_sound(t)])
            time.sleep(1)
        else:
            if not self.channelMap[t].get_busy():
                s = self.cyclic_queue[0]
                self.play_file(s, self.channelMap[t])
                self.channelLastPlayed[t] = s
                self.cyclic_queue.remove(self.cyclic_queue[0])

    def shiftPlayList(self, idx, offset):
        target = idx + offset
        target = max(target, 0)
        target = min(target, len(self.cyclic_queue)-1)
        self.cyclic_queue[target], self.cyclic_queue[idx] = self.cyclic_queue[idx], self.cyclic_queue[target]

    def stationID(self):
        """Play randomly selected stationID. Lower show volume during station ID.
        """
        try:
            vol = self.channelMap['show'].get_volume()
            effect.fadeOut(self.channelMap['show'], SURPRESSION_FACTOR*vol)
            self.random('stationID')
            while self.channelMap['stationID'].get_busy():
                time.sleep(1)
            effect.fadeIn(self.channelMap['show'], vol)
            logging.info("Station ID sent.")
        except Exception as e:
            logging.critical("Fail to sent station ID: " + str(e))
        pass
