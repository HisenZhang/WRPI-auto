from . import play
from . import audio
import logging
import multiprocessing
import time
import os
import sys
import psutil
import schedule

from .util import configManager, fsUtil, db


class manager:
    """Station manager. The public interface for all operations. Include a play control instance.
    """
    def __init__(self) -> None:
        self.mixer = audio.virtualMixerWrapper()
        self.playControl = play.control(self.mixer)
        self.cwd = os.getcwd()
        self.systemStat = None
        self.db = db()
        self.lastSignIn = None # identify if system has signed in successfully (not None)
        try:
            self.db.connect('db.json')
        except IOError as e:
            logging.critical("Cannot connect to database: "+str(e))
        self.watchdogs = [fsUtil.libWatchdogInit(),
                          fsUtil.configWatchdogInit()]
        pass

    def ID(self):
        """Station ID
        """
        try:
            self.playControl.stationID()
        except Exception as e:
            logging.critical("Station ID not sent: " + str(e))
            self.mixer.pause()

    def scheduleInit(self):
        """Register events in schedule
        """
        cfg = configManager.cfg.schedule
        # System monitor
        schedule.every(cfg.systemMonitor.interval).minutes.at(
            cfg.systemMonitor.time).do(self.systemMonitor)
        # Station ID
        schedule.every(cfg.stationID.interval).hours.at(
            cfg.stationID.time).do(self.ID)
        # Mixer digest
        schedule.every(cfg.mixerDigest.interval).minutes.at(
            cfg.mixerDigest.time).do(self.mixer.digest)
        # Volume guard
        schedule.every(cfg.volumeGuard.interval).minutes.at(
            cfg.volumeGuard.time).do(self.mixer.volumeGuard)

    def scheduleRun(self):
        """Run the schedule loop
        """ 
        schedule.run_pending()

    # TODO signIn / Out special audio
    def signIn(self):
        """Sign in to station to get mixer!

        Returns:
            virtualMixer: Virtual audio mixer
        """
        logging.warning("Welcome to {stationName} automation system. Signing in.".format(
            stationName=configManager.cfg.station.name))
        try:
            assert len(fsUtil.list_sound('stationID')) > 0
        except AssertionError:
            logging.critical('No stationID sound available.')
            sys.exit(1)

        logging.info("Scanning sound lib...")
        self.loudNorm()
        logging.info("All sounds in lib normalized.")
        self.ID()
        self.lastSignIn = time.time()

    def loudNorm(self, targets: list = None):
        """Loudness normalization in parallel

        Args:
            targets (list, optional): Sounds to be normalized. Defaults to None.
        """
        procs = []

        if targets is None:
            # get sub dirs in lib using magic
            subDir = [d[1]
                      for d in os.walk(configManager.cfg.path.lib) if d[1]][0]
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
                    self.db.setRecord(file, fsUtil.sha256sum(
                        file), configManager.cfg.audio.loudness, configManager.cfg.audio.bitrate)
                    procs.remove(p)
            except Exception as e:
                logging.error("Process error: " + str(e))
                for p in multiprocessing.active_children():
                    p.kill()

    def systemMonitor(self):
        """Monitor system resources such as CPU and RAM usage

        Returns:
            dict: dictionary containing system statistics
        """ 
        try:
            self.systemStat = {
                'CPU': psutil.cpu_percent(),
                'RAM': psutil.virtual_memory(),
                'storage': psutil.disk_usage(self.cwd),
                'power': psutil.sensors_battery()
            }
            if self.systemStat['CPU'] > configManager.cfg.alert.threshold.cpu:
                logging.warning('CPU usage too high: {}%'.format(
                    self.systemStat['CPU']))
            if self.systemStat['RAM'].percent > configManager.cfg.alert.threshold.ram:
                logging.warning('RAM usage too high: {}%'.format(
                    self.systemStat['RAM'].percent))
            if self.systemStat['storage'].percent > configManager.cfg.alert.threshold.storage:
                logging.warning('Storage space too full: {}%'.format(
                    self.systemStat['storage'].percent))
            if self.systemStat['power'] != None and \
                (self.systemStat['power'].percent < configManager.cfg.alert.threshold.power and
                    not self.systemStat['power'].power_plugged):
                logging.warning('Battery not charging: {}%'.format(
                    self.systemStat['power'].percent))
        except Exception as e:
            logging.critical("Fail to update system statistics: "+str(e))
        finally:
            return self.systemStat

    def signOff(self):
        """Release resources.
        """

        for wd in self.watchdogs:
            wd.unschedule_all()
            wd.stop()
            logging.info("{} stopped.".format(wd.name))

        self.mixer.destroy()
        logging.debug("Mixer Destroyed.")

        self.db.disconnect()
        logging.debug("Database disconnected.")

        logging.warning("{stationName} automation system terminates. Signing off.".format(
            stationName=configManager.cfg.station.name))

        self.lastSignIn = None

    def __del__(self):
        if self.lastSignIn is not None:
            self.signOff()
