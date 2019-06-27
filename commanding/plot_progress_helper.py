#!/usr/bin/env python3

import numpy as np


# TODO refactor to move the following from all caps global vars to config/settings (if appropriate)
SF_COUNTS = 1000    # scale factor for counts (e.g. instead of 400,000 -- scale to 400)
NUM_PTS = 20        # how much of a history of searched points to keep/observe

ACDB = np.array([
    150.000, 172.918, 187.082, 210.000,
    195.836,
    181.672,
    178.328,
    183.738,
    180.395,
    179.605,
    180.883,
    180.093,
    179.907,
    180.208,
    180.022,
    179.978,
    180.049,
    180.005,
    179.995,
    180.012,
    180.001,
    179.999,
    144.1,
    144.2,
    144.3,
])


def angles():
    for i in range(0, len(ACDB)):
        yield ACDB[i]
    for j in np.arange(140.0, 220.0, 0.2):
        yield j


def get_next_angle():
    return next(ANGLES)

ANGLES = angles()
