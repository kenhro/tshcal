#!/usr/bin/env python

import operator
import numpy as np
from collections import deque


class Point(object):

    def __init__(self, angle, counts):
        self.angle, self.counts = angle, counts

    def __str__(self):
        return "angle:{}, counts:{}".format(self.angle, self.counts)

    def __neg__(self):
        return Point(-self.angle, -self.counts)

    def __add__(self, point):
        return Point(self.angle + point.x, self.counts + point.y)

    def __sub__(self, point):
        return self + -point  # add negative value is what we need here


def dummy_get_counts(adeg):
    from math import cos, radians
    return cos(radians(adeg))


def get_counts(adeg):
    # move to specified angle, adeg, wait for steady state settling, then return counts value
    return dummy_get_counts(adeg)


class GoldenSection(object):
    """
    A class used for golden section search to find min/max.
    see https://en.wikipedia.org/wiki/Golden-section_search

    Attributes
    ----------
    a : float
        The smallest x-value (smallest angle) in search interval.
    b : float
        The largest x-value (largest angle) in search interval.
    max: bool, optional
        A flag, True to find max, or False to find min (default is True to find max).

    Methods
    -------
    four_moves_section_init()
        Deferred initialization of 4-tuple: (angle, counts) for a, c, d, b.
    update_section()
        Decide how to re-partition interval/section for next iteration in search.
    """

    golden_ratio = (1 + np.sqrt(5)) / 2

    def __init__(self, a, b, max=True):
        """
        Parameters
        ----------
        :param a: Initial float for smallest angle in interval being searched.
        :param b: Initial float for largest angle in interval being searched.
        :param max: Boolean True to find max; otherwise, find min.
        """
        self._a = a
        self._b = b
        self._max = max  # True to find _max, False to find min
        self._c = b - (b - a) / self.golden_ratio
        self._d = a + (b - a) / self.golden_ratio
        self._gsection = deque(maxlen=4)  # after we truly initialize _gsection, we always want exactly 4 tuples

    def four_moves_section_init(self):
        """
        For each of 4 angle values in interval, get corresponding counts.
        :return: None
        """
        # we defer this initialization for _gsection because call to get_counts will MOVE THE RIG!
        self._gsection.append((self._a, get_counts(self._a)))
        self._gsection.append((self._c, get_counts(self._c)))
        self._gsection.append((self._d, get_counts(self._d)))
        self._gsection.append((self._b, get_counts(self._b)))

    def __str__(self):
        s = 'GSS(max)' if self._max else 'GSS(min)'
        # 3 digits after decimal pt for angle; 9 for cosine (dummy) value since not yet working with counts
        for tup in zip(['a', 'b', 'c', 'd'], self._gsection):
            s += '  ' + str(tup[0]) + ': '
            s += '{:8.3f}, {:.9f}'.format(*tup[1])
        return s

    def update_section(self):
        """
        Refine interval based on whether searching for min or max and middle-two counts.
        :return: None
        """
        if self._max:
            op = operator.ge  # comparison operator to find max
        else:
            op = operator.lt  # comparison operator to find min
        fc = self._gsection[1][1]
        fd = self._gsection[2][1]
        if op(fc, fd):
            # shift d2b & c2d
            # initially                            # a c d b
            self._gsection.rotate()                # b a c d
            self._gsection[0] = self._gsection[1]  # a a c d
            # now recompute 2nd element
            b = self._gsection[-1][0]
            a = self._gsection[0][0]
            c = b - (b - a) / self.golden_ratio
            self._gsection[1] = (c, get_counts(c))
        else:
            # shift c2a & d2c
            # initially                              # a c d b
            self._gsection.rotate(-1)                # c d b a
            self._gsection[-1] = self._gsection[-2]  # c d b b
            # now recompute 3rd element
            b = self._gsection[-1][0]
            a = self._gsection[0][0]
            d = a + (b - a) / self.golden_ratio
            self._gsection[2] = (d, get_counts(d))


gs = GoldenSection(150, 210, max=False)
# gs = GoldenSection(-30, 30, max=True)
gs.four_moves_section_init()  # section
print(gs)
for _ in range(15):
    gs.update_section()
    print(gs)
