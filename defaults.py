import os
import datetime
from tshcal.common.time_utils import ceil_dtm

# TODO figure out what makes sense to have defaults for (or not) -- this should be happening as we develop
# TODO find & use most widely used [needed?] convention for "tsh_id": es13, tshes-13, tsh-es13, other?

# ---------------------------------------------------------------------------------------------------------------------
# --- TSH DEFAULTS ----------------------------------------------------------------------------------------------------
# tsh-es parameters (see Tables 18-20 in SAMS-SPC-005 Rev A)
DEFAULT_SENSOR = 'es13'   # use TSH-ES naming convention of "esXX" where XX is S/N digits
DEFAULT_RATE = 250.0      # samples/second
DEFAULT_GAIN = 1          # the value (not the code)
DEFAULT_UNITS = 'counts'  # {counts|volts|ug}
TSH_AX = {'x': 0, 'y': 1, 'z': 2}  # map axis letter to index for TSH axes
TSH_SETTLE_SEC = 0.5   # 5 # amount of time allocated for accelerometer to "settle" after a move & before reading
TSH_BUFFER_SEC = 10  # amount of time to take mean (for example) with calibration find min/max

# ---------------------------------------------------------------------------------------------------------------------
# --- TIME DEFAULTS ---------------------------------------------------------------------------------------------------
# time parameters (start at top of the next hour, but not sooner than 30 minutes from now)
NOW = datetime.datetime.now()
# FIXME with better strategy than this for default start (how relative to when program started or such)?
DEFAULT_START = ceil_dtm(NOW + datetime.timedelta(minutes=30), datetime.timedelta(minutes=60))

# ---------------------------------------------------------------------------------------------------------------------
# --- PATH DEFAULTS ---------------------------------------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))      # project root directory
DEFAULT_OUTDIR = 'c:/temp' if os.name == 'nt' else '/tmp'  # results/output directory

# ---------------------------------------------------------------------------------------------------------------------
# --- PROGRAM DEFAULTS ------------------------------------------------------------------------------------------------
# rough homes dictionary defines 6 approximate starting positions (FIXME does this account for the shim?)
ROUGH_HOMES = {
        # POS   R     P    Y
        '+x':  (0,    0,   0),
        '-x':  (0,  170,   0),
        '+y':  (0,   80, -90),
        '-y':  (0, -100, -90),
        '+z':  (0, -100,   0),
        '-z':  (0,   80,   0),
}
# empirically-derived order for rough homes transition trajectories so that cables and such are nicely kept
NICE_ORDER = ['+x', '-z', '+y', '-x', '-y', '+z']  # this is order with which to visit each rough home pos
