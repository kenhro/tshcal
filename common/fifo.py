#!/usr/bin/env python3

import numpy as np
from collections import deque

from tshcal.defaults import TSH_BUFFER_SEC
from tshcal.commanding.tsh_commands import fake_query_tsh_sample_rate


tsh_id = 'tshes-44'
fs = fake_query_tsh_sample_rate(tsh_id)
buff_len = np.int(np.ceil(fs * TSH_BUFFER_SEC))

d = deque(maxlen=buff_len)

for i in range(6):
    d.appendleft(i)

print(d, np.mean(d))
