import os
import datetime

# TODO figure out what makes sense to have defaults for (or not)
NOW = datetime.datetime.now()
DEFAULT_START = NOW - datetime.timedelta(microseconds=NOW.microsecond) - datetime.timedelta(minutes=5)
DEFAULT_SENSOR = 'es13'
DEFAULT_RATE = 100
DEFAULT_GAIN = 1

# output directory
if os.name == 'nt':
    DEFAULT_OUTDIR = 'c:/temp'
else:
    DEFAULT_OUTDIR = '/tmp'
