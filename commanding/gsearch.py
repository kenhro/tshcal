#!/usr/bin/env python

from math import cos, radians
import numpy as np
from collections import deque


class Point(object):

  def __init__(self, x, y):
    self.x, self.y = x, y

  def __str__(self):
    return "{}, {}".format(self.x, self.y)

  def __neg__(self):
    return Point(-self.x, -self.y)

  def __add__(self, point):
    return Point(self.x+point.x, self.y+point.y)

  def __sub__(self, point):
    return self + -point  # add negative value is what we need here


def get_counts(adeg):
    # move to angle, adeg, wait for steady state, then return counts value
    return cos(radians(adeg))


class GoldenSection(object):

    golden_ratio = (1 + np.sqrt(5)) / 2

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.c = b - (b - a) / self.golden_ratio
        self.d = a + (b - a) / self.golden_ratio
        self.gsection = deque(maxlen=4)  # once we truly initialize, we always want exactly len = 4

    def __str__(self):
        return "a:{:.4f}, c:{:.4f}, d:{:.4f}, b:{:.4f}".format(self.a, self.c, self.d, self.b)

    def init_section(self):
        # we separate this init for section because get_counts will MOVE THE RIG!
        self.gsection.append((self.a, get_counts(self.a)))
        self.gsection.append((self.c, get_counts(self.c)))
        self.gsection.append((self.d, get_counts(self.d)))
        self.gsection.append((self.b, get_counts(self.b)))




# p1 = Point(1, 1)
# p2 = Point(1, 2)
# print(p1)
# print(p2)
# print(p1+p2)
# print(-p2)
# print(p1-p2)

gs = GoldenSection(145, 200)
gs.init_section()  # section
print(gs)
print(gs.gsection)
