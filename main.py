#!/usr/bin/env python3

import os
import sys
import time
import datetime
import logging
import logging.config
import numpy as np

from tshcal.inputs import argparser
from tshcal.commanding import tsh_commands
from tshcal.commanding import esp_commands
from tshcal.common import buffer
from tshcal.defaults import ROOT_DIR, DEFAULT_PORT
from tshcal.common.buffer import Tsh, raw_data_from_socket


def get_logger(log_file):
    """return logger object with both stream and file handlers, the latter using log_file"""

    # create logger
    logger = logging.getLogger('tshcal')
    logger.setLevel(logging.DEBUG)

    # create file handler which logs to DEBUG level
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)  # changed from ERROR to INFO

    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s : %(lineno)d - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def get_inputs(module_logger):
    """return arguments parsed from command line and make log entries"""

    # parse arguments
    module_logger.debug('parsing input arguments')
    args = argparser.parse_inputs()
    module_logger.info(str(args).replace('Namespace', 'Inputs: '))

    # adjust log level based on verbosity input args
    if args.quiet:
        module_logger.warning('Now switching to quiet for logging, that is, log level = WARNING.')
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    # switch to same level for all handlers
    module_logger.setLevel(level)
    for handler in module_logger.handlers:
        handler.setLevel(level)

    return args


def wait_for_start_time(s, mod_logger):
    """delay until start time, s, has been surpassed; log via mod_logger"""

    # TODO make more user-friendly; e.g. prompt/update every 10sec with time remaining to start & a chance to abort

    # FIXME below lines are development/debug "if False" mechanism used so I am not waiting during code development
    # ----- WHEN READY GET RID OF if False PRETEXT AND UNINDENT THE OTHER LINES OF CODE TO DEPLOY ACTUAL DELAY -----
    if False:
        now = datetime.datetime.now()
        if s <= now:
            raise RuntimeError('not enough delay in start time, use more of a delay until start time')

        while now < s:
            time.sleep(10)  # wait 10 seconds
            now = datetime.datetime.now()

        mod_logger.info('The calibration start time, %s, has been reached.  Begin calibrating now.' % s)
    # ----- WHEN READY GET RID OF if False PRETEXT AND UNINDENT THE OTHER LINES OF CODE TO DEPLOY ACTUAL DELAY -----

    mod_logger.info('Faking that the calibration start time, %s, has been reached.  Begin calibrating now.' % s)


def get_tsh_buffer_summary(tsh, sec=3, logger=None):
    """this does not much beyond demonstrate instantiation of TshAccelBuffer with logging"""

    # FIXME significant parts of this function are for quick demo purposes only, so scrub and fix

    logger.info('Capturing quick data summary from tsh...')

    # create data buffer
    buff = buffer.TshAccelBuffer(tsh, sec, logger=logger)
    raw_data_from_socket(tsh.ip, buff, port=DEFAULT_PORT)  # this populates 2nd arg, buff

    logger.debug('Done capturing quick data summary from tsh.')

    # FIXME should we do something smart about units?
    s = 'QUICK SUMMARY...Mean: X = {:.3f}, Y = {:.3f}, Z = {:.3f} [units]'.format(*np.mean(buff.xyz, axis=0))
    s += ' <-' * 17
    return s


def main(want_to_plot=True, debug_plot=True):
    """return status/exit code that results from running main tshcal application"""

    # create logger
    log_file = os.path.join(ROOT_DIR, 'logging', 'tshcal.log')
    module_logger = get_logger(log_file)
    module_logger.info('- STARTING MAIN TSHCAL APP - - - - - - - - - - - - - - - - - - - - - -')
    module_logger.debug('log_file = %s' % log_file)

    # get input arguments
    args = get_inputs(module_logger)

    # FIXME design better tsh class to give more robustness (with commanding to set/get sample rate, gain, units, etc.)
    # create tsh object
    tsh = Tsh(args.sensor, args.rate, args.gain)

    # FIXME verify the tsh object we created given desired input args matches what's physically hooked up

    # set tsh parameters
    tsh_state_desired = tsh_commands.set_tsh_state(args)

    # get tsh parameters
    tsh_state_actual = tsh_commands.get_tsh_state()

    # verify tsh parameters
    if tsh_state_actual == tsh_state_desired:
        module_logger.debug('The tsh actual state matches our desired state.')
    else:
        # TODO give more info here -- what exactly does not match?
        raise AssertionError('The tsh actual state does NOT match our desired state.')

    # create buffer to capture few seconds' worth of TSH data and show user summary of what we got
    summary = get_tsh_buffer_summary(tsh, sec=3, logger=module_logger)

    # show/log summary
    module_logger.info(summary)

    # FIXME Do we need to do anything prep/config for ESP here? (e.g. GENERAL MODE SELECTION or STATUS FUNCTIONS...
    # FIXME ...maybe from Table 3.5.1 of ESP301 User Guide or possibly something else)?  Will may have answered this?

    # FIXME before any motion begins, our safe trajectories ASSUME starting in home position; prompt user to verify home

    # FIXME Before delay timer, prompt user with enough info here to enable a go/no-go answer...
    # FIXME ... e.g. hit [Enter] if prompted-profile looks good OR give another keypress with chance to retry or...?
    # FIXME ** This should include whether or not debug/prompt-along-way is going to happen or not [auto- or semi-auto?]

    # FIXME our flow chart shows 2 delays, but no smarts here yet to verify enough time for TSH temperature settling

    # delay until start time to begin calibration
    wait_for_start_time(args.start, module_logger)

    # run calibration routine
    esp_commands.run_cal(tsh, args.outdir, want_to_plot=want_to_plot, debug_plot=debug_plot)

    # FIXME are there any commands we need to send to TSH at this point after running calibration?

    module_logger.info('- - - Calibration Complete - - - - - - - - - - - - - - - - - - - - - -')

    return 0  # return zero for success (typical Linux command line behavior)


if __name__ == '__main__':

    sys.exit(main(want_to_plot=True, debug_plot=False))
