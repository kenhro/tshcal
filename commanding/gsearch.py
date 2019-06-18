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


class GoldenSectionSearch(object):
    """
    A class used for golden section search to find min/max.

    see https://en.wikipedia.org/wiki/Golden-section_search

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
        self.width = b - a
        self.mean = np.mean([a, b])
        self._max = max  # True to find _max, False to find min
        self._c = b - self.width / self.golden_ratio
        self._d = a + self.width / self.golden_ratio
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
        for tup in zip(['a', 'c', 'd', 'b'], self._gsection):
            s += '  ' + str(tup[0]) + ': '
            s += '{:8.3f}, {:12.9f}'.format(*tup[1])
        s += '  w:{:6.2f}'.format(self.width)  # width of overall interval in degrees
        s += '  m:{:6.2f}'.format(self.mean)   # midpoint of overall interval in degrees
        return s

    def update_section(self):
        """
        Refine interval based on middle-two counts & whether searching for min or max.
        :return: None
        """
        if self._max:
            op = operator.ge  # comparison operator to find max
        else:
            op = operator.lt  # comparison operator to find min
        fc = self._gsection[1][1]
        fd = self._gsection[2][1]
        if op(fc, fd):

            # shift d2b & c2d, keep a, new c        # a c d b << initially
            self._gsection.rotate()                 # b a c d << d2b & c2d
            self._gsection[0] = self._gsection[1]   # a a c d << keep a

            # now recompute 2nd element
            b = self._gsection[-1][0]
            a = self._gsection[0][0]
            c = b - (b - a) / self.golden_ratio
            self._gsection[1] = (c, get_counts(c))  # a N c d << N is the only new pt

        else:

            # shift c2a & d2c, keep b, new d         # a c d b << initially
            self._gsection.rotate(-1)                # c d b a << c2a & d2c
            self._gsection[-1] = self._gsection[-2]  # c d b b << keep b

            # now recompute 3rd element
            b = self._gsection[-1][0]
            a = self._gsection[0][0]
            d = a + (b - a) / self.golden_ratio
            self._gsection[2] = (d, get_counts(d))   # c d N b << N is the only new pt

        self.width = (b - a)
        self.mean = np.mean([a, b])

    def auto_run(self, min_width=0.1, max_iters=25):
        """
        Automatically run with calls to update_section, but stop when width < min_width or iterations > max_iters,
        whichever comes first.

        :param min_width: Float minimum value below which the auto_run method stops (default = 0.1 degrees).
        :param max_iters: Integer maximum number of iterations above which auto_run method stops (default = 25).
        :return: None
        """
        for i in range(max_iters):
            self.update_section()
            print('{}  i:{:3d}'.format(self, i + 1))  # TODO -- maybe a verbosity input to suppress stdout? Regardless, we should be logging!
            if self.width < min_width:
                break


def demo():
    # gs = GoldenSectionSearch(-30, 30, max=True)
    gs = GoldenSectionSearch(150, 210, max=False)
    gs.four_moves_section_init()  # deferred initialization
    print('{}  i:{:3d}'.format(gs, 0))
    gs.auto_run()


if __name__ == '__main__':
    demo()
