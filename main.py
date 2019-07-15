#!/usr/bin/env python3

import os
import sys
import logging
import logging.config

from tshcal.inputs import argparser
from tshcal.commanding import tsh_commands
from tshcal.defaults import ROOT_DIR

# create logger
log_file = os.path.join(ROOT_DIR, 'logging', 'tshcal.log')
module_logger = logging.getLogger('main')
module_logger.setLevel(logging.DEBUG)

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
module_logger.addHandler(fh)
module_logger.addHandler(ch)

module_logger.info('-' * 55)
module_logger.info('log_file = %s' % log_file)


def get_inputs():

    # parse arguments
    module_logger.info('parsing input arguments')
    args = argparser.parse_inputs()
    module_logger.info(str(args).replace('Namespace', 'inputs:'))

    # adjust log level based on verbosity input args
    if args.quiet:
        module_logger.warning('switching to quiet for logging (switch to WARNING level)')
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


def main():

    # create logger
    

    # get input arguments
    args = get_inputs()

    # set tsh parameters
    tsh_state_desired = tsh_commands.set_tsh_state(args)

    # get and verify tsh parameters
    tsh_state_actual = tsh_commands.get_tsh_state()
    if tsh_state_actual == tsh_state_desired:
        module_logger.info('tsh actual state matches desired')
    else:
        module_logger.info('tsh actual state does NOT match desired')

    return 0  # return zero for success


if __name__ == '__main__':

    sys.exit(main())
