# $$\      $$\ $$$$$$$\  $$$$$$$\ $$$$$$\        $$$$$$\  $$\   $$\ $$$$$$$$\  $$$$$$\
# $$ | $\  $$ |$$  __$$\ $$  __$$\\_$$  _|      $$  __$$\ $$ |  $$ |\__$$  __|$$  __$$\
# $$ |$$$\ $$ |$$ |  $$ |$$ |  $$ | $$ |        $$ /  $$ |$$ |  $$ |   $$ |   $$ /  $$ |
# $$ $$ $$\$$ |$$$$$$$  |$$$$$$$  | $$ |        $$$$$$$$ |$$ |  $$ |   $$ |   $$ |  $$ |
# $$$$  _$$$$ |$$  __$$< $$  ____/  $$ |        $$  __$$ |$$ |  $$ |   $$ |   $$ |  $$ |
# $$$  / \$$$ |$$ |  $$ |$$ |       $$ |        $$ |  $$ |$$ |  $$ |   $$ |   $$ |  $$ |
# $$  /   \$$ |$$ |  $$ |$$ |     $$$$$$\       $$ |  $$ |\$$$$$$  |   $$ |    $$$$$$  |
# \__/     \__|\__|  \__|\__|     \______|      \__|  \__| \______/    \__|    \______/

# Author: Hisen Zhang <hisen@hisenz.com>

# MIT LICENSE
# Copyright (c) 2012-2021 Scott Chacon and others

# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import time
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from modules import logger  # MUST BE IMPORTED BEFORE ANY OTHER LOGGING MODULES
from modules.station import manager

# Defining station behavior


def routine():
    """Defining station routine.
    """
    try:
        # At startup
        station = manager()
        station.signIn()

        # Register schedule
        station.scheduleInit()

        # loop
        while True:
            station.scheduleRun()
            station.playControl.play('show')
            time.sleep(1)
            pass

    except KeyboardInterrupt:
        logger.rootLogger.warning("KeyboardInterrupt detected.")

    finally:
        station.signOff()


if __name__ == '__main__':
    routine()
