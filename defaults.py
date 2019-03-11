import os
import datetime

# TODO figure out what makes sense to have defaults for (or not)
NOW = datetime.datetime.now()
DEFAULT_START = NOW - datetime.timedelta(microseconds=NOW.microsecond) - datetime.timedelta(minutes=5)
DEFAULT_SENSOR = 'es13'  # use TSH-ES naming convention of "esXX" where XX is S/N digits
DEFAULT_RATE = 100  # cut-off (Hz); see leftmost column Table 18 in SAMS-SPC-005 Rev A
DEFAULT_GAIN = 1  # value (not code); see leftmost column Table 19 in SAMS-SPC-005 Rev A
DEFAULT_UNITS = 'counts'  # {counts|volts|ug} - see leftmost column in Table 20 in SAMS-SPC-005 Rev A

# project root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# output directory (use root to infer this...or you can customize per machine as needed)
if os.name == 'nt':
    # windows
    DEFAULT_OUTDIR = 'c:/temp'
else:
    # linux
    DEFAULT_OUTDIR = '/tmp'
