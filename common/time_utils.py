#!/usr/bin/env python3

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


if __name__ == '__main__':
    demo_it()
