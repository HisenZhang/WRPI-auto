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
        self.queue = []  # For play_loop use
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
            logging.info("Playing \"" + s.path + "\" Length " + s.strDuration())
            return s.getDuration()
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
    
    def _discoverSound(self, t :str):
        return [sound(f) for f in fsUtil.list_sound(t)]

    def setMode(self,m:str):
        self.mode = m

    def play(self, t:str):
        if len(self.queue) == 0:
            self.queue.extend(self._discoverSound(t))
            if self.mode == 'shuffle':
                rnd.shuffle(self.queue)
        else:
            if not self.channelMap[t].get_busy():
                s = self.queue[0]
                self.play_file(s, self.channelMap[t])
                self.channelLastPlayed[t] = s
                self.queue.remove(self.queue[0])
                if len(self.queue) > 0: # still have content queued
                    self.preloadNextSound()

        pass

    def loop(self, t: str):
        """Loop playing all sounds in that type. Needs to be called every time in the main loop.

        Args:
            t (str): type of sound
        """
        if len(self.queue) == 0:
            self.queue.extend(self._discoverSound(t))
        else:
            if not self.channelMap[t].get_busy():
                s = self.queue[0]
                self.play_file(s, self.channelMap[t])
                self.channelLastPlayed[t] = s
                self.queue.remove(self.queue[0])
                if len(self.queue) > 0: # still have content queued
                    self.preloadNextSound()
        # TODO REWRITE queue: use pointer to loop/all modes instead of remove (so no need to load sound again)

    def preloadNextSound(self):
        self.queue[0].getData()

    def next(self):
        self.mixer.fadeout(TRANSITION_LENGTH)

    def appendPlayList(self,t:str='show'):

        # assume all media in lib normalized.
        l =  self._discoverSound(t)
        for s in l:
            if s not in self.queue:
                self.queue.append(s)

    def shiftPlayList(self, idx, offset):
        target = idx + offset
        target = max(target, 0)
        target = min(target, len(self.queue)-1)
        self.queue[target], self.queue[idx] = self.queue[idx], self.queue[target]
    
    def removeFromPlayList(self,idx):
        del self.queue[idx]

    def stationID(self):
        """Play randomly selected stationID. Lower show volume during station ID.
        """
        vol = self.channelMap['show'].get_volume()
        effect.fadeOut(self.channelMap['show'], SURPRESSION_FACTOR*vol)
        duration = self.random('stationID')
        if duration > 10:
            self.channelMap['show'].pause()
            effect.fadeOut(self.channelMap['show'], 0)
        while self.channelMap['stationID'].get_busy():
            time.sleep(1)
        if duration > 10:
            self.channelMap['show'].unpause()
        effect.fadeIn(self.channelMap['show'], vol)
        logging.info("Station ID sent.")

