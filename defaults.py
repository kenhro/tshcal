import os
import datetime
from tshcal.common.time_utils import ceil_dtm

# TODO figure out what makes sense to have defaults for (or not)
# TODO find & use most widely used [needed?] convention: es13, tshes-13, tsh-es13, other?

# tsh-es parameters (see Tables 18-20 in SAMS-SPC-005 Rev A)
DEFAULT_SENSOR = 'es13'   # use TSH-ES naming convention of "esXX" where XX is S/N digits
DEFAULT_RATE = 100        # cut-off (Hz)
DEFAULT_GAIN = 1          # value (not code)
DEFAULT_UNITS = 'counts'  # {counts|volts|ug}

# time parameters (start at top of the next hour, but not sooner than 10 minutes from now)
NOW = datetime.datetime.now()
DEFAULT_START = ceil_dtm(NOW + datetime.timedelta(minutes=10), datetime.timedelta(minutes=60))

# project root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# output directory (use root to infer this...or you can customize per machine as needed)
if os.name == 'nt':
    # windows
    DEFAULT_OUTDIR = 'c:/temp'
else:
    # linux
    DEFAULT_OUTDIR = '/tmp'
