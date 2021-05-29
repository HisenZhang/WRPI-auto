import hashlib
import logging
import subprocess
import os
import multiprocessing

import traceback

from tinydb import TinyDB, Query  # lightweight DB based on JSON

from .config import *


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
            cmd = '"{prog}" -y -i "{infile}" -af loudnorm=I={loudness}:LRA=7:tp=-2:print_format=json -b:a "{bitrate}" -f mp3 "{outfile}"'.format(
                prog=os.path.join(FFMPEG_PATH, prog),
                loudness=loudness,
                bitrate=str(BITRATE),
                infile=file,
                outfile=file+".normalized")

            logging.debug("Command: " + cmd)

            # suppress output to stdout from the subprocess
            FNULL = open(os.devnull, 'w')
            subprocess.call(cmd, stdout=FNULL, stderr=FNULL, shell=False)
            # subprocess.call(cmd, shell=False)
            logging.debug("ffmpeg exited")

            os.remove(file)
            os.rename(file+".normalized", file)
        except PermissionError as e:
            logging.error("Permission error: " + str(e))
        except Exception as e:
            logging.error("Error occured in the subprocess: " + str(e))
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
        return [f for f in os.listdir(os.path.join(LIB_BASE, t)) if f.lower().endswith(SOUND_FORMAT)]