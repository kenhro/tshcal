#!/usr/bin/env python3

"""This module utilizes argparse from the standard library to define what arguments are required and handles those with
defaults and logic to help detect avoid invalid arguments."""


import os
import re
import logging
import argparse
from dateutil import parser as dparser

from tshcal.defaults import DEFAULT_OUTDIR
from tshcal.defaults import DEFAULT_SENSOR, DEFAULT_RATE, DEFAULT_GAIN
from tshcal.defaults import DEFAULT_START


# create logger
module_logger = logging.getLogger('tshcal')


def folder_str(f):
    """return string provided only if this folder exists"""
    if not os.path.exists(f):
        raise argparse.ArgumentTypeError('"%s" does not exist, you must create this folder' % f)
    return f


def outdir_str(d):
    """return string provided only if this folder exists and we can create logs subdir in it"""
    f = folder_str(d)
    logs_dir = os.path.join(f, 'logs')
    try:
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
    except OSError:
        raise argparse.ArgumentTypeError('could not create "%s" directory for logs' % logs_dir)
    return f


def rate_str(r):
    """return valid sample rate (sa/sec) as float value converted from string, r"""
    try:
        value = float(r)
    except Exception as e:
        raise argparse.ArgumentTypeError('%s' % e)

    # FIXME replace next 2 lines so that we raise error for any input besides our specific TSH-ES sample rates
    # FIXME maybe use "not in" syntax for this
    # FIXME see SAMS-SPC-005 Rev A "SAMS Data & Command Format Definitions: Developers Edition"
    if value < 1 or value > 999:
        raise argparse.ArgumentTypeError('rate, r, in sa/sec must be such that 1 <= r <= 999')

    return value


def gain_str(g):
    """return valid gain as float value converted from string, g"""
    try:
        value = float(g)
    except Exception as e:
        raise argparse.ArgumentTypeError('%s' % e)

    # TODO replace next 2 lines so that we raise error for any input besides our specific TSH-ES gains
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


def start_str(t):
    """ return string provided only if it is a valid time at least 30 minutes from now

    :param t: string for time to start
    :return: string for time to start
    """
    return dparser.parse(t)


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

    # output directory (mainly for csv output files)
    help_outdir = 'output dir; default is %s' % DEFAULT_OUTDIR
    parser.add_argument('-o', '--outdir', default=DEFAULT_OUTDIR, type=outdir_str, help=help_outdir)

    # start time
    help_start = 'start time; default is %s' % DEFAULT_START
    parser.add_argument('-t', '--start', default=DEFAULT_START, type=start_str, help=help_start)

    # fake ESP
    parser.add_argument('--fake_esp', dest='fake_esp', action='store_true')
    parser.add_argument('--real_esp', dest='fake_esp', action='store_false')

    # fake TSH
    parser.add_argument('--fake_tsh', dest='fake_tsh', action='store_true')
    parser.add_argument('--real_tsh', dest='fake_tsh', action='store_false')

    # want plot
    parser.add_argument('--plot', dest='plot', action='store_true')
    parser.add_argument('--no_plot', dest='plot', action='store_false')

    # debug mode
    parser.add_argument('--debug', dest='debug', action='store_true')
    parser.add_argument('--no_debug', dest='debug', action='store_false')

    # set defaults for some booleans (done in canonical fashion)
    parser.set_defaults(fake_esp=False, fake_tsh=False, plot=True, debug=False)

    # FIXME we do not check that log directory seen in log_conf_file matches relative to outdir, assumed this above

    # parse arguments
    module_logger.debug('calling parse_args')
    args = parser.parse_args()

    return args
