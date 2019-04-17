#!/usr/bin/env python3

from subprocess import getoutput
from datetime import datetime, timedelta


def ceil_dtm(dt, tdelta=timedelta(minutes=60)):
    """ return input datetime plus delta

    :param dt: datetime object
    :param tdelta: timedelta object
    :return: dt rounded up to nearest tdelta
    """
    return dt + (datetime.min - dt) % tdelta


def demo_it():
    now = datetime.now()
    print(now)
    print(ceil_dtm(now, timedelta(minutes=30)))


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


if __name__ == '__main__':
    demo_it()
