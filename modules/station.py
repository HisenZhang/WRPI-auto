import logging
from pygame import mixer
from .config import *
from . import audio


class control:
    def __init__(self) -> None:
        self.mixer = audio.virtualMixerWrapper()
        self.playControl = audio.control(self.mixer)
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
        logging.info("Welcome to WRPI automation system. Signing in.")
        try:
            assert len(audio.util.list_sound('stationID')) > 0
        except AssertionError:
            logging.critical('No stationID sound available.')

        self.ID()
        return self.mixer

    def signOff(self):
        """Release resources.
        """
        mixer.stop()
        mixer.quit()
        logging.info("Mixer Destroyed.")
        logging.info("WRPI automation system terminates. Signing off.")
