import headless
import argparse
import threading
import schedule
import sys
import logging
import py_cui
from modules.tui import TUI
from modules.config import STATION_NAME


def runSchedule(station):
    while station.mixer.get_init():
        logging.debug("Hello from backgroud thread...")
        schedule.run_pending()


def main():
    parser = argparse.ArgumentParser(
        description='{station} Broadcast Automation System'.format(station=STATION_NAME))
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
                '{} Broadcast Automation System'.format(STATION_NAME))
            frame = TUI(mainWindow)
            daemonThread = threading.Thread(
                name='Daemon', target=runSchedule, args=(frame.station,), daemon=True)
            daemonThread.start()
            logging.info("TUI starting...")
            mainWindow.start()
            logging.info("TUI exited.")
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt detected.")
        except Exception as e:
            logging.critical("TUI: "+str(e))
        finally:
            if frame:
                frame.station.signOff()
            sys.exit(0)


if __name__ == "__main__":
    main()
