#------------#
#  STATION   #
#------------#

STATION_NAME = 'WRPI'

#------------#
#   LOGGER   #
#------------#

LOG_FORMAT = "%(asctime)s - %(threadName)-10s [%(levelname)s] %(message)s"
ALERT_FORMAT = """
Message type:   [%(levelname)s]
Time:           %(asctime)s
Location:       %(pathname)s: %(lineno)d
Module:         %(module)s
Thread:         %(threadName)s
Function:       %(funcName)s

Message:

%(message)s
"""
# SMTP outgoing email alert
SMTP_ENABLE = False
SMTP_HOST = ('mailserver', 587)  # ('host', port)
SMTP_SENDER = 'noreply@example.com'
SMTP_RECIPIENTS = ['me@example.com']
SMTP_SUBJECT = '[WRPI-Alert] WRPI Automation Broadcast System Alert'
SMTP_CREDENTIALS = ('user', 'pwd')  # ('user','pwd')

# DISCORD alert
DISCORD_ENABLE = False
DISCORD_WEBHOOK = 'YOUR WEB HOOK HERE'
DISCORD_AGENT = 'AGENT NAME'
DISCORD_RECIPIENTS = ['everyone']

#------------#
#    PATH    #
#------------#

EXT_BIN_PATH = 'bin'
LIB_BASE = 'lib'
LOG_BASE = 'log'

#------------#
#   AUDIO    #
#------------#

# transition time in ms.
TRANSITION_LENGTH = 1000
# how much lower the audio should be when being surpressed (e.g. during a Station ID)
SURPRESSION_FACTOR = 0.3
# format supported
# Basically everything ffmpeg supports
SOUND_FORMAT = ('.mp3', '.wav', '.ogg', '.m4a')
# bitrate
BITRATE = '192k'
# loudness in LUFS
LOUDNESS = -23
# User defined show type. Each type will use an individual channel
USER_CHANNEL = []  # e.g. ['typeA','typeB']
