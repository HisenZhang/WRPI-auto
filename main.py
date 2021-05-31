import headless
import argparse
import sys
import time
import schedule
import logging
import threading
import py_cui
from modules.tui import TUI
from modules.config import STATION_NAME


def backgroundTask(station):
    while station.mixer.get_init():
        logging.debug("Hello from backgroud thread...")
        schedule.run_pending()
        station.playControl.loop('show')
        time.sleep(1)


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
            mainWindow = py_cui.PyCUI(3, 3, exit_key=1)
            mainWindow.set_refresh_timeout(1)            
            mainWindow.set_title(
                '{} Broadcast Automation System'.format(STATION_NAME))
            frame = TUI(mainWindow)
            daemonThread = threading.Thread(
                name='Daemon', target=backgroundTask, args=(frame.station,), daemon=True)
            daemonThread.start()
            # Wait until initial stationID is done
            while frame.mixer.channelMap['stationID'].get_busy():
                time.sleep(0.5)
            logging.info("TUI starting...")
            mainWindow.start()
            logging.info("TUI exited.")
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt detected.")
        except Exception as e:
            logging.critical("TUI: "+str(e))
        finally:
            frame.station.signOff()
            sys.exit(0)


if __name__ == "__main__":
    main()
