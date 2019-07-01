#!/usr/bin/env python3

import operator
import numpy as np
from collections import deque

from tshcal.commanding.plot_progress import GoalProgressPlot

# next 2 imports (I think) only in dummy calls
from time import sleep
from math import cos, radians


def dummy_move_to_get_counts(a):
    """This is a convenient/dummy function for mimicking cosine profile around min/max values."""
    sleep(0.5)  # this to fake what should be allowed settling time (maybe 60 seconds?)
    return 4_123_456 * cos(radians(a))


def move_rig_get_counts(ax, a, plot_fun=None):
    """Move calibration rig axis to desired absolute angle (i.e. "move roll axis to 89.05 degrees").

    Parameters
    ----------
    ax : str
        The rig axis to be moved: 'yaw', 'pitch', or 'roll'.
    a: float
        The absolute angle (degrees) that we want to drive the given rig axis to.
    plot_fun: plot function (method)
        None for no plotting or...
        an object method:
         e.g. GoalProgressPlot's plot_point or debug_plot_point method
              plot_point: just update plot with (angle, counts) -- no prompts
              debug_plot_point: prompt user with angle BEFORE moving rig

    Returns
    -------
    counts

    """
    # TODO replace dummy call with actual rig control code
    if plot_fun:
        fun_name = plot_fun.__name__
        if fun_name.lower().startswith('debug'):
            ans = input("RIG AXIS = %s, ANGLE = %.3f deg...Type [enter] to step, or [x] exit: " % (ax, a))
            if ans == 'x':
                raise Exception('User aborted RIG AXIS = %s, ANGLE = %.3f' % (ax, a))
        counts = dummy_move_to_get_counts(a)
        plot_fun(a, counts)  # e.g. GoalProgressPlot.plot_point(x, y)
        return counts
    else:
        return dummy_move_to_get_counts(a)


class GoldenSectionSearch(object):
    """
    A class used for golden section search to find min/max within the interval (a, b).

    see https://en.wikipedia.org/wiki/Golden-section_search

    """

    golden_ratio = (1 + np.sqrt(5)) / 2

    def __init__(self, a, b, rig_ax, max=True, plot=None):
        """
        Parameters
        ----------
        :param a: Initial float value for smallest angle in interval being searched.
        :param b: Initial float value for largest angle in interval being searched.
        :param rig_ax: String for which rig axis is being controlled and used to search ('yaw', 'pitch' or 'roll')
        :param max: Boolean True to find max; otherwise, find min.
        :param plot: None for no plotting or an object with these methods:
                     plot_point or debug_plot_point
        """
        self._a = a
        self._b = b
        self.rig_ax = self._set_ax(rig_ax)
        self.width = b - a
        self.mean = np.mean([a, b])
        self._max = max  # True to find max, False to find min
        self.plot = plot  # None for no plot; otherwise object with prescribed methods
        self._buffer = None
        self._c = b - self.width / self.golden_ratio
        self._d = a + self.width / self.golden_ratio
        self._ginterval = deque(maxlen=4)
        self.current_angle = None

    def _set_ax(self, rax):
        """
        Validate and set attribute for rig axis.

        :param rax: String for rig axis ('roll', 'pitch' or 'yaw')
        :return: String (that was validated)
        """
        if rax in ['roll', 'pitch', 'yaw']:
            return rax
        else:
            raise ValueError("invalid input ax ('%s') must be: 'roll', 'pitch' or 'yaw'" % rax)

    def four_initial_moves(self):
        """
        For each of 4 angle values in interval, get corresponding counts.

        :return: None
        """
        # we defer this initialization for interval because calls here will MOVE THE RIG!

        # create first 4 pts for interval
        self._ginterval.append((self._a, move_rig_get_counts(self.rig_ax, self._a, self.plot)))
        self._ginterval.append((self._c, move_rig_get_counts(self.rig_ax, self._c, self.plot)))
        self._ginterval.append((self._d, move_rig_get_counts(self.rig_ax, self._d, self.plot)))
        self._ginterval.append((self._b, move_rig_get_counts(self.rig_ax, self._b, self.plot)))

    def __str__(self):
        s = 'GSS(max)' if self._max else 'GSS(min)'
        # 3 digits after decimal pt for angle; 9 for cosine (dummy) value since not yet working with counts
        for tup in zip(['a', 'c', 'd', 'b'], self._ginterval):
            s += '  ' + str(tup[0]) + ': '
            s += '{:8.3f}, {:12.9f}'.format(*tup[1])
        s += '  w:{:6.2f}'.format(self.width)  # width of overall interval in degrees
        s += '  m:{:6.2f}'.format(self.mean)   # midpoint of overall interval in degrees
        return s

    def get_interval(self):
        return list(self._ginterval)

    def update_interval(self):
        """
        Refine interval based on middle-two counts & whether searching for min or max.
        :return: None
        """

        # establish operator used for comparison based on whether we are searching for min or max
        if self._max:
            op = operator.ge  # comparison operator to find max is "greater than or equal to (ge)", >=
        else:
            op = operator.lt  # comparison operator to find min is "less than (lt)", <

        # get function values (actually, it's counts) at the 2 inner points in the interval
        fc = self._ginterval[1][1]
        fd = self._ginterval[2][1]

        # compare values at 2 inner points in interval
        if op(fc, fd):

            # shift d2b & c2d, keep a, new c                        # a c d b << initial order
            self._ginterval.rotate()                                # b a c d << d2b & c2d
            self._ginterval[0] = self._ginterval[1]                 # a a c d << keep a

            # now recompute 2nd element
            b = self._ginterval[-1][0]
            a = self._ginterval[0][0]
            c = b - (b - a) / self.golden_ratio
            new_point = (c, move_rig_get_counts(self.rig_ax, c, self.plot))
            self._ginterval[1] = new_point                          # a N c d << N is the only new pt

        else:

            # shift c2a & d2c, keep b, new d                        # a c d b << initial order
            self._ginterval.rotate(-1)                              # c d b a << c2a & d2c
            self._ginterval[-1] = self._ginterval[-2]               # c d b b << keep b

            # now recompute 3rd element
            b = self._ginterval[-1][0]
            a = self._ginterval[0][0]
            d = a + (b - a) / self.golden_ratio
            new_point = (d, move_rig_get_counts(self.rig_ax, d, self.plot))
            self._ginterval[2] = new_point                          # c d N b << N is the only new pt

        # recompute width and mean value
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
            self.update_interval()
            # TODO -- maybe a verbosity input to suppress stdout? Regardless, we should be logging!
            print('{}  i:{:3d}'.format(self, i + 1))
            if self.width < min_width:
                break


def demo():

    # get info (mostly from parsing command line args)
    rig_ax = 'pitch'       # decided by which TSH axis working on (need 2 such rig_ax for each TSH axis)
    amin, amax = 150, 210  # if TSH +X, then e.g. pitch range (similar for other rig_ax range)
    is_max = False         # if TSH +X, then True (-X: False, +Y, True, etc.)
    want_to_plot = True    # to be parsed from command line args
    debug_plot = False     # to be parsed from command line args

    # if we want to plot, then need an object to handle plotting our points
    if want_to_plot:

        # initialize and setup plot
        gpp = GoalProgressPlot(rig_ax)
        gpp.setup_plot()

        # choose the method for plotting
        if debug_plot:
            plot_func = gpp.debug_plot_point
        else:
            plot_func = gpp.plot_point

    else:

        plot_func = None

    # run search, which MOVES THE RIG (possibly plot results or prompting user along the way)
    gs = GoldenSectionSearch(amin, amax, rig_ax, max=is_max, plot=plot_func)
    gs.four_initial_moves()
    print('{}  i:{:3d}'.format(gs, 0))
    gs.auto_run()


if __name__ == '__main__':
    demo()
