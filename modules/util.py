import datetime
import hashlib
import logging
from math import ceil
import subprocess
import os
import multiprocessing
import pygame
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


from tinydb import TinyDB, Query  # lightweight DB based on JSON

from .config import LIB_BASE, EXT_BIN_PATH, BITRATE, LOUDNESS, SOUND_FORMAT


class db:
    def isNormalized(con: TinyDB, h: str) -> bool:
        """Test if file with given hash has been normalized

        Args:
            con (TinyDB): TinyDB object
            h (str): hash string

        Returns:
            bool: is the sound normalized
        """
        table = con.table('sound')
        q = Query()
        data = table.search(q.hash == h)
        if len(data) == 0:
            return False
        else:
            return data[0]['loudness'] == LOUDNESS

    def setRecord(con: TinyDB, n: str, h: str, l: int, b: str):
        """Insert record to database

        Args:
            con (TinyDB): TinyDB object
            n (str): name of sound file
            h (str): hash of sound file
            l (int): loudness in LUFS
            b (str): bitrate
        """
        table = con.table('sound')
        q = Query()
        table.upsert({'name': n,
                      'hash': h,
                      'loudness': l,
                      'bitrate': b},
                     q.hash == h)
        pass


class fsUtil:
    # TODO file system watchdog for normalization
    class SoundWatchdogHandler(PatternMatchingEventHandler):
        patterns = SOUND_FORMAT

        def process(self, event):
            """
            event.event_type 
                'modified' | 'created' | 'moved' | 'deleted'
            event.is_directory
                True | False
            event.src_path
                path/to/observed/file
            """
            # the file will be processed there
            print(event.src_path, event.event_type)  # print now only for degug

        def on_modified(self, event):
            self.process(event)

        def on_created(self, event):
            self.process(event)

    def fsWatchdogInit():
        observer = Observer()
        observer.schedule(fsUtil.SoundWatchdogHandler(),
                          path=os.path.join(os.getcwd(), LIB_BASE))
        observer.start()
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
        return [os.path.join(LIB_BASE, t, f) for f in os.listdir(os.path.join(LIB_BASE, t)) if f.lower().endswith(SOUND_FORMAT)]

    def soundDuration(file: str):
        s = pygame.mixer.Sound(file)
        l = s.get_length()
        return l


class conversion:
    def floatToHMS(f: float):
        return str(datetime.timedelta(seconds=ceil(f)))


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
                result = subprocess.run([os.path.join(EXT_BIN_PATH, prog), '-v', 'error', '-show_entries', 'format=duration', '-of',
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
                result = subprocess.run([os.path.join(EXT_BIN_PATH, prog), '-i', file, '-hide_banner', '-filter_complex',
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
                "Error occured in the ffmpeg loudness detection: " + str(e))

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
                prog=os.path.join(EXT_BIN_PATH, prog),
                loudness=loudness,
                bitrate=str(BITRATE),
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
                "Error occured in the loudness normalization: " + str(e))
        finally:
            logging.debug("Worker " + workerName + " ends.")
