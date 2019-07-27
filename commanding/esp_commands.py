#!/home/pims/PycharmProjects/tshcal/venv/bin/python

import logging
import operator
import numpy as np
from collections import deque
from newportESP import ESP, Axis

from tshcal.defaults import ROUGH_HOMES

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


def move_to_rough_home_get_counts(esp, num, rhome, axpos):

    module_logger.info('Go to calibration %s rough home (position %d of 6).' % (rhome, num))
    for ax, pos in axpos:
        actual_pos = move_axis(esp, ax, pos)
    # currently at +x rough home
    # gss for +x
    # data collection for +x


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


# TODO compare refact2 function to what we had for rough draft prototype_routine above & to refact3 routine below
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


# TODO compare this refact3 function to refact2 routine above
def refact3(esp):

    # FIXME it's not good practice to assume other axes are where we want them, so move to absolute RPY, not just R or P or Y

    move_to_rough_home_get_counts(esp, 1, '+x', [(2, 0)])

    move_to_rough_home_get_counts(esp, 2, '-z', [(2, 80)])

    move_to_rough_home_get_counts(esp, 3, '+y', [(3, -90)])

    move_to_rough_home_get_counts(esp, 4, '-x', [(2, 170)])

    move_to_rough_home_get_counts(esp, 5, '-y', [(2, -100), (3, -90)])

    move_to_rough_home_get_counts(esp, 6, '+z', [(3, 0)])

    # move back to +x rough home for convenience
    actual_pos = move_axis(esp, 2, 0)
    module_logger.info('Finished calibration, so park at +x rough home.')


# TODO compare this calibration function to refact3 routine above
def calibration(esp):

    # empirically-derived order for rough homes transition trajectories so that cables and such are nicely kept
    nice_order = ['+x', '-z', '+y', '-x', '-y', '+z']

    # FIXME nice_order should be relocated to defaults & be called CAL_AX_ORDER there and imported like ROUGH_HOMES here

    # iterate over rough homes in nice order as specified
    for ax in nice_order:
        actual_rpy = move_to_rough_home(esp, ax)
        module_logger.info('NOT YET IMPLEMENTED: Do gss for %s.' % ax)  # this will include data collect & write results

    # move back to +x rough home for convenience
    module_logger.info('Finished calibration, so park at +x rough home.')
    actual_rpy = move_to_rough_home(esp, '+x')


def run_cal():

    from tshcal.tests.fake_esp import FakeESP  # faking ESP object to facilitate the demo code here

    # open communication with controller
    esp = FakeESP('/dev/ttyUSB0')

    # run calibration routine
    calibration(esp)


if __name__ == '__main__':
    run_cal()
