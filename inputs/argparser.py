#!/usr/bin/env python

"""This module utilizes argparse from the standard library to define what arguments are required and handles how to
parse those from sys.argv.  The argparse module automatically generates help and usage messages and issues errors
when users give the program invalid arguments."""


import os
import re
import datetime
import argparse


# TODO consolidate defaults in a defaults module or directory
_NOW = datetime.datetime.now()
_DEFAULT_START = _NOW - datetime.timedelta(microseconds=_NOW.microsecond) - datetime.timedelta(minutes=5)
_DEFAULT_OUTDIR = '/tmp'

# TODO figure out if/what makes sense to have defaults or not
_DEFAULT_SENSOR = 'es13'
_DEFAULT_RATE = 100


def folder_str(f):
    """return string provided only if this folder exists"""
    if not os.path.exists(f):
        raise argparse.ArgumentTypeError('"%s" does not exist as a folder' % f)
    return f


def rate_str(r):
    """return valid sample rate (sa/sec) as int value converted from string, r"""
    try:
        value = int(r)
    except Exception as e:
        raise argparse.ArgumentTypeError('%s' % e)

    # William replace next 2 lines so that we raise error for any input besides our specific TSH-ES sample rates
    # William maybe use "not in" syntax
    if value < 1 or value > 999:
        raise argparse.ArgumentTypeError('rate, r, in sa/sec must be such that 1 <= r <= 999')

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
    help_rate = "sample rate (sa/sec); default = %s" % str(_DEFAULT_RATE)
    parser.add_argument('-r', '--rate', default=_DEFAULT_RATE, type=rate_str, help=help_rate)

    # sensor
    help_sensor = "sensor; default is %s" % _DEFAULT_SENSOR
    parser.add_argument('-s', '--sensor', default=_DEFAULT_SENSOR, type=sensor_str, help=help_sensor)

    # output directory
    help_outdir = 'output dir; default is %s' % _DEFAULT_OUTDIR
    parser.add_argument('-o', '--outdir', default=_DEFAULT_OUTDIR, type=folder_str, help=help_outdir)

    # parse
    args = parser.parse_args()

    # show args
    if args.quiet:
        pass
    elif args.verbose:
        print("sensor {} at sample rate of {} sa/sec".format(args.sensor, args.rate))
        print("output directory is {}".format(args.outdir))
    else:
        print("{} at {} sa/sec in {}".format(args.sensor, args.rate, args.outdir))

    return args


if __name__ == '__main__':

    args = parse_inputs()
