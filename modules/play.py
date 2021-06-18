import datetime
import logging
import threading
import time
from os.path import join
import random as rnd

from pygame import mixer
import pygame

from .audio import virtualMixerWrapper, effect, sound
from .config import LIB_BASE, TRANSITION_LENGTH, SURPRESSION_FACTOR
from .util import fsUtil


class control:
    def __init__(self, m: virtualMixerWrapper) -> None:
        self.mixer = m.mixer
        self.mixerLock = m.lock
        self.channelMap = m.channelMap
        self.channelLastPlayed = m.channelLastPlayed
        self.queue = []  # For play_loop use
        self.index = 0
        self.mode = 'loop'
        pass

    def play_file(self, s: sound, chan: mixer.Channel) -> float:
        """Play a sound in a channel. This is a low level function.

        Args:
            f (str): path to sound file, i.e. "lib/show/abc.mp3"
            chan (Mixer.Channel): channel to play in

        Returns:
            float: duration of the sound file
        """
        try:
            chan.play(s.getData(), fade_ms=TRANSITION_LENGTH)
            logging.info("Playing \"" + s.path +
                         "\" Length " + s.strDuration())
            return s.getDuration()
        except pygame.error as e:
            logging.error("pygame error: " + str(e))
        except Exception as e:
            logging.error("Cannot play sound " + s.path + ": " + str(e))

    def random(self, t: str):
        """Play a randomly picked sound from a given type

        Args:
            t (str): type of sound
        """
        try:
            selected = sound(rnd.choice(fsUtil.list_sound(t)))
            duration = self.play_file(selected, self.channelMap[t])
            self.channelLastPlayed[t] = selected
            return duration
        except IndexError:
            logging.error("Empty playlist. Not playing.")

    def _discoverSound(self, t: str):
        return [sound(f) for f in fsUtil.list_sound(t)]

    def setMode(self, m: str):
        assert m in ('loop', 'shuffle', 'single', 'once')
        self.mode = m

    def pullPlayList(self, t: str):
        self.queue.extend(self._discoverSound(t))

    def play(self, t: str):
        if len(self.queue) == 0:
            self.pullPlayList(t)
            self.index = -1
        else:
            if not self.channelMap[t].get_busy():  # previous sound is over                
                self.channelLastPlayed[t] = ''
                self.queue[self.index].unloadData()
                # update index
                if self.mode == 'shuffle':
                    self.index = rnd.randint(0, len(self.queue)-1)
                elif self.mode in ('loop', 'once'):
                    if self.index == len(self.queue)-1:  # last one, back to top
                        self.index = 0
                        if self.mode == 'once':
                            self.mixer.fadeout(TRANSITION_LENGTH)
                    else:
                        self.index += 1
                elif self.mode == 'single':
                    pass  # do nothing
                logging.debug("Next play index {}, sound {}".format(
                    self.index, self.queue[self.index].path))
                s = self.queue[self.index]
                self.play_file(s, self.channelMap[t])
                self.channelLastPlayed[t] = s
                if (len(self.queue) > 0) and self.mode in ('loop', 'once'):
                    self.preloadNextSound(1)
        pass

    def preloadNextSound(self,lookahead=1):
        idx = self.index
        for _ in range(lookahead):
            i = (idx+1)%len(self.queue)
            self.queue[i].getData()
            idx += 1

    def next(self):
        # TODO multichannel playlist
        self.mixer.fadeout(TRANSITION_LENGTH)

    def appendPlayList(self, t: str = 'show'):

        # assume all media in lib normalized.
        l = self._discoverSound(t)
        for s in l:
            if s not in self.queue:
                self.queue.append(s)

    def shiftPlayList(self, idx, offset):
        target = idx + offset
        target = max(target, 0)
        target = min(target, len(self.queue)-1)
        self.queue[target], self.queue[idx] = self.queue[idx], self.queue[target]

    def removeFromPlayList(self, idx):
        del self.queue[idx]

    def stationID(self):
        """Play randomly selected stationID. Lower show volume during station ID.
        """
        with self.mixerLock:
            vol = self.channelMap['show'].get_volume()
            effect.fadeOut(self.channelMap['show'], SURPRESSION_FACTOR*vol)
            duration = self.random('stationID')
            if duration > 8:
                effect.fadeOut(self.channelMap['show'], 0)
                self.channelMap['show'].pause()
            while self.channelMap['stationID'].get_busy():
                time.sleep(1)
            if duration > 8:
                self.channelMap['show'].unpause()
            effect.fadeIn(self.channelMap['show'], vol)
            logging.info("Station ID sent.")
            self.channelLastPlayed['stationID'] = None
