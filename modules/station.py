import logging
import multiprocessing
import time
import os
import sys
import psutil
from tinydb import TinyDB, Query  # lightweight DB based on JSON

from .config import LIB_BASE, LOUDNESS, BITRATE, STATION_NAME, TRANSITION_LENGTH
from .util import ffmpegWrapper, fsUtil, db
from . import audio
from . import play


class control:
    def __init__(self) -> None:
        self.mixer = audio.virtualMixerWrapper()
        self.playControl = play.control(self.mixer)
        self.cwd = os.getcwd()
        self.systemStat = None
        self.db = TinyDB('db.json')
        pass

    def ID(self):
        """Station ID
        """
        try:
            self.playControl.stationID()
        except Exception as e:
            logging.critical("Station ID not sent: " + str(e))
            self.signOff()
            sys.exit(0)
    
    # TODO signIn / Out special audio 
    def signIn(self):
        """Sign in to station to get mixer!

        Returns:
            virtualMixer: Virtual audio mixer
        """
        logging.warning("Welcome to {stationName} automation system. Signing in.".format(
            stationName=STATION_NAME))
        try:
            assert len(fsUtil.list_sound('stationID')) > 0
        except AssertionError:
            logging.critical('No stationID sound available.')
            sys.exit(1)

        logging.info("Scanning sound lib...")
        self.loudNorm()
        logging.info("All sounds in lib normalized.")
        self.ID()
        return self.mixer

    def loudNorm(self, targets:list=None):
        procs = []

        if targets is None:
            # get sub dirs in lib using magic
            subDir = [d[1] for d in os.walk(LIB_BASE) if d[1]][0]
            for sub in subDir:
                for s in fsUtil.list_sound(sub):
                    p = audio.effect.normalize(s)
                    if p != None:
                        procs.append((p, s))
        else:
            for s in targets:
                p = audio.effect.normalize(self.db, s)
        
        if len(procs) > 0:
            logging.info("Waiting for loudness normalization...")

            try:
                for p in procs:
                    p[0].join()

                while len(multiprocessing.active_children()) > 0:
                    time.sleep(0.1)

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

    def systemMonitor(self):
        try:
            self.systemStat = {
                'CPU':psutil.cpu_percent(),
                'RAM':psutil.virtual_memory(),
                'storage':psutil.disk_usage(self.cwd),
                'power':psutil.sensors_battery()
            }
            if self.systemStat['CPU'] > 90:
                logging.warning('CPU usage too high: {}%'.format(self.systemStat['CPU']))
            if self.systemStat['RAM'].percent > 90:
                logging.warning('RAM usage too high: {}%'.format(self.systemStat['RAM'].percent))
            if self.systemStat['storage'].percent > 90:
                logging.warning('Storage space too full: {}%'.format(self.systemStat['storage'].percent))
            if self.systemStat['power'] != None and (self.systemStat['power'].percent < 50 and not self.systemStat['power'].power_plugged):
                logging.warning('Battery not charging: {}%'.format(self.systemStat['power'].percent))
        except Exception as e:
            logging.critical("Fail to update system statistics: "+str(e))
        finally:
            return self.systemStat

    def signOff(self):
        """Release resources.
        """
        self.mixer.destroy()
        logging.debug("Mixer Destroyed.")

        self.db.close()
        logging.debug("Database disconnected.")

        logging.warning("{stationName} automation system terminates. Signing off.".format(
            stationName=STATION_NAME))
