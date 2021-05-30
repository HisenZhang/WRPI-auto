import logging
import multiprocessing
import time
import os
import sys
from tinydb import TinyDB, Query  # lightweight DB based on JSON

from .config import LIB_BASE, LOUDNESS, BITRATE, STATION_NAME
from .util import fsUtil, db
from . import audio
from . import play


class control:
    def __init__(self) -> None:
        self.mixer = audio.virtualMixerWrapper()
        self.playControl = play.control(self.mixer)
        self.db = TinyDB('db.json')
        pass

    def ID(self):
        """Station ID
        """
        self.playControl.stationID()

    def signIn(self):
        """Sign in to station to get mixer!

        Returns:
            virtualMixer: Virtual audio mixer
        """
        logging.info("Welcome to {stationName} automation system. Signing in.".format(
            stationName=STATION_NAME))
        try:
            assert len(fsUtil.list_sound('stationID')) > 0
        except AssertionError:
            logging.critical('No stationID sound available.')
            sys.exit(1)

        logging.info("Scanning sound lib...")

        procs = []
        # get sub dirs in lib using magic
        subDir = [d[1] for d in os.walk(LIB_BASE) if d[1]][0]
        for sub in subDir:
            for sound in fsUtil.list_sound(sub):
                file = os.path.join(LIB_BASE, sub, sound)
                p = audio.effect.normalize(self.db, file)
                if p != None:
                    procs.append((p, file))

        logging.info("Waiting for loudness normalization...")

        try:
            for p in procs:
                p[0].join()

            while len(multiprocessing.active_children()) > 0:
                time.sleep(1)

            for p in procs:  # t = (thread, file)
                p[0].close()
                file = p[1]
                db.setRecord(self.db, file, fsUtil.sha256sum(
                    file), LOUDNESS, BITRATE)
                procs.remove(p)
        except Exception as e:
            logging.error("Process error: " + str(e))
            for p in multiprocessing.active_children():
                p.kill()

        logging.info("All sounds in lib normalized.")

        self.ID()
        return self.mixer

    def signOff(self):
        """Release resources.
        """
        self.mixer.destroy()
        logging.debug("Mixer Destroyed.")

        self.db.close()
        logging.debug("Database disconnected.")

        logging.info("{stationName} automation system terminates. Signing off.".format(
            stationName=STATION_NAME))
