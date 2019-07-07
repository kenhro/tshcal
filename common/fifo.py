#!/usr/bin/env python3

import numpy as np
from time import sleep
from collections import deque

from tshcal.defaults import TSH_BUFFER_SEC, TSH_SETTLE_SEC, TSH_AX
from tshcal.commanding.tsh_commands import fake_query_tsh_sample_rate

# a = np.nan * np.zeros((9, 3))
# print(a)
# raise SystemExit

np.random.seed(42)  # for repeatable random values


def fake_tsh_accel_data(size=(5, 3)):
    """return array of specified size with random values and y and z scaled down"""
    xyz = np.random.randint(4_000_000, 4_123_456, size=size)  # underscores for better readability (ignored by Python)
    xyz[:, 1] = xyz[:, 1] / 2.0
    xyz[:, 2] = xyz[:, 2] / 4.0
    return xyz


# FIXME should next few lines be Tsh or TshAccelData object? -- something we have not gotten to yet
tsh_id = 'tshes-44'  # tsh id can vary (e.g. TSH-ES 19, tshes-19, etc.) but let's pick/stick with one for tshcal code
tsh_ax = 'z'
fs = fake_query_tsh_sample_rate(tsh_id)
tsh_buffer_len = np.int(np.ceil(fs * TSH_BUFFER_SEC))
# FIXME should previous few lines be Tsh or TshAccelData object? -- something we have not gotten to yet

# pretend this line is final move to "max count" resting position, so now need TSH settling time
print('sleeping for TSH_SETTLE_SEC = %d' % TSH_SETTLE_SEC)  # TODO make this log entry
sleep(TSH_SETTLE_SEC)

# FIXME following lines for demo of filling TSH_BUFFER_SEC, then getting mean and std dev values
d = deque(maxlen=tsh_buffer_len)  # this is our data buffer for a TSH axis' acceleration values
is_buffer_full = False

# map tsh axis letter to (column) index
idx = TSH_AX[tsh_ax]  # e.g. tsh_ax = 'x' --> idx = 0

# fill buffer incrementally until we completely fill buffer
print('collecting %d seconds of TSH data' % TSH_BUFFER_SEC)
while not is_buffer_full:
    xyz = fake_tsh_accel_data(size=(tsh_buffer_len // 5 - 10, 3))  # demo: chose size not to be multiple of buffer len
    d.extend(xyz[:, idx])
    # print(len(d))
    is_buffer_full = len(d) >= tsh_buffer_len  # we now have num pts corresponding to TSH_BUFFER_SEC

# TODO an improved version of following lines should show up in log (plus in Eric spreadsheet format too)
print('%s %s-axis mean = %13.4f counts' % (tsh_id, tsh_ax, np.mean(d)))
print('%s %s-axis std  = %13.4f counts' % (tsh_id, tsh_ax, np.std(d)))

# using np.random.seed(42) at top of this module gives following, repeatable values:
#
# TSH X-axis mean =  4061474.1967 counts
# TSH X-axis std  =    35753.3989 counts
#
# TSH Y-axis mean =  2030850.3560 counts
# TSH Y-axis std  =    17979.9049 counts
#
# TSH Z-axis mean =  1015399.8815 counts
# TSH Z-axis std  =     8907.1709 counts
