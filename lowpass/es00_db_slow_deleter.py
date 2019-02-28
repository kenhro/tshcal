#!/usr/bin/env python

import time
import pandas as pd
from lowpass import sqlConnect

sec = 1
freq = '%dS' % sec

dr = pd.date_range(start='2017-01-03 15:00', end='2017-01-03 16:00', freq=freq)

i = -1
for _ in range(len(dr)):
    query_str = "delete from es00 where time > unix_timestamp('%s');" % dr[i]
    print(query_str)
    results = sqlConnect(query_str)
    i -= 1
    time.sleep(sec)
