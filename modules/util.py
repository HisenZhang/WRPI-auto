import datetime
import hashlib
import logging
from math import ceil
import subprocess
import os
import multiprocessing
import pygame
from tinydb import TinyDB, Query  # lightweight DB based on JSON
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import yaml
import munch

# TODO hot patch


class Singleton(object):
    # http://www.python.org/download/releases/2.2/descrintro/#__new__
    def __new__(cls, *args, **kwds):
        it = cls.__dict__.get("__it__")
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwds)
        return it

    def init(self, *args, **kwds):
        pass


class configProxy(Singleton):
    # https://martin-thoma.com/configuration-files-in-python/
    def __init__(self) -> None:
        self.cfg = None
        self.load()

    def load(self, filename='config.yml'):
        with open(filename, "r") as ymlfile:
            d = yaml.safe_load(ymlfile)
        self.cfg = munch.munchify(d)

    def get(self):
        return self.cfg

    def reload(self):
        try:
            self.load('config.yml')
            logging.info('Config hot reload successfully.')
        except Exception as e:
            logging.error('Config hot reload error: ' + str(e))


configManager = configProxy()


class db(Singleton):
    def __init__(self, filename=None) -> None:
        super().__init__()
        self.conn = None
        if filename is not None:
            self.connect(filename)

    def connect(self, filename: str):
        if self.conn is not None:
            self.disconnect()
        if filename:
            self.conn = TinyDB(filename)
        else:
            self.conn = TinyDB(configManager.cfg.path.db)

    def disconnect(self):
        if self.conn:
            self.conn.close()

    def isNormalized(self, h: str) -> bool:
        """Test if file with given hash has been normalized

        Args:
            con (TinyDB): TinyDB object
            h (str): hash string

        Returns:
            bool: is the sound normalized
        """
        table = self.conn.table('sound')
        q = Query()
        data = table.search(q.hash == h)
        if len(data) == 0:
            return False
        else:
            return data[0]['loudness'] == configManager.cfg.audio.loudness

    def setRecord(self, n: str, h: str, l: int, b: str):
        """Insert record to database

        Args:
            con (TinyDB): TinyDB object
            n (str): name of sound file
            h (str): hash of sound file
            l (int): loudness in LUFS
            b (str): bitrate
        """
        table = self.conn.table('sound')
        q = Query()
        table.upsert({'name': n,
                      'hash': h,
                      'loudness': l,
                      'bitrate': b},
                     q.hash == h)
        pass

    def __del__(self):
        self.disconnect()


class fsUtil:
    # TODO file system watchdog for normalization
    class SoundWatchdogHandler(PatternMatchingEventHandler):
        def process(self, event):
            """
            event.event_type 
                'modified' | 'created' | 'moved' | 'deleted'
            event.is_directory
                True | False
            event.src_path
                path/to/observed/file
            """
            logging.info(
                "libWatchdog: {} - {}".format(event.src_path, event.event_type))
            # normalize

        def on_created(self, event):
            self.process(event)

    def libWatchdogInit():
        patterns = ['*'+t for t in configManager.cfg.audio.formats]
        path = os.path.join(os.getcwd(), configManager.cfg.path.lib)
        observer = Observer()
        observer.schedule(fsUtil.SoundWatchdogHandler(patterns=patterns,
                                                      case_sensitive=True),
                          path=path,
                          recursive=True)
        observer.setName('libWatch')
        observer.start()
        logging.info("libWatchdog started.")
        logging.debug(
            "Looking for change in {} of following sound types:{}".format(path, patterns))
        return observer

    # config hot reload
    class ConfigWatchdogHandler(PatternMatchingEventHandler):
        def process(self, event):
            global configManager
            logging.info(
                "configWatchdog: {} - {}".format(event.src_path, event.event_type))
            configManager.reload()

        def on_modified(self, event):
            self.process(event)

    def configWatchdogInit():
        patterns = ['*.yml']
        path = os.getcwd()
        observer = Observer()
        observer.schedule(fsUtil.ConfigWatchdogHandler(patterns=patterns,
                                                       case_sensitive=True),
                          path=path,
                          recursive=False)
        observer.setName('configWatch')
        observer.start()
        logging.info("configWatchdog started.")
        logging.debug(
            "Looking for config change recursively in {} of following config types:{}".format(path, patterns))
        return observer

    def sha256sum(filename: str) -> str:
        """Calculate hash from file in chunks

        Args:
            filename (str): path to the file 

        Returns:
            str: hash string
        """
        h = hashlib.sha256()
        b = bytearray(128*1024)
        mv = memoryview(b)
        with open(filename, 'rb', buffering=0) as f:
            for n in iter(lambda: f.readinto(mv), 0):
                h.update(mv[:n])
        return h.hexdigest()

    def list_sound(t: str) -> list:
        """list sound files of the given type

        Args:
            t (str): type of sound

        Returns:
            list: a list of sound files
        """
        return [os.path.join(configManager.cfg.path.lib, t, f) for f in
                os.listdir(os.path.join(configManager.cfg.path.lib, t))
                if f.lower().endswith(tuple(configManager.cfg.audio.formats))]

    def soundDuration(file: str):
        s = pygame.mixer.Sound(file)
        l = s.get_length()
        return l


class conversion:
    def floatToHMS(f: float):
        if f < 0:
            raise ValueError("Duration must be non-negative")

        fmt = "{hours:0>1}:{minutes:0>2}:{seconds:0>2}"
        tdelta = datetime.timedelta(seconds=ceil(f))
        d = {}
        d["hours"], rem = divmod(tdelta.seconds, 3600)
        d["hours"] += tdelta.days * 24
        d["minutes"], d["seconds"] = divmod(rem, 60)
        return fmt.format(**d)


class ffmpegWrapper:
    def getLength(file):
        logging.debug("Running getLength:")
        prog = ''
        if os.name == 'nt':  # Windows
            prog = 'ffprobe.exe'
        elif os.name == 'posix':  # Linux, Mac OS, etc
            prog = "./ffprobe"
        try:
            try:
                result = subprocess.run([os.path.join(configManager.cfg.path.bin, prog), '-v', 'error', '-show_entries', 'format=duration', '-of',
                                        'default=noprint_wrappers=1:nokey=1', file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                logging.debug("getLength output: "+repr(result))
            except PermissionError as e:
                logging.error("Permission error: " + str(e))
            try:
                length = float(result.stdout)
                logging.debug(
                    "getLength output {}: ".format(file)+repr(result))
                return length
            except ValueError as e:
                logging.error(
                    "Unexpected output for getLength (float expected): " + length)
        except Exception as e:
            logging.error("Error occured in the ffprobe getLength: " + str(e))

            """ .\bin\ffmpeg.exe -i '.\lib\show\My Funny Valentine.m4a' -hide_banner -filter_complex ebur128 -f null -"""

    def getLoudness(file):
        logging.debug("Running getLoudness:")
        prog = ''
        if os.name == 'nt':  # Windows
            prog = 'ffmpeg.exe'
        elif os.name == 'posix':  # Linux, Mac OS, etc
            prog = "./ffmpeg"
        try:
            # run command
            try:
                result = subprocess.run([os.path.join(configManager.cfg.path.bin, prog), '-i', file, '-hide_banner', '-filter_complex',
                                        'ebur128', '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                logging.debug("getLength output: "+repr(result))
            except PermissionError as e:
                logging.error("Permission error: " + str(e))
            # extract result
            try:
                loudness = float(result.stdout.splitlines()[-8].split()[1])
                logging.debug(
                    "Loudness of {} is {} LUFS".format(file, loudness))
                return loudness
            except ValueError as e:
                logging.error(
                    "Unexpected output for loudness (float expected): " + loudness)
        except Exception as e:
            logging.error(
                "Error occured in the ffmpeg loudness detection: " + str(e) + repr(result))

    # TODO logging is not process safe!
    def normalizeLoudness(file, loudness):
        workerName = multiprocessing.current_process().name
        logging.debug(
            "Worker " + workerName + " has started.")
        prog = ''
        if os.name == 'nt':  # Windows
            prog = 'ffmpeg.exe'
        elif os.name == 'posix':  # Linux, Mac OS, etc
            prog = "./ffmpeg"
        try:
            os.rename(file, file+".normalizing")
            cmd = '"{prog}" -y -i "{infile}" -af loudnorm=I={loudness}:LRA=7:tp=-2 -b:a "{bitrate}" -f mp3 "{outfile}"'.format(
                prog=os.path.join(configManager.cfg.path.bin, prog),
                loudness=loudness,
                bitrate=str(configManager.cfg.audio.bitrate),
                infile=file+".normalizing",
                outfile=file+".normalized")

            logging.info(
                "Normalizing loudness for \"{}\" at {} LUFS".format(file, loudness))
            logging.debug("Command: " + cmd)

            # suppress output to stdout from the subprocess
            FNULL = open(os.devnull, 'w')
            subprocess.call(cmd, stdout=FNULL, stderr=FNULL, shell=False)
            # subprocess.call(cmd, shell=False)
            logging.debug("ffmpeg exited")

            os.remove(file+".normalizing")
            os.rename(file+".normalized", file)
        except PermissionError as e:
            logging.error("Permission error: " + str(e))
        except Exception as e:
            logging.error(
                "Error occurred in the loudness normalization: " + str(e))
        finally:
            logging.debug("Worker " + workerName + " ends.")
