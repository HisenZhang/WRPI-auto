import datetime
import hashlib
import logging
from math import ceil
import subprocess
import os
import multiprocessing
import pygame


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


class paralell:
    def ffmpegWorker(file, loudness):
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
            cmd = '"{prog}" -y -i "{infile}" -af loudnorm=I={loudness}:LRA=7:tp=-2:print_format=json -b:a "{bitrate}" -f mp3 "{outfile}"'.format(
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
            logging.error("Error occured in the loudness normalization: " + str(e))
        finally:
            logging.debug("Worker " + workerName + " ends.")


class fsUtil:
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

    def getLength(file):
        logging.debug("Running getLength:")
        prog = ''
        if os.name == 'nt':  # Windows
            prog = 'ffprobe.exe'
        elif os.name == 'posix':  # Linux, Mac OS, etc
            prog = "./ffprobe"
        try:
            result = subprocess.run([os.path.join(EXT_BIN_PATH,prog), '-v', 'error', '-show_entries', 'format=duration', '-of',
                                    'default=noprint_wrappers=1:nokey=1', file], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logging.debug("getLength output: "+repr(result))                       
            return float(result.stdout)
        except PermissionError as e:
            logging.error("Permission error: " + str(e))
        except Exception as e:
            logging.error("Error occured in the ffprobe getLength: " + str(e))

class conversion:
    def floatToHMS(f: float):
        return str(datetime.timedelta(seconds=ceil(f)))
