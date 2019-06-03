#!/usr/bin/env python3

from time import sleep
from threading import Timer
from subprocess import getoutput
from datetime import datetime, timedelta


def ceil_dtm(dt, tdelta=timedelta(minutes=60)):
    """ return input datetime plus delta

    :param dt: datetime object
    :param tdelta: timedelta object
    :return: dt rounded up to nearest tdelta
    """
    return dt + (datetime.min - dt) % tdelta


def unix_to_human_time(utime, alt_format=0):
    """convert Unix time to Human readable time"""
    try:
        fraction = utime - int(utime)
    except OverflowError as err:
        t = 'Unix time %s too long to convert, substituting 0' % utime
        # TODO log this time issue
        print('NEED TO LOG THIS TIME ISUSE:', t)
        fraction = utime = 0
    # handle special case of -1 (not handled correctly by 'date')
    if int(utime == -1):
        return 1969, 12, 31, 23, 59, 59
    cmd = 'date -u -d "1970-01-01 %d sec" +"%%Y %%m %%d %%H %%M %%S"' % int(utime)
    try:
        result = getoutput(cmd)
        # s = split(result)
        s = result.split()
        # s[5] = atoi(s[5]) + fraction
        s[5] = int(s[5]) + fraction
    except ValueError as err:
        t = 'date conversion error\ndate command was: %sdate command returned: %s' % (cmd, result)
        # TODO log this time issue
        print('NEED TO LOG THIS TIME ISUSE:', t)
        raise ValueError(err)
    if alt_format == 1:
        return "%s_%s_%s_%s_%s_%06.3f" % tuple(s)
    elif alt_format == 0:
        return "%s/%s/%s %s:%s:%06.3f" % tuple(s)
    else:  # i.e. alt_format == 2
        s[0:5] = list(map(atoi, s[0:5]))
        return tuple(s)


def human_to_unix_time(month, day, year, hour, minute, second, fraction=0.0):
    """convert Human readable to Unix time"""
    cmd = 'date -u -d "%d/%d/%d %d:%d:%d UTC" +%%s' % tuple((month, day, year, hour, minute, second))
    result = 0
    try:
        result = int(getoutput(cmd)) + fraction
    except ValueError as err:
        t = 'date conversion error\ndate command was: %sdate command returned: %s' % (cmd, result)
        printLog(t)
        raise ValueError(err)
    return result


class RepeatedTimer(object):

    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class BytesCounter(object):

    def __init__(self):
        self.byte_count = 0
        self.start_time = datetime.now()

    def __str__(self):
        b = self.byte_count
        t = self.total_seconds()
        return '%6.2f Bps (bytes = %d, sec = %f)' % (b / t, b, t)

    def total_seconds(self):
        return (datetime.now() - self.start_time).total_seconds()

    def add(self, b):
        self.byte_count += b


def demo_ceil_dtm():
    now = datetime.now()
    print(now)
    print(ceil_dtm(now, timedelta(minutes=30)))


def demo_bytes_counter(interval_sec=60):

    # create object to count bytes (holds cumulative bytes and seconds to give bytes/sec)
    bc = BytesCounter()

    # TODO change print to log via a verbose setting (not just print)

    # start a timer that triggers interval number of seconds and prints bytes/sec info
    print("RepeatedTimer starting (triggers every %d sec)..." % interval_sec)
    rt = RepeatedTimer(interval_sec, print, bc)  # auto-starts here
    try:
        # your long-running job goes here...
        for _ in range(20):
            bc.add(3)
            sleep(3)
    finally:
        print("stopping")
        rt.stop()  # better in a try/finally block to make sure the program ends!

        # 0.99 Bps (bytes = 1790, sec = 1800.162992); LOOP[30*60]; bc.add(1); sleep(1)
        # 1.00 Bps (bytes = 5214, sec = 5220.452299); LOOP[30*60]; bc.add(3); sleep(3)
        # 1.00 Bps (bytes = 1800, sec = 1800.113556); LOOP[5*60];  bc.add(6); sleep(6);
        # 1.00 Bps (bytes = 3600, sec = 3600.306267); LOOP[6*60];  bc.add(10); sleep(10)
        # 1.00 Bps (bytes = 5400, sec = 5400.540904); LOOP[3*60];  bc.add(30); sleep(30);


if __name__ == '__main__':
    demo_ceil_dtm()
    demo_bytes_counter(interval_sec=10)
