#!/home/pims/PycharmProjects/tshcal/venv/bin/python

from newportESP import ESP, Axis
from time import sleep
import operator
import numpy as np
from collections import deque
from tshcal.inputs.argparser import parse_inputs
import logging
logger = logging.getLogger(__name__)

args = parse_inputs()
# raise SystemExit


def dummy_get_counts(a):
    """This is a convenient/dummy function for mimicking cosine profile around min/max values."""
    from math import cos, radians
    return cos(radians(a))


def move_rig_get_counts(ax, a):
    """Move calibration rig axis to desired absolute angle (i.e. "move roll axis to 89.05 degrees").

    Parameters
    ----------
    ax : str
        The rig axis to be moved: 'yaw', 'pitch', or 'roll'.
    a: float
        The absolute angle (degrees) that we want to drive the given rig axis to.

    Returns
    -------
    None

    """

    # TODO replace dummy call with actual rig control code
    # TODO make variable for time to take data "data span"
    # TODO set up socket connection to TSH in order to get 1 min of data
    # TODO take average of the data
    # TODO see GoldenSectionSearch class' _set_ax method for validating rig axis string
    return dummy_get_counts(a)


def move_to_pos(esp, pos):
    """moves axis """
    if pos == '+x':
        (r, p, y) = (0, 0, 0)
    elif pos == '-x':
        (r, p, y) = (0, 170, 0)
    elif pos == '+y':
        (r, p, y) = (0, 80, -90)
    elif pos == '-y':
        (r, p, y) = (0, -100, -90)
    elif pos == '+z':
        (r, p, y) = (0, -100, 0)
    elif pos == '-z':
        (r, p, y) = (0, 80, 0)
    else:
        logging.log(logging.ERROR, "unknown axis:" + pos)
        raise SystemExit

    logging.log(logging.INFO, "start move to " + str(r) + '.')
    stage1 = esp.axis(1)
    stage1.on()
    stage1.move_to(r, True)
    logging.log(logging.INFO, "done move to " + str(r) + '.')

    logging.log(logging.INFO, "start move to " + str(p) + '.')
    stage2 = esp.axis(2)
    stage2.on()
    stage2.move_to(p, True)
    logging.log(logging.INFO, "done move to " + str(p) + '.')

    logging.log(logging.INFO, "start move to " + str(y) + '.')
    stage3 = esp.axis(3)
    stage3.on()
    stage3.move_to(y, True)
    logging.log(logging.INFO, "done move to " + str(y) + '.')

    logging.log(logging.INFO, "moved to " + pos + '.')


def fake_move_to(p):
    print(p)


def move_axis(esp, ax, pos):
    """return float for actual position after trying to move axis, ax, of esp object to desired pos, angle in degrees"""

    # get reference to axis (aka stage), and turn it on
    stage = esp.axis(ax)
    stage.on()

    # move axis to desired position
    stage.move_to(pos, True)

    # query for actual position achieved
    actual_pos = stage.position

    return actual_pos


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


def move_to_rough_home(esp, pos):
    """Move calibration rig to desired rough home position (i.e. "move to TSH +X UP or TSH -Y UP, etc.").

    Parameters
    ----------
    esp : ESP object
          driver for Newport's ESP 301 motion controller.
    pos: str
         designation for rough home position (+x, -x, +y, -y, +z, -z)

    Returns
    -------
    None

    """
    r = {'+x': 0, '-x': 0, '+y': 0, '-y': 0, '+z': 0, '-z': 0}
    p = {'+x': 0, '-x': 170, '+y': 80, '-y': -100, '+z': -100, '-z': 80}
    y = {'+x': 0, '-x': 0, '+y': -90, '-y': -90, '+z': 0, '-z': 0}

    '''logging.log(logging.ERROR, "unknown axis:" + pos)
    raise SystemExit'''
    stage1 = esp.axis(1)
    stage1.on()
    # stage1.move_to(r[pos], True)
    fake_move_to(r[pos], True)
    raise SystemExit

    stage2 = esp.axis(2)
    stage2.on()
    stage2.move_to(p[pos], True)

    stage3 = esp.axis(3)
    stage3.on()
    stage3.move_to(y[pos], True)
    logging.log(logging.INFO, "moved to " + pos + '.')


def demo():
    # gs = GoldenSectionSearch(-30, 30, max=True)
    gs = GoldenSectionSearch(150, 210, 'pitch', max=False)
    gs.four_initial_moves()
    print('{}  i:{:3d}'.format(gs, 0))
    gs.auto_run()


class GoldenSectionSearch(object):
    """
    A class used for golden section search to find min/max within the interval (a, b).

    see https://en.wikipedia.org/wiki/Golden-section_search

    """

    golden_ratio = (1 + np.sqrt(5)) / 2

    def __init__(self, a, b, ax, max=True):
        """
        Parameters
        ----------
        :param a: Initial float value for smallest angle in interval being searched.
        :param b: Initial float value for largest angle in interval being searched.
        :param ax: String for which rig axis is being controlled and used to search ('yaw', 'pitch' or 'roll')
        :param max: Boolean True to find max; otherwise, find min.
        """
        self._a = a
        self._b = b
        self.ax = self._set_ax(ax)
        self.width = b - a
        self.mean = np.mean([a, b])
        self._c = b - self.width / self.golden_ratio
        self._d = a + self.width / self.golden_ratio
        self._ginterval = deque(maxlen=4)

    def _set_ax(self, ax):
        """
        Validate and set attribute for rig axis.

        :param ax: String for rig axis ('roll', 'pitch' or 'yaw')
        :return: String (that was validated)
        """
        if ax in ['roll', 'pitch', 'yaw']:
            return ax
        else:
            raise ValueError("invalid input ax ('%s') must be: 'roll', 'pitch' or 'yaw'" % ax)

    def four_initial_moves(self):
        """
        For each of 4 angle values in interval, get corresponding counts.

        :return: None
        """
        # we defer this initialization for _gsection because call to get_counts will MOVE THE RIG!
        self._ginterval.append((self._a, move_rig_get_counts(self.ax, self._a)))
        self._ginterval.append((self._c, move_rig_get_counts(self.ax, self._c)))
        self._ginterval.append((self._d, move_rig_get_counts(self.ax, self._d)))
        self._ginterval.append((self._b, move_rig_get_counts(self.ax, self._b)))

    def __str__(self):
        s = 'GSS(max)' if self.max else 'GSS(min)'
        # 3 digits after decimal pt for angle; 9 for cosine (dummy) value since not yet working with counts
        for tup in zip(['a', 'c', 'd', 'b'], self._ginterval):
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
            # HOMES
            # shift d2b & c2d, keep a, new c                        # a c d b << initial order
            self._ginterval.rotate()                                # b a c d << d2b & c2d
            self._ginterval[0] = self._ginterval[1]                 # a a c d << keep a

            # now recompute 2nd element
            b = self._ginterval[-1][0]
            a = self._ginterval[0][0]
            c = b - (b - a) / self.golden_ratio
            self._ginterval[1] = (c, move_rig_get_counts(self.ax, c))  # a N c d << N is the only new pt

        else:

            # shift c2a & d2c, keep b, new d                        # a c d b << initial order
            self._ginterval.rotate(-1)                              # c d b a << c2a & d2c
            self._ginterval[-1] = self._ginterval[-2]               # c d b b << keep b

            # now recompute 3rd element
            b = self._ginterval[-1][0]
            a = self._ginterval[0][0]
            d = a + (b - a) / self.golden_ratio
            self._ginterval[2] = (d, move_rig_get_counts(self.ax, d))  # c d N b << N is the only new pt

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
            self.update_section()
            # TODO -- maybe a verbosity input to suppress stdout? Regardless, we should be logging!
            print('{}  i:{:3d}'.format(self, i + 1))
            if self.width < min_width:
                break


if __name__ == '__main__':

    import logging.config
    logging.config.fileConfig('/home/pims/dev/tshcal/logging/log.conf')

    esp = ESP('/dev/ttyUSB0')  # open communication with controller

    # taking measurements

    axis = {'+x', '-x', '+y', '-y', '+z', '-z'}

    esp.axis(1).on()
    esp.axis(2).on()
    esp.axis(3).on()
    # Axis.query(position(self=esp))
    # print(Axis.query())
    # print(esp.axis(1).position)

    prototype_routine(esp)

    '''for item in axis:
        move_to_rough_home(esp, item)
        print(esp.axis(1).position)
        print(esp.axis(2).position)
        print(esp.axis(3).position)'''

    # demo()

    # move_to_pos(esp, "-z")
    # print("a tuple " + str(item))

    """stage = esp.axis(1)        # open axis no 1
    print(stage.id)
    stage.on()
    print(stage.position)# print stage ID
    stage.move_by(-5, True)
    print(stage.position)
    stage.move_by(5, True)
    print(stage.position)# print stage ID"""