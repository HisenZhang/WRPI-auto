#------------#
#  STATION   #
#------------#

STATION_NAME = 'WRPI'

#------------#
#   LOGGER   #
#------------#

LOG_FORMAT = "%(asctime)s - %(threadName)-11s - [%(levelname)s] - %(message)s"
# SMTP outgoing email alert
SMTP_ENABLE = False
SMTP_HOST = 'mailserver',
SMTP_FROMADDR = 'noreply@example.com'
SMTP_TOADDRS = ['me@example.com']
SMTP_SUBJECT = '[WRPI-Alert] WRPI Automation Broadcast System Alert'
SMTP_CREDENTIALS = ('user', 'pwd')  # ('user','pwd')
SMTP_SECURE = None  # ('keyfile', 'certificate file'), default None

#------------#
#    PATH    #
#------------#

EXT_BIN_PATH = 'bin'
LIB_BASE = 'lib'

#------------#
#   AUDIO    #
#------------#

# number of channels in virtual mixer. 48 is more than sufficient.
NUM_CHANNEL = 48
# transition time in ms.
TRANSITION_LENGTH = 1000
# how much lower the audio should be when being surpressed (e.g. during a Station ID)
SURPRESSION_FACTOR = 0.3
# format supported
SOUND_FORMAT = ('.mp3', '.wav', '.ogg', 'm4a') # Basically everything ffmpeg supports
# bitrate
BITRATE = '192k'
# loudness in LUFS
LOUDNESS = -23
