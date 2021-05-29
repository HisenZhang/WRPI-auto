import multiprocessing
import time
import logging
from pygame import mixer

from tinydb import TinyDB, Query  # lightweight DB based on JSON

from .config import TRANSITION_LENGTH,LOUDNESS,NUM_CHANNEL
from .util import fsUtil, db, paralell


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

    # def async_normalize(con: TinyDB, file: str):

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
        self.mixer = mixer
        self.mixer.init()
        self.mixer.set_num_channels(NUM_CHANNEL)
        self.mixer.music.set_volume(1)
        self.channelMap = {
            "master": self.mixer.music,
            "stationID": self.mixer.Channel(0),
            "show": self.mixer.Channel(1),
            "fill": self.mixer.Channel(2),
            "PSA": self.mixer.Channel(3),
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

    def destroy(self):
        self.mixer.stop()
        self.mixer.quit()
