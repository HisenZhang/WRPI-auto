import multiprocessing
import threading
import time
import logging
from pygame import mixer
import asyncio

from .util import configManager, ffmpegWrapper, conversion, Singleton


class sound:
    """Sound lazy-load proxy class
    """
    def __init__(self, filename, duration=None) -> None:
        self.path = filename
        self.data = None # load on demand
        self.duration = duration

    def getDuration(self):
        if self.duration is None:
            self.duration = ffmpegWrapper.getLength(self.path)
        return self.duration

    def getData(self):
        if self.data is None:
            self.data = mixer.Sound(self.path)
        return self.data

    def strDuration(self):
        return conversion.floatToHMS(self.getDuration())

    def unloadData(self):
        self.data = None

    def __str__(self) -> str:
        return self.path


class effect:
    """Common audio effects
    """
    def fadeOut(chan: mixer.Channel, desired_vol: int = 0):
        asyncio.run(effect._fadeOut(chan, desired_vol))

    def fadeIn(chan: mixer.Channel, desired_vol: int = 0):
        asyncio.run(effect._fadeIn(chan, desired_vol))

    async def _fadeOut(chan: mixer.Channel, desired_vol: int = 0):
        """Fade out effect

        Args:
            chan (mixer.Channel): the channel affected
            desired_vol (int, optional): the vol after fading. Assumed lower than original. Defaults to 0.
        """
        vol = chan.get_volume()
        for i in range(1, configManager.cfg.audio.transition_length):
            await asyncio.sleep(1/configManager.cfg.audio.transition_length)
            chan.set_volume((configManager.cfg.audio.transition_length-i) /
                            configManager.cfg.audio.transition_length*(vol-desired_vol)+desired_vol)
        # Avoid float point error builds up
        chan.set_volume(desired_vol)

    async def _fadeIn(chan: mixer.Channel, desired_vol: int = 1):
        """Fade in effect

        Args:
            chan (mixer.Channel): the channel affected
            desired_vol (int, optional): the vol after fading. Assumed higher than original. Defaults to 1.
        """
        vol = chan.get_volume()
        for i in range(1, configManager.cfg.audio.transition_length):
            await asyncio.sleep(1/configManager.cfg.audio.transition_length)
            chan.set_volume(i/configManager.cfg.audio.transition_length *
                            (desired_vol-vol)+vol)
        # Avoid float point error builds up
        chan.set_volume(desired_vol)

    def normalize(file: str):
        # allow +/- 1.5 LUFS error
        if abs(ffmpegWrapper.getLoudness(file) - configManager.cfg.audio.loudness) > configManager.cfg.audio.loudness_tolerant:
            p = effect._normalize(file, configManager.cfg.audio.loudness)
            return p
        else:
            return None

    def _normalize(file, loudness: None):
        """Loudness normalization in parallel

        Args:
            file (str): path to sound
            loudness (int): a negative value in LUFS

        Returns:
            multiprocessing.Process: a process running the normalization wrapper,
            or nothing if loudness check fails
        """
        if loudness is None:
            loudness = configManager.cfg.audio.loudness
        try:
            assert loudness <= 0
        except AssertionError:
            logging.error("Invalid loudness valid in LUFS.")
            return

        p = multiprocessing.Process(
            name='FFMPEG '+file, target=ffmpegWrapper.normalizeLoudness, args=(file, loudness))
        p.start()
        return p


class virtualMixerWrapper(Singleton):
    """A mixer wrapper managing multi-channel information
    """
    def __init__(self) -> None:
        DEFAULT_CHANNEL = ["stationID", "show", "fill", "PSA"]
        self.lock = threading.RLock()
        self.mixer = mixer
        self.mixer.init()
        All_CHANNEL = DEFAULT_CHANNEL + configManager.cfg.audio.user_channels
        self.mixer.set_num_channels(len(All_CHANNEL))
        self.mixer.music.set_volume(1)
        self.channelMap = {}
        for i, chan in enumerate(All_CHANNEL):
            self.channelMap[chan] = self.mixer.Channel(i)
        self.channelLastPlayed = {}
        for _, chan in enumerate(All_CHANNEL):
            self.channelLastPlayed[chan] = None
        self.vol = {}
        self.muted = False
        self.paused = False

    def digest(self):
        """What's playing in each channel.
        """
        with self.lock:
            self.get_volume()
            stringBuffer = ['Mixer digest:']
            for chan, sound in self.channelLastPlayed.items():
                if self.channelMap[chan].get_busy():
                    stringBuffer.append("[{chan}]  ({vol}%) - {sound}".format(
                        chan=chan, vol=int(self.vol[chan]*100), sound=sound.path))
            logging.info(' '.join(stringBuffer))

    def get_volume(self) -> map:
        with self.lock:
            for name, chan in self.channelMap.items():
                self.vol[name] = chan.get_volume()
            return self.vol

    def get_busy(self) -> bool:
        return self.mixer.mixer.get_busy()

    def mute(self):
        with self.lock:
            if self.muted == True:
                return
            for _, chan in self.channelMap.items():
                chan.set_volume(0)
            self.muted = True
            logging.warning("All channels muted.")

    def unmute(self):
        with self.lock:
            if self.muted == False:
                return
            for _, chan in self.channelMap.items():
                chan.set_volume(1)
            self.muted = False
            logging.warning("All channels unmuted.")

    def pause(self):
        with self.lock:
            if self.paused == True:
                return
            for _, chan in self.channelMap.items():
                chan.pause()
            self.paused = True
            logging.warning("All channels paused.")

    def resume(self):
        with self.lock:
            if self.paused == False:
                return
            for _, chan in self.channelMap.items():
                chan.unpause()
            self.paused = False
            logging.warning("All channels resumed.")

    def fadeout(self, length):
        self.mixer.fadeout(length)

    def volumeUp(self):
        with self.lock:
            self.volumeChange(+0.1)

    def volumeDown(self):
        with self.lock:
            self.volumeChange(-0.1)

    def volumeChange(self, deviation):
        with self.lock:
            self.get_volume()
            for name, vol in self.vol.items():
                target = vol + deviation
                target = min(target, 1.0)
                target = max(target, 0)
                self.channelMap[name].set_volume(target)

    def get_init(self):
        return self.mixer.get_init()

    def volumeGuard(self):
        if self.muted or self.paused:
            return
        for _, chan in self.channelMap.items():
            effect.fadeIn(chan, 1)

    def destroy(self):
        with self.lock:
            if self.mixer.get_init():
                self.mixer.fadeout(configManager.cfg.audio.transition_length)
                self.mixer.stop()
            self.mixer.quit()
