#!/usr/bin/env python3

"""
This is demo code to:

(1) show 2 options for moving to rough home positions (dictionary is improvement as it takes basically hard-coded
    position information and moves it up/out and more toward collecting all such info into common/config location)

(2) show refactored code -- pull repeated patterns of code out to higher-level abstract version
"""

from tshcal.tests.fake_esp import FakeESP  # faking it to facilitate the demo here
from tshcal.inputs import HOMES  # go see content of __init__.py file in tshcal's "inputs" directory...maybe our config?


#######################################################################################################################
# Option 1 -- branch via dictionary
def go_to_rough_home(esp, pos):
    """
    return actual position after moving rig to approximate, rough home position

    :param esp: NewportESP object for controller
    :param pos: tuple (r, p, y) for desired position
    :return: two (r, p, y) tuples; (1) desired, and (2) actual position
    """
    desired_rpy = HOMES[pos]  # use dictionary, HOMES, that we imported from (basically) a "config" file
    actual_rpy = rpy_move(esp, desired_rpy)
    return desired_rpy, actual_rpy


#######################################################################################################################
# Option 2 (similar to Will's original code) -- this uses an if/else pattern
def go_to_rough_home_via_ifelse(esp, pos):
    """
    return actual position after moving rig to approximate, rough home position (via if/else pattern)

    :param esp: NewportESP object for controller
    :param pos: tuple (r, p, y) for desired position
    :return: two (r, p, y) tuples; (1) desired, and (2) actual position
    """
    if pos == '+x':
        desired_rpy = (0, 0, 0)
    elif pos == '-x':
        desired_rpy = (1, 1, 1)

    elif pos == '+y':
        desired_rpy = (2, 2, 2)
    elif pos == '-y':
        desired_rpy = (3, 3, 3)

    elif pos == '+z':
        desired_rpy = (4, 4, 4)
    elif pos == '-z':
        desired_rpy = (5, 5, 5)

    else:
        raise Exception('unhandled pos %s' % pos)

    actual_rpy = rpy_move(esp, desired_rpy)

    return desired_rpy, actual_rpy


def rpy_move(esp, rpy):
    """
    return (r, p, y) tuple of actual position after attempt to move to input (desired) position

    :param esp: NewportESP object for controller
    :param rpy: (r, p, y) tuple for desired position
    :return: (r, p, y) tuple for actual position
    """
    # TODO Do you see how the combo of this function with stage_move recognizes original repeat/pattern and refactors?
    # TODO Realize if/when you do more and more programming you will get better at recognizing and refactoring.
    # TODO Realize that refactoring comes after first pass that creates the repeats/pattern.
    actual_ax1 = stage_move(esp, 1, rpy[0])  # roll
    actual_ax2 = stage_move(esp, 2, rpy[1])  # pitch
    actual_ax3 = stage_move(esp, 3, rpy[2])  # yaw
    return actual_ax1, actual_ax2, actual_ax3


def stage_move(esp, ax, angle):
    """
    return float for actual angle achieved after moving ESP stage (axis) to input (desired) angle

    :param esp: NewportESP object for controller
    :param ax: integer index of which ESP stage is to be moved (1, 2 or 3)
    :param angle: float for desired angle to move to
    :return: float for actual angle achieved after moving ESP stage (axis)
    """
    # FIXME include provision to prompt user with move about to make before making it (with option to by-pass prompt)
    # FIXME log moves here with 2 consecutive lines in log file for easy comparison of RPY values (desired vs. actual)
    stage = esp.axis(ax)  # open esp axis, ax, number: 1, 2 or 3
    stage.move_to(angle)  # move to this angle
    actual = angle        # TODO replace this with result from query to get actual angle achieved

    # TODO think about things we might do if "actual not close enough to desired" (maybe just abort!?)

    return actual


def main_example():
    """create esp controller object and use it to drive rig to -x rough home position"""
    esp = FakeESP('/fake/ttyUSB0')
    desired_rpy, actual_rpy = go_to_rough_home(esp, '-x')  # improved implementation of "go_to_rough_home_via_ifelse"
    print('desired RPY =', desired_rpy)
    print('actual  RPY =', actual_rpy)


if __name__ == '__main__':
    main_example()
