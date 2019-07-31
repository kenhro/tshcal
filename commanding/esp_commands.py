#!/usr/bin/env python3

import os
import logging
import operator
import numpy as np
from time import sleep
from collections import deque
import matplotlib.pyplot as plt

from newportESP import ESP, Axis
# FIXME refactor to use ESP instead of FakeESP
# from tshcal.tests.fake_esp import FakeESP  # faking ESP object to facilitate the demo code here

from tshcal.defaults import ROUGH_HOMES, DEFAULT_PORT
from tshcal.constants_esp import SAFE_TRAJ_MOVES
from tshcal.constants_esp import TWO_RIG_AX_TO_MOVE, ESP_SETTLE
from tshcal.commanding.plot_progress import GoalProgressPlot
from tshcal.constants_esp import ESP_AX
from tshcal.defaults import TSH_SETTLE_SEC, TSH_BUFFER_SEC
from tshcal.common import buffer


# create logger
module_logger = logging.getLogger('tshcal')


class GoldenSectionSearch(object):
    """
    A class used for golden section search to find min/max within the interval (a, b).

    see https://en.wikipedia.org/wiki/Golden-section_search

    """

    golden_ratio = (1 + np.sqrt(5)) / 2

    def __init__(self, rough_home, tsh, esp, a, b, rig_ax, max=True, plot=None, debug=False):
        """
        Parameters
        ----------
        :param rough_home: string for which rough_home we are nearby
        :param tsh: TSH "data source" object.
        :param esp: Newport ESP motion controller object.
        :param a: Initial float value for smallest angle in interval being searched.
        :param b: Initial float value for largest angle in interval being searched.
        :param rig_ax: String for which rig axis is being controlled and used to search ('yaw', 'pitch' or 'roll')
        :param max: Boolean True to find max; otherwise, find min.
        :param plot: None for no plotting or an object with these methods:
                     plot_point (or debug_plot_point) and set_title
        """
        self.rough_home = rough_home
        self.idx_tsh_ax = self._get_idx_tsh_ax()
        self.tsh = tsh
        self.esp = esp
        self._a = a
        self._b = b
        self.rig_ax = self._set_ax(rig_ax)
        self.width = b - a
        self.mean = np.mean([a, b])
        self._max = max  # True to find max, False to find min
        self.plot = plot  # None for no plot; otherwise object with prescribed methods
        self.debug = debug
        self._buffer = None
        self._c = b - self.width / self.golden_ratio
        self._d = a + self.width / self.golden_ratio
        self._ginterval = deque(maxlen=4)
        self.current_angle = None

    def _get_idx_tsh_ax(self):
        """given rough home (e.g. '+x'), return index for mean(xyz) array"""
        ta = self.rough_home[-1]
        TAS = {'x': 0, 'y': 1, 'z': 2}
        return TAS[ta]

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
        if self.plot:
            self.plot.set_title('doing 1st 4 pts')

        # iterate over pts in this order a, c, d, b
        for pt in [self._a, self._c, self._d, self._b]:
            avg = move_rig_get_counts(self.esp, self.tsh, self.rig_ax, pt, self.idx_tsh_ax, self.plot, debug=self.debug)
            self._ginterval.append((pt, avg))

    def __str__(self):
        s = 'GSS(max)' if self._max else 'GSS(min)'
        for tup in zip(['a', 'c', 'd', 'b'], self._ginterval):
            s += '  ' + str(tup[0]) + ': '
            s += '{:.3f}, {:.4f}'.format(*tup[1])
        s += '  w:{:.2f}'.format(self.width)  # width of overall interval in degrees
        s += '  m:{:.2f}'.format(self.mean)   # midpoint of overall interval in degrees
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
            avg = move_rig_get_counts(self.esp, self.tsh, self.rig_ax, c, self.idx_tsh_ax, self.plot, debug=self.debug)
            new_point = (c, avg)
            self._ginterval[1] = new_point                          # a N c d << N is the only new pt

        else:

            # shift c2a & d2c, keep b, new d                        # a c d b << initial order
            self._ginterval.rotate(-1)                              # c d b a << c2a & d2c
            self._ginterval[-1] = self._ginterval[-2]               # c d b b << keep b

            # now recompute 3rd element
            b = self._ginterval[-1][0]
            a = self._ginterval[0][0]
            d = a + (b - a) / self.golden_ratio
            avg = move_rig_get_counts(self.esp, self.tsh, self.rig_ax, d, self.idx_tsh_ax, self.plot, debug=self.debug)
            new_point = (d, avg)
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
            module_logger.info('{}  i:{:3d}'.format(self, i + 1))
            if np.abs(self.width) < min_width:
                module_logger.info('The abs interval width = %.4f is less than min_width = %.4f, so close enough!? %s' %
                                   (np.abs(self.width), min_width, '<' * 44))
                module_logger.info('GSS yield: {}'.format(self))
                break


def gss_single_rig_ax(rough_home, tsh, esp, rig_ax, amin, amax, is_max, want_to_plot, debug_plot):

    module_logger.info("Near %s, performing GSS for rig_ax = %s, amin = %.4f, amax = %.4f." %
                       (rough_home, rig_ax, amin, amax))

    # if we want to plot, then need an object to handle plotting our points
    if want_to_plot:
        # initialize and setup plot
        gpp = GoalProgressPlot(rig_ax)
        gpp.setup_plot()
        plot_obj = gpp
    else:
        plot_obj = None

    # FIXME we have not incorporated debug_plot feature yet (just going to hard code as debugging for now)

    # run search, which MOVES THE RIG (possibly plot results or prompting user along the way)
    gs = GoldenSectionSearch(rough_home, tsh, esp, amin, amax, rig_ax, max=is_max, plot=plot_obj, debug=debug_plot)
    gs.four_initial_moves()
    module_logger.info('{}  i:{:3d}'.format(gs, 0))
    gs.auto_run()
    plt.close(gpp.fig)


def gss_two_axes(tsh, esp, out_dir, rough_home, want_to_plot=True, debug_plot=False):

    # # FIXME get these info (from parsing command line args?)
    # want_to_plot = True
    # debug_plot = True

    # for given rough home position, get the 2 rig axes/ranges to be moved in succession for finding min/max
    two_rig_ax = TWO_RIG_AX_TO_MOVE[rough_home]
    is_max = not rough_home.startswith('-')  # is_max = True if rough_home starts with minus sign

    module_logger.info('The two rig axes for %s are %s.' % (rough_home, two_rig_ax))

    # find min/max for first of 2 rig axes (run gss on it)
    module_logger.info('Find min/max for 1st of 2 rig axes for %s are %s.' % (rough_home, two_rig_ax))
    rig_ax, amin, amax = two_rig_ax[0]
    gss_single_rig_ax(rough_home, tsh, esp, rig_ax, amin, amax, is_max, want_to_plot, debug_plot)

    # find min/max for 2nd of 2 rig axes (run gss on it)
    module_logger.info('Find min/max for 2nd of 2 rig axes for %s are %s.' % (rough_home, two_rig_ax))
    rig_ax, amin, amax = two_rig_ax[1]
    gss_single_rig_ax(rough_home, tsh, esp, rig_ax, amin, amax, is_max, want_to_plot, debug_plot)

    # FIXME hard coded change in real-time so we don't have to watch paint dry
    # create data buffer
    tsh_buff = buffer.TshAccelBuffer(tsh, 60, logger=module_logger)
    buffer.raw_data_from_socket(tsh.ip, tsh_buff, port=DEFAULT_PORT)  # this populates 2nd arg, buff

    # save data to csv file
    bname = 'axes_tsh' + tsh.name.replace('s', 's-') + '_' + rough_home
    csv_file = os.path.join(out_dir, bname)
    tsh_buff.write_csv_in_counts(csv_file)

    # move to this rough home before going to next rough home pos
    move_to_rough_home(esp, rough_home)


def move_axis(esp, ax, pos, tsh_settle=None, esp_settle=None):
    """return float for actual position after command to move esp axis, ax, to desired angle (in degrees), pos"""

    module_logger.info("Moving ESP axis = %d to pos = %.4f." % (ax, pos))

    # get reference to axis (aka stage here), and turn it on
    stage = esp.axis(ax)
    stage.on()

    # move axis to desired position
    stage.move_to(pos, True)  # if 2nd arg is True, then further execution blocked until move is completed [sorta?]

    # allow stage to settle
    if esp_settle:
        module_logger.info('Let stage settle for %d sec.' % esp_settle)
        sleep(esp_settle)

    # let's look at motor on query
    mons = []
    for m in range(1, 4):
        mons.append(esp.query('MO', m))
    module_logger.info("Motor status: %s." % str(mons))

    # get actual angle achieved from position attribute
    actual_pos = stage.position

    # FIXME for this log entry, we should report position for each axis (R, P, Y) instead of just the one we moved
    module_logger.info("Done moving ESP axis = %d, now ACTUAL pos = %.4f." % (ax, actual_pos))

    # TODO what should we do here if difference between actual and desired position is more than some small tolerance?

    count = 0
    while np.abs(actual_pos - pos) > 0.05:
        count += 1
        if count > 2:
            module_logger.info('Too may reposition attempts, abort.')
            raise Exception('Too may reposition attempts, abort.')

        module_logger.info("Retry #%d moving ESP axis = %d to pos = %.4f." % (count, ax, pos))

        # move axis back a smidge from actual
        stage.on()
        stage.move_to(actual_pos - 1, True)  # if 2nd arg is True, then further execution blocked until move is complete

        # get actual angle achieved from position attribute
        actual_pos = stage.position

        module_logger.info("Done moving ESP axis = %d back a smidge, now ACTUAL pos = %.4f." % (ax, actual_pos))

        # move axis to desired position
        stage.on()
        stage.move_to(pos, True)  # if 2nd arg is True, then further execution blocked until move is completed

        # allow stage to settle
        if esp_settle:
            module_logger.info('Let stage settle for %d sec.' % esp_settle)
            sleep(esp_settle)

        # let's look at motor on query
        mons = []
        for m in range(1, 4):
            mons.append(esp.query('MO', m))
        module_logger.info("Motor status: %s." % str(mons))

        # get actual angle achieved from position attribute
        actual_pos = stage.position

        module_logger.info("Done retry moving ESP axis = %d, now ACTUAL pos = %.4f." % (ax, actual_pos))

    # pause if settle time (in seconds) for tsh is passed in
    if tsh_settle:
        module_logger.info('Pausing %.1f seconds for TSH to settle.' % tsh_settle)
        sleep(tsh_settle)

    return actual_pos


def move_to_rough_home(esp, rig_ax):
    """Move calibration rig to desired rough home position (i.e. "move to TSH +X UP or TSH -Y UP, etc.").

    Parameters
    ----------
    esp : ESP object
          driver for Newport's ESP 301 motion controller.
    rig_ax: str
         designation for rough home position (+x, -x, +y, -y, +z, -z)

    Returns
    -------
    tuple, (r, p, y), of actual positions, which are angles in degrees

    """
    module_logger.info('Go to calibration %s rough home.' % rig_ax)
    roll, pitch, yaw = ROUGH_HOMES[rig_ax]

    # adjust roll, then pitch, then yaw to achieve rough home position
    actual_roll = move_axis(esp, 1, roll)
    actual_pitch = move_axis(esp, 2, pitch)
    actual_yaw = move_axis(esp, 3, yaw)

    module_logger.info('Now at %s rough home, actual RPY = (%.3f, %.3f, %.3f).' %
                       (rig_ax, actual_roll, actual_pitch, actual_yaw))

    return actual_roll, actual_pitch, actual_yaw


def move_to_rough_home_do_gss(tsh, esp, out_dir, rhome, axpos, want_to_plot=True, debug_plot=False):
    """move to rough home, rhome, via (ax, pos) values in axpos tuple"""

    module_logger.info('Go to rough home %s for calibration.' % rhome)

    # iterate over sequence listed in axpos (ax, moves) tuple to get to initial pos
    for ax, pos in axpos:
        actual_pos = move_axis(esp, ax, pos, esp_settle=ESP_SETTLE)

    # currently at rough home, rhome

    # do gss for each of two "other" axes when at this rough home position, rhome
    module_logger.info('Doing gss for %s.' % rhome)  # gss to do data collect, tsh settle & writes
    gss_two_axes(tsh, esp, out_dir, rhome, want_to_plot=want_to_plot, debug_plot=debug_plot)

    # data collection for rhome
    # FIXME we have not gotten to this point yet!


# TODO compare what we had as a rough draft of prototype_routine to refact2 function below
def prototype_routine(m):

    # currently at +x
    # gss for +x
    # data collection

    # move to -z rough home
    actual_pos = move_axis(m, 2, 80)
    '''stage2 = esp.axis(2)
    stage2.on()
    stage2.move_to(80, True)'''
    # currently at -z
    # gss for -z
    # data collection

    # move to +y
    actual_pos = move_axis(m, 3, -90)
    '''stage3 = esp.axis(3)
    stage3.on()
    stage3.move_to(-90, True)'''
    # currently at +y
    # gss for +y
    # data collection

    # move to -x rough home
    actual_pos = move_axis(m, 2, 170)
    '''stage2.move_to(170, True)'''
    # currently at -x
    # gss for -x
    # data collection

    # move to -y
    actual_pos = move_axis(m, 2, -100)
    actual_pos = move_axis(m, 3, -90)
    '''stage2.move_to(-100, True)
    stage3.move_to(-90, True)'''
    # currently at -y
    # gss for -y
    # data collection

    # move to +z
    actual_pos = move_axis(m, 3, 0)
    '''stage3.move_to(0, True)'''
    # currently at +z
    # gss for +z
    # data collection

    # move to +x
    actual_pos = move_axis(m, 2, 0)
    '''stage2.move_to(0, True)'''
    # currently at +x
    # data collection


# TODO compare refact2 function to what we had for rough draft prototype_routine above & see refact3 routine below
def refact2(esp):

    module_logger.info('Go to calibration +x rough home (position 1 of 6).')
    actual_pos = move_axis(esp, 2, 0)
    # currently at +x rough home
    # gss for +x
    # data collection for +x

    module_logger.info('Go to calibration -z rough home (position 2 of 6).')
    actual_pos = move_axis(esp, 2, 80)
    # currently at -z rough home
    # gss for -z
    # data collection for -z

    module_logger.info('Go to calibration +y rough home (position 3 of 6).')
    actual_pos = move_axis(esp, 3, -90)
    # currently at +y rough home
    # gss for +y
    # data collection for +y

    module_logger.info('Go to calibration -x rough home (position 4 of 6).')
    actual_pos = move_axis(esp, 2, 170)
    # currently at -x rough home
    # gss for -x
    # data collection for -x

    module_logger.info('Go to calibration -y rough home (position 5 of 6).')
    actual_pos = move_axis(esp, 2, -100)
    actual_pos = move_axis(esp, 3, -90)
    # currently at -y rough home
    # gss for -y
    # data collection for -y

    module_logger.info('Go to calibration +z rough home (position 6 of 6).')
    actual_pos = move_axis(esp, 3, 0)
    # currently at +z rough home
    # gss for +z
    # data collection for +z

    # move back to +x rough home for convenience
    actual_pos = move_axis(esp, 2, 0)
    module_logger.info('Finished calibration, so park at +x rough home.')


# TODO compare this refact3 function to refact2 routine above as another step toward finalizing in calibration below
def refact3(esp):

    # TODO note we are only doing safe moves, so we only make minimal adjustments...
    # TODO ...it's not good practice to assume other axes are where we want them, but we will for safe-trajectory sake

    # we assume rig starting in home position, so moves below get us from rough home to rough home safely

    move_to_rough_home_do_gss(esp, '+x', [(2, 0)])
    move_to_rough_home(esp, '+x')

    move_to_rough_home_do_gss(esp, '-z', [(2, 80)])
    move_to_rough_home(esp, '-z')

    move_to_rough_home_do_gss(esp, '+y', [(3, -90)])
    move_to_rough_home(esp, '+y')

    move_to_rough_home_do_gss(esp, '-x', [(2, 170)])
    move_to_rough_home(esp, '-x')

    move_to_rough_home_do_gss(esp, '-y', [(2, -100), (3, -90)])
    move_to_rough_home(esp, '-y')

    move_to_rough_home_do_gss(esp, '+z', [(3, 0)])
    move_to_rough_home(esp, '+z')

    # move back to +x rough home for convenience
    move_to_rough_home(esp, '+x')
    module_logger.info('Finished calibration, so park at +x rough home.')


# TODO compare this calibration function to refact3 routine above
def calibration(tsh, esp, out_dir, safe_moves=SAFE_TRAJ_MOVES, want_to_plot=True, debug_plot=False):
    """return status/exit code that results from attempt to run calibration given motion controller object, esp"""

    # iterate over rough homes for cal in safe manner; empirically-derived trajectories that nicely keep cables, etc.
    for rhome, moves in safe_moves:
        move_to_rough_home_do_gss(tsh, esp, out_dir, rhome, moves, want_to_plot=want_to_plot, debug_plot=debug_plot)  # min/max search & write results

    # move back to +x rough home for convenience
    module_logger.info('Finished calibration, so park at +x rough home.')
    move_to_rough_home(esp, '+x')

    # since axis object (an attribute of esp) has an "off" method, we should turn off each axis here
    for iax in range(1, 4):
        esp.axis(iax).off()
        module_logger.info('Powered off ESP axis #%d.' % iax)


def get_tsh_counts(tsh, sec=TSH_BUFFER_SEC):
    """Fill buffer with TSH data, compute mean and return 1x3 array for TSH x-, y- and z-axis.

    Parameters
    ----------
    tsh : obj
        The TSH "data source" object.
    sec : float
        The number of seconds of xyz data to get.

    Returns
    -------
    counts: 1x3 array of floats
        The mean value for each of TSH x-, y- and z-axis.

    """

    module_logger.warning('ASSUMING the TSH is configured (sample rate, gain, and so on).')

    # create data buffer -- at some pt in code before we need mean(counts), probably just after GSS min/max found
    buff = buffer.TshAccelBuffer(tsh, sec, logger=module_logger)
    buffer.raw_data_from_socket(tsh.ip, buff, port=DEFAULT_PORT)  # this populates 2nd arg, buff

    # FIXME should this be median (instead of mean)?
    return np.median(buff.xyz, axis=0)


def move_rig_get_counts(esp, tsh, ax, a, idx_tsh_ax, plot_obj=None, debug=False):
    """Move esp calibration rig's axis, ax, to desired absolute angle, a (i.e. "move roll axis to 89.05 degrees") and
    return average counts after TSH settles at that position.

    Parameters
    ----------
    esp : obj
        The ESP motion controller object.
    tsh : obj
        The TSH "data source" object.
    ax : str
        The rig axis to be moved: 'yaw', 'pitch', or 'roll'.
    a: float
        The absolute angle (degrees) that we want to drive the given rig axis to.
    idx_tsh_ax: int
        Index of which mean value we want 0 for x, 1 for y or 2 for z.
    plot_obj: plot object (with plot_point or debug_plot_point method and set_title method)
        None for no plotting or...
        an object such as:
         e.g. GoalProgressPlot's plot_point or debug_plot_point method
              plot_point: just update plot with (angle, counts) -- no prompts
              debug_plot_point: prompt user with angle BEFORE moving rig
    debug: boolean True if prompt before moving rig; otherwise False

    Returns
    -------
    counts: 1x3 array of floats
        The mean value for each of TSH x-, y- and z-axis.

    """
    if debug:
        ans = input("MOVE RIG AXIS = %s TO ANGLE = %.3f deg?...Type [enter] for Yes, or [x] exit: " % (ax, a))
        module_logger.info('User hit enter.')
        if ans == 'x':
            module_logger.info('User aborted RIG AXIS = %s, ANGLE = %.3f' % (ax, a))
            raise Exception('User aborted RIG AXIS = %s, ANGLE = %.3f' % (ax, a))

    # move rig
    actual_pos = move_axis(esp, ESP_AX[ax], a, tsh_settle=TSH_SETTLE_SEC, esp_settle=ESP_SETTLE)

    # get counts
    avg_counts = get_tsh_counts(tsh)[idx_tsh_ax]

    # FIXME we want a particular element of avg_counts (not all 3 components)
    # send (x, y) = (angle, counts) to plot this point
    if plot_obj:
        plot_obj.plot_point(a, avg_counts)  # e.g. GoalProgressPlot.plot_point(x, y)

    return avg_counts


def run_cal(tsh, out_dir, want_to_plot=True, debug_plot=False):
    """a fake/placeholder for now, but actual code will be fairly simple and probably alot like what's shown here"""

    # open communication with controller
    esp = ESP('/dev/ttyUSB0')

    # run calibration routine
    calibration(tsh, esp, out_dir, want_to_plot=want_to_plot, debug_plot=debug_plot)

def demo_one():

    # open communication with controller
    esp = ESP('/dev/ttyUSB0')
    move_to_rough_home(esp, '-y')


if __name__ == '__main__':
    demo_one()
