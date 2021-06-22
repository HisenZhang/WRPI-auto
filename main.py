import headless
import argparse
import threading
import sys
import logging
import py_cui
from modules.tui import TUI
from modules.util import configManager


def runSchedule(station):
    logging.info("Scheduler started.")
    while station.mixer.get_init():
        station.scheduleRun()


def runTUI(mainWindow):
    logging.info("TUI starting...")
    mainWindow.start()
    logging.info("TUI exited.")


def main():
    parser = argparse.ArgumentParser(
        description='{station} Broadcast Automation System'.format(station=configManager.cfg.station.name))
    parser.add_argument('--headless', action='store_true',
                        help='run without TUI')

    args = parser.parse_args()
    if args.headless:
        headless.routine()
    else:
        try:
            frame = None
            mainWindow = py_cui.PyCUI(4, 3, exit_key=1)
            mainWindow.set_refresh_timeout(1)
            mainWindow.set_title(
                '{} Broadcast Automation System'.format(configManager.cfg.station.name))
            frame = TUI(mainWindow)

            daemonThread = threading.Thread(
                name='Daemon', target=runSchedule, args=(frame.station,), daemon=True)
            daemonThread.start()

            TUIThread = threading.Thread(
                name='TUI', target=runTUI, args=(mainWindow,))
            TUIThread.start()
            TUIThread.join()

        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt detected.")
        except Exception as e:
            logging.critical("TUI: "+str(e))
        finally:
            if frame:
                frame.station.signOff()
            sys.exit(0)

# TODO turn this into a package at first major released
# packaging: https://uoftcoders.github.io/studyGroup/lessons/python/packages/lesson/
# with CLI: https://medium.com/nerd-for-tech/how-to-build-and-distribute-a-cli-tool-with-python-537ae41d9d78


if __name__ == "__main__":
    main()
