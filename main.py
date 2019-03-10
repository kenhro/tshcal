#!/usr/bin/env python3

import sys
from inputs.argparser import parse_inputs


def main():

    # get input arguments
    args = parse_inputs()

    print(args)

    return 0  # return zero for success


if __name__ == '__main__':

    sys.exit(main())
