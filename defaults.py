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

# rough homes dictionary defines 6 approximate starting positions and accounts for the shim
HOMES = {
        # POS   R  P  Y
        '+x':  (0, 0, 0),
        '-x':  (1, 1, 1),
        '+y':  (2, 2, 2),
        '-y':  (3, 3, 3),
        '+z':  (4, 4, 4),
        '-z':  (5, 5, 5),
}

# ------- Time Constants ------- #

# TSH settling time (in seconds) -- amount of time allocated for accelerometer to "settle" after a move & before reading
TSH_SETTLE_SEC = 3

# TSH acceleration buffer length (in seconds) -- amount of time to take mean (for example) with calibration find min/max
TSH_BUFFER_SEC = 60
