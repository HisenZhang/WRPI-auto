import logging
import logging.handlers
import os
import time
import re
import smtplib
import ssl

from .config import LOG_BASE, LOG_FORMAT, ALERT_FORMAT, SMTP_SENDER, STATION_NAME, SMTP_ENABLE, SMTP_HOST, SMTP_SENDER, SMTP_RECPIENTS, SMTP_SUBJECT, SMTP_CREDENTIALS


class ParallelTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Alternative to TimedRotatingFileHandler: rewrite naming rules. https://stackoverflow.com/a/25387192

    Args:
        logging ([type]): [description]
    """

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, postfix=".log"):

        self.origFileName = filename
        self.when = when.upper()
        self.interval = interval
        self.backupCount = backupCount
        self.utc = utc
        self.atTime = None
        self.postfix = postfix

        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError(
                    "You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError(
                    "Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}$"
        else:
            raise ValueError(
                "Invalid rollover interval specified: %s" % self.when)

        currenttime = int(time.time())
        logging.handlers.BaseRotatingHandler.__init__(
            self, self.calculateFileName(currenttime), 'a', encoding, delay)

        self.extMatch = re.compile(self.extMatch)
        self.interval = self.interval * interval  # multiply by units requested

        self.rolloverAt = self.computeRollover(currenttime)

    def calculateFileName(self, currenttime):
        if self.utc:
            timeTuple = time.gmtime(currenttime)
        else:
            timeTuple = time.localtime(currenttime)

        return self.origFileName + "." + time.strftime(self.suffix, timeTuple) + self.postfix

    def getFilesToDelete(self, newFileName):
        dirName, fName = os.path.split(self.origFileName)
        dName, newFileName = os.path.split(newFileName)

        fileNames = os.listdir(dirName)
        result = []
        prefix = fName + "."
        postfix = self.postfix
        prelen = len(prefix)
        postlen = len(postfix)
        for fileName in fileNames:
            if fileName[:prelen] == prefix and fileName[-postlen:] == postfix and len(fileName)-postlen > prelen and fileName != newFileName:
                suffix = fileName[prelen:len(fileName)-postlen]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[:len(result) - self.backupCount]
        return result

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        currentTime = self.rolloverAt
        newFileName = self.calculateFileName(currentTime)
        newBaseFileName = os.path.abspath(newFileName)
        self.baseFilename = newBaseFileName
        self.mode = 'a'
        self.stream = self._open()

        if self.backupCount > 0:
            for s in self.getFilesToDelete(newFileName):
                try:
                    os.remove(s)
                except:
                    pass

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval

        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt = newRolloverAt - 3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt = newRolloverAt + 3600
        self.rolloverAt = newRolloverAt

class SSLSMTPHandler(logging.handlers.SMTPHandler):
    def emit(self, record):
        """
        Emit a record.
        """
        try:
            context=ssl.create_default_context()

            from email.message import EmailMessage
            msg = EmailMessage()
            msg.set_content(self.format(record))
            msg["Subject"] = self.subject
            msg["From"] = self.fromaddr
            msg["To"] = self.toaddrs

            port = 0
            if self.mailport:
                port = self.mailport
            else:
                port = 587
            with smtplib.SMTP(self.mailhost, port) as smtp:
                smtp.starttls(context=context)
                smtp.login(self.username, self.password)
                smtp.send_message(msg)
                logging.info("Email alert sent.")

        # except (KeyboardInterrupt, SystemExit):
        #     raise
        except Exception as e:
            self.handleError(record)
            logging.critical("Fail to send email alert: "+str(e))

# TODO BufferedEmail for daily digest

logFormatter = logging.Formatter(LOG_FORMAT)
rootLogger = logging.getLogger()
rootLogger.level = logging.INFO

# fileHandler = logging.FileHandler("WRPI.log")
fileHandler = ParallelTimedRotatingFileHandler(
    os.path.join(LOG_BASE, STATION_NAME), postfix='.log', encoding='utf-8', when='midnight', backupCount=0)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

if SMTP_ENABLE:
    smtp_handler = SSLSMTPHandler(mailhost=SMTP_HOST,
                                  fromaddr=SMTP_SENDER,
                                  toaddrs=SMTP_RECPIENTS,
                                  subject=SMTP_SUBJECT,
                                  credentials=SMTP_CREDENTIALS,
                                  )
    smtp_handler.setFormatter(logging.Formatter(ALERT_FORMAT))
    smtp_handler.setLevel(logging.WARNING)
    rootLogger.addHandler(smtp_handler)
