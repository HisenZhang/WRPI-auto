from datetime import datetime
from .logger import rootLogger, logFormatter
import logging
from typing import ChainMap
import py_cui
import schedule
import sys
import types

from modules import station
from modules.config import STATION_NAME
from modules.util import conversion


class TUIHandler(logging.Handler):
    def __init__(self, parent):
        logging.Handler.__init__(self)
        self.parent = parent

    def emit(self, record):
        if record:
            self.parent.write(self.format(record))


class TUI():
    def __init__(self, root: py_cui.PyCUI) -> None:
        self.station = station.control()
        self.mixer = self.station.signIn()

        # Register schedule
        # schedule.every().hour.at(":00").do(play_stationID) # real business here
        # schedule.every(5).minute.at(":15").do(digest)
        schedule.every().minute.at(":00").do(self.station.ID)  # debugging
        schedule.every().minute.at(":30").do(self.mixer.digest)

        schedule.every().second.do(self._updateUI)

        self.root = root
        self.root.add_key_command(py_cui.keys.KEY_M_LOWER, self.mixer.mute)
        self.root.add_key_command(py_cui.keys.KEY_M_UPPER, self.mixer.unmute)
        self.root.add_key_command(py_cui.keys.KEY_P_LOWER, self.mixer.pause)
        self.root.add_key_command(py_cui.keys.KEY_P_UPPER, self.mixer.unpause)
        self.root.add_key_command(py_cui.keys.KEY_H_LOWER, self.help)
        self.root.add_key_command(py_cui.keys.KEY_H_UPPER, self.help)
        self.root.add_key_command(py_cui.keys.KEY_Q_LOWER, self.quit)
        self.root.add_key_command(py_cui.keys.KEY_Q_UPPER, self.quit)
        self.root.add_key_command(py_cui.keys.KEY_CTRL_UP, self.mixer.volumeUp)
        self.root.add_key_command(
            py_cui.keys.KEY_CTRL_DOWN, self.mixer.volumeDown)

        self.root.set_status_bar_text(
            "[M]ute [P]ause [CTRL]+[UP/DN]Volume [H]elp [Q]uit - Use arrow keys to navigate. ENTER to focus.")

        self.logConsole = self.root.add_text_block(
            'Station Log', 0, 1, row_span=4, column_span=2)
        self.logConsole.set_focus_text(
            '[HOME] [END] [PGUP] [PGDN] - For more log history check log files. ESC to defocus.')
        self.logConsole.add_text_color_rule(
            ' \[DEBUG\] ', py_cui.BLUE_ON_BLACK, 'contains', match_type='regex')
        self.logConsole.add_text_color_rule(
            ' \[INFO\] ', py_cui.GREEN_ON_BLACK, 'contains', match_type='regex')
        self.logConsole.add_text_color_rule(
            ' \[WARNING\] ', py_cui.YELLOW_ON_BLACK, 'contains', match_type='regex')
        self.logConsole.add_text_color_rule(
            ' \[ERROR\] ', py_cui.RED_ON_BLACK, 'contains', match_type='regex')
        self.logConsole.add_text_color_rule(
            ' \[CRITICAL\] ', py_cui.MAGENTA_ON_BLACK, 'contains', match_type='regex')

        # logging.info("stdout redirected to logConsole.")

        TUIhandler = TUIHandler(self.logConsole)
        TUIhandler.setFormatter(logFormatter)
        rootLogger.addHandler(TUIhandler)

        self.playlist = self.root.add_scroll_menu(
            'Media Queue', 0, 0, row_span=2)
        self.playlist.set_focus_text(
            '[PGUP] [PGDN] [HOME] [END] Rearrange selected item. ENTER to defocus.')
        self.playlist.add_key_command(py_cui.keys.KEY_PAGE_UP, self.itemMoveUp)
        self.playlist.add_key_command(
            py_cui.keys.KEY_PAGE_DOWN, self.itemMoveDown)
        self.playlist.add_key_command(py_cui.keys.KEY_HOME, self.itemMoveTop)
        self.playlist.add_key_command(
            py_cui.keys.KEY_END, self.itemMoveBottom)

        self.mixerStatus = self.root.add_scroll_menu('Mixer', 2, 0)
        self.mixerStatus.set_focus_text('Mixer digest.')

        self.resMonitor = self.root.add_scroll_menu('System Resource', 3, 0)
        self.resMonitor.set_focus_text('System info and resource monitor.')

        #--------------------------------#
        # logConsole keybinding override #
        #--------------------------------#

        def logConsole_handle_key_press(self, key_pressed):
            if key_pressed == py_cui.keys.KEY_LEFT_ARROW:
                self._move_left()
            elif key_pressed == py_cui.keys.KEY_RIGHT_ARROW:
                self._move_right()
            elif key_pressed == py_cui.keys.KEY_UP_ARROW:
                self._move_up()
            # TODO: Fix this janky operation here
            elif key_pressed == py_cui.keys.KEY_DOWN_ARROW and self._cursor_text_pos_y < len(self._text_lines) - 1:
                self._move_down()
            elif key_pressed == py_cui.keys.KEY_HOME:
                self._viewport_y_start = 0
            elif key_pressed == py_cui.keys.KEY_END:
                self._stick_to_bottom()
                self._cursor_text_pos_x = 0
            elif key_pressed == py_cui.keys.KEY_HOME:
                self._viewport_y_start = 0
            elif key_pressed == py_cui.keys.KEY_END:
                self._stick_to_bottom()
                self._cursor_text_pos_x = 0
            elif key_pressed == py_cui.keys.KEY_PAGE_UP:
                h, _ = self.get_viewport_dims()
                if self._viewport_y_start < h:
                    self._viewport_y_start = 0
                else:
                    self._viewport_y_start -= h
            elif key_pressed == py_cui.keys.KEY_PAGE_DOWN:
                h, _ = self.get_viewport_dims()
                lastLineNum = len(self._text_lines)
                if self._viewport_y_start + h >= lastLineNum:
                    self._viewport_y_start = lastLineNum - h
                else:
                    # self._stick_to_bottom()
                    self._viewport_y_start += h

        def logConsole_stick_to_bottom(self):
            h, _ = self.get_viewport_dims()
            lastLineNum = len(self._text_lines)
            if lastLineNum > h:
                self._viewport_y_start = lastLineNum - h

        def logConsolewrite(self, text):
            """Function used for writing text to the text block

            Parameters
            ----------
            text : str
                Text to write to the text block
            """

            lines = text.splitlines()
            if len(self._text_lines) == 1 and self._text_lines[0] == '':
                self.set_text(text)
            else:
                self._text_lines.extend(lines)
            self._stick_to_bottom()  # changed behavior: stick to bottom

        # self.logConsole._handle_key_press = _handle_key_press
        self.logConsole._handle_key_press = types.MethodType(
            logConsole_handle_key_press, self.logConsole)
        self.logConsole._stick_to_bottom = types.MethodType(
            logConsole_stick_to_bottom, self.logConsole)
        self.logConsole.write = types.MethodType(
            logConsolewrite, self.logConsole)
        pass

    def itemMoveUp(self):
        currIdx = self.playlist.get_selected_item_index()
        self.station.playControl.shiftPlayList(currIdx, -1)
        self.playlist.set_selected_item_index(max(currIdx - 1, 0))

    def itemMoveDown(self):
        currIdx = self.playlist.get_selected_item_index()
        self.station.playControl.shiftPlayList(currIdx, +1)
        maxIdx = len(self.playlist._view_items)-1
        self.playlist.set_selected_item_index(min(currIdx + 1, maxIdx))

    def itemMoveTop(self):
        currIdx = self.playlist.get_selected_item_index()
        self.station.playControl.shiftPlayList(currIdx, -currIdx)
        self.playlist.set_selected_item_index(0)

    def itemMoveBottom(self):
        currIdx = self.playlist.get_selected_item_index()
        maxIdx = len(self.playlist._view_items)-1
        self.station.playControl.shiftPlayList(currIdx, maxIdx-currIdx)
        self.playlist.set_selected_item_index(maxIdx)

    def _updateUI(self):
        logging.debug("TUI update")

        status = []
        if self.mixer.muted:
            status.append("[MUTED]")
        if self.mixer.paused:
            status.append("[PAUSED]")
        statusString = ' '.join(status)
        t = datetime.now()
        self.root.set_title(
            '{} {} Broadcast Automation System {}'.format(statusString, STATION_NAME, t.strftime("%b-%d-%Y %H:%M:%S")))

        self.mixer.get_volume()
        mixerDigest = []
        for chan, sound in self.mixer.channelLastPlayed.items():
            mixerDigest.append("[{chan: <10}]  ({vol:>3}%) - {sound}".format(
                chan=chan, vol=int(self.mixer.vol[chan]*100), sound=sound.path))
        oldDigest = self.mixerStatus.get_item_list()
        if oldDigest != mixerDigest:
            self.mixerStatus.clear()
            self.mixerStatus.add_item_list(mixerDigest)


        playIdx = self.playlist.get_selected_item_index()
        q = self.station.playControl.cyclic_queue
        oldPlaylist = self.playlist.get_item_list()
        newPlaylist = ["{:>3}. [{}] {}".format(i+1,s.strDuration(), s.path) for i,s in enumerate(q)]
        if oldPlaylist != newPlaylist:
            self.playlist.clear()
            self.playlist.add_item_list(newPlaylist)
        totalLength = sum([s.duration for s in q])
        self.playlist.set_title("Media Queue ({}) [{}]".format(
            len(q), conversion.floatToHMS(totalLength)))
        self.playlist.set_selected_item_index(playIdx)

    def help(self):
        helpText = "Volume control: CTRL-UP/DN " + \
            "Use lower/uppercase key to toggle flags. " + \
            "e.g. [m] for mute, [M] for unmute"
        self.root.show_message_popup("HELP", helpText)

    def quit(self):
        self.root.show_yes_no_popup("QUIT?", self._quit)

    def _quit(self, confirm: bool):
        if confirm:
            self.root.stop()
