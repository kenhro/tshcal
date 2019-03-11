#!/usr/bin/env python3

import sys
from inputs.argparser import parse_inputs
from commanding.tsh_commands import set_tsh


def main():

    # get input arguments
    args = parse_inputs()

    # set tsh parameters via commanding
    set_tsh(args)

    return 0  # return zero for success


if __name__ == '__main__':

    sys.exit(main())
