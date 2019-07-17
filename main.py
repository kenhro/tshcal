#!/usr/bin/env python3

import os
import sys
import time
import datetime
import logging
import logging.config

from tshcal.inputs import argparser
from tshcal.commanding import tsh_commands
from tshcal.defaults import ROOT_DIR


def get_logger(log_file):

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
    """delay until start time, s, has been surpassed"""

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


def main():

    # create logger
    log_file = os.path.join(ROOT_DIR, 'logging', 'tshcal.log')
    module_logger = get_logger(log_file)
    module_logger.info('- STARTING MAIN TSHCAL APP - -')
    module_logger.debug('log_file = %s' % log_file)

    # get input arguments
    args = get_inputs(module_logger)

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

    # FIXME do we need to do anything prep/config for ESP here? (e.g. GENERAL MODE SELECTION or STATUS FUNCTIONS...
    # FIXME ...maybe from Table 3.5.1 of ESP301 User Guide or possibly something else)?

    # TODO before delay timer, prompt user with enough info here to enable go/no-go...
    # TODO ... e.g. hit [Enter] if prompted profile looks good OR give user another keypress with chance to retry

    # FIXME flow chart shows 2 delays, but no smarts here yet to verify enough time for TSH temp. settling vs. start

    # delay until start time to begin calibration
    wait_for_start_time(args.start, module_logger)

    # TODO call Will's prototype/template code -- that which actually moves rig and gathers calibration data

    return 0  # return zero for success, which is typical Linux command line behavior


if __name__ == '__main__':

    sys.exit(main())
