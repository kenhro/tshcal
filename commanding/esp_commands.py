#!/home/pims/PycharmProjects/tshcal/venv/bin/python

import logging
import operator
import numpy as np
from collections import deque
from newportESP import ESP, Axis

# create logger
module_logger = logging.getLogger('tshcal')


def move_axis(esp, ax, pos):
    """return float for actual position after command to move esp axis, ax, to desired angle (in degrees), pos"""

    module_logger.info("Moving ESP axis = %d to pos = %.4f." % (ax, pos))

    # get reference to axis (aka stage here), and turn it on
    stage = esp.axis(ax)
    stage.on()

    # move axis to desired position
    stage.move_to(pos, True)  # if 2nd arg is True, then further execution blocked until move is completed

    # get actual angle achieved from position attribute
    actual_pos = stage.position

    module_logger.info("Done moving ESP axis = %d to ACTUAL pos = %.4f." % (ax, actual_pos))

    # TODO what should we do here if difference between actual and desired position is more than some small tolerance?

    return actual_pos


# TODO compare what we had as a rough draft of prototype_routine to calibration function below
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


# TODO compare this calibration function to what we had as a rough draft of prototype_routine above
def calibration(esp):

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


def run_cal():

    from tshcal.tests.fake_esp import FakeESP  # faking ESP object to facilitate the demo code here

    # open communication with controller
    esp = FakeESP('/dev/ttyUSB0')

    # run calibration routine
    calibration(esp)


if __name__ == '__main__':
    run_cal()
