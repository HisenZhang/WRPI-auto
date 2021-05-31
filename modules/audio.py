import multiprocessing
import threading
import time
import logging
from pygame import mixer

from tinydb import TinyDB, Query, utils  # lightweight DB based on JSON

from .config import TRANSITION_LENGTH, LOUDNESS, NUM_CHANNEL
from .util import fsUtil, db, paralell, conversion

class sound:
    def __init__(self,filename,duration=None) -> None:
        self.path = filename
        self.data = None
        self.duration = duration

    def _get_length(self):
        return fsUtil.getLength(self.path)

    def getDuration(self):
        if self.duration is None:
            self.duration = self._get_length()
        return self.duration

    def getData(self):
        if self.data is None:
            self.data = mixer.Sound(self.path)
        return self.data

    def strDuration(self):
        return conversion.floatToHMS(self.getDuration())

    def __str__(self) -> str:
        return self.path

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
        # Avoid float point error builds up
        chan.set_volume(desired_vol)

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
        # Avoid float point error builds up
        chan.set_volume(desired_vol)

    def normalize(con: TinyDB, file: str):
        if not db.isNormalized(con, fsUtil.sha256sum(file)):
            p = effect._normalize(file, LOUDNESS)
            return p
        else:
            return None

    def _normalize(file, loudness: int = -23):
        try:
            assert loudness <= 0
        except AssertionError:
            logging.error("Invalid loudness valid in LUFS.")
            return

        p = multiprocessing.Process(
            name='FFMPEG '+file, target=paralell.ffmpegWorker, args=(file, loudness))
        p.start()
        return p


class virtualMixerWrapper:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.mixer = mixer
        self.mixer.init()
        self.mixer.set_num_channels(NUM_CHANNEL)
        self.mixer.music.set_volume(1)
        self.channelMap = {
            "stationID": self.mixer.Channel(0),
            "show": self.mixer.Channel(1),
            "fill": self.mixer.Channel(2),
            "PSA": self.mixer.Channel(3),
        }
        self.channelLastPlayed = {}
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
            effect.fadeOut(self.mixer.music)
            self.mixer.pause()
            self.paused = True
            logging.warning("All channels paused.")

    def unpause(self):
        with self.lock:
            if self.paused == False:
                return
            effect.fadeIn(self.mixer.music)
            self.mixer.unpause()
            self.paused = False
            logging.warning("All channels unpaused.")

    def volumeUp(self):
        with self.lock:
            self.volumeShift(+0.1)

    def volumeDown(self):
        with self.lock:
            self.volumeShift(-0.1)

    def volumeShift(self, deviation):
        with self.lock:
            self.get_volume()
            for name, vol in self.vol.items():
                target = vol + deviation
                target = min(target, 1.0)
                target = max(target, 0)
                self.channelMap[name].set_volume(target)

    def get_init(self):
        return self.mixer.get_init()

    def destroy(self):
        with self.lock:
            if self.mixer.get_init():
                self.mixer.fadeout(TRANSITION_LENGTH)
                self.mixer.stop()
            self.mixer.quit()
