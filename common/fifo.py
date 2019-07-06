#!/usr/bin/env python3

import numpy as np
from collections import deque

from tshcal.defaults import TSH_BUFFER_SEC
from tshcal.commanding.tsh_commands import fake_query_tsh_sample_rate


# FIXME should below few lines be creation (or pass-in) of TSH object? -- something we have not gotten to yet
tsh_id = 'tshes-44'
tsh_ax = 'x'
fs = fake_query_tsh_sample_rate(tsh_id)
tsh_buffer_len = np.int(np.ceil(fs * TSH_BUFFER_SEC))
# FIXME should above few lines be creation (or pass-in) of TSH object? -- something we have not gotten to yet

d = deque(maxlen=tsh_buffer_len)

for i in range(6):
    d.appendleft(i)

print(d, np.mean(d))
