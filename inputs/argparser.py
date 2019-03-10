#!/usr/bin/env python

"""This module utilizes argparse from the standard library to define what arguments are required and handles those with
defaults and logic to help detect avoid invalid arguments."""


import os
import re
import argparse
import logging.config

from defaults import DEFAULT_OUTDIR, DEFAULT_SENSOR, DEFAULT_RATE, DEFAULT_GAIN, ROOT_DIR


def folder_str(f):
    """return string provided only if this folder exists"""
    if not os.path.exists(f):
        raise argparse.ArgumentTypeError('"%s" does not exist, you must create this folder' % f)
    return f


def rate_str(r):
    """return valid sample rate (sa/sec) as int value converted from string, r"""
    try:
        value = int(r)
    except Exception as e:
        raise argparse.ArgumentTypeError('%s' % e)

    # William replace next 2 lines so that we raise error for any input besides our specific TSH-ES sample rates
    # William maybe use "not in" syntax for this
    # William see SAMS-SPC-005 Rev A "SAMS Data & Command Format Definitions: Developers Edition"
    if value < 1 or value > 999:
        raise argparse.ArgumentTypeError('rate, r, in sa/sec must be such that 1 <= r <= 999')

    return value


def gain_str(g):
    """return valid gain as float value converted from string, g"""
    try:
        value = float(g)
    except Exception as e:
        raise argparse.ArgumentTypeError('%s' % e)

    # William replace next 2 lines so that we raise error for any input besides our specific TSH-ES gains
    if value < 1 or value > 999:
        raise argparse.ArgumentTypeError('gain, g, must be such that 1 <= r <= 999')

    return value


def sensor_str(s):
    """return string provided only if it is a valid esXX"""
    # TODO agree on consistent convention of string to refer to sensor (e.g. es09 or tshes-13); which is most prevalent?
    pat = re.compile(r'es\d{2}$', re.IGNORECASE)
    if re.match(pat, s):
        return s.lower()
    else:
        raise argparse.ArgumentError('"%s" does not appear to be a valid string for a TSH (e.g. es09)')


def parse_inputs():
    """parse input arguments using argparse from standard library"""

    parser = argparse.ArgumentParser(description="Command line argument handler for tshcal project's main program.")

    # a group of args for verbosity
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true')
    group.add_argument('-q', '--quiet', action='store_true')

    # sample rate
    help_rate = "sample rate (sa/sec); default = %s" % str(DEFAULT_RATE)
    parser.add_argument('-r', '--rate', default=DEFAULT_RATE, type=rate_str, help=help_rate)

    # gain
    help_gain = "gain; default = %s" % str(DEFAULT_GAIN)
    parser.add_argument('-g', '--gain', default=DEFAULT_GAIN, type=gain_str, help=help_gain)

    # sensor
    help_sensor = "sensor; default is %s" % DEFAULT_SENSOR
    parser.add_argument('-s', '--sensor', default=DEFAULT_SENSOR, type=sensor_str, help=help_sensor)

    # output directory
    help_outdir = 'output dir; default is %s' % DEFAULT_OUTDIR
    parser.add_argument('-o', '--outdir', default=DEFAULT_OUTDIR, type=folder_str, help=help_outdir)

    # start logging
    logging.config.fileConfig(os.path.join(ROOT_DIR, 'logging/log.conf'))  # get logging config info from file
    logger = logging.getLogger('root')
    logger.info('-' * 55)
    logger.info('parsing input arguments')

    # parse
    args = parser.parse_args()

    # show args
    logger.info(str(args).replace('Namespace', 'inputs:'))

    # adjust log level based on verbosity input args
    if args.quiet:
        logger.warning('switching to quiet (WARNING level) logging')
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

    return args


if __name__ == '__main__':

    args = parse_inputs()
