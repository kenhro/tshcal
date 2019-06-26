#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from time import sleep
from collections import deque

# array = np.arange(18).reshape(9, 2)
# print("Original array : \n", array)
#
# # Rolling array; Shifting one place
# print("\nRolling with 1 shift : \n", np.roll(array, 1))
#
# # Rolling array; Shifting five places
# print("\nRolling with 5 shift : \n", np.roll(array, 5))
#
# # Rolling array; Shifting five places with 0th axis
# print("\nRolling with 5 shift with 0 axis : \n", np.roll(array, 2, axis=0))
#
# raise SystemExit

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
])


def angles():
    for i in range(0, len(ACDB)):
        yield ACDB[i]


a = angles()

# TODO refactor to move the following from all caps global vars to config/settings (if appropriate)
SF_COUNTS = 10_000  # scale factor for counts
NUM_PTS = 10        #

# Create new figure and axes
fig, ax = plt.subplots(figsize=(16, 9))

# Labels
ax.set_xlabel('Angle (deg.)', size=12)
ax.set_ylabel("Counts (x{:,})".format(SF_COUNTS), size=12)

# TODO set xticks based on current rough home position and/or interval
# TODO set yticks how?  we don't really know good, fairly narrow bounds?
# Adjust axes
ax.axis([0, 1, 0, 1])
ax.set_xlim(0, 360)
ax.set_ylim(-1.1, 1.1)

# Create initial scatter data points
n_pts = NUM_PTS
scatter_pts = np.zeros(n_pts, dtype=[('position', float, 2),
                                     ('color',    float, 4)])

# angle = next(a)
# scatter_pts['position'][0, 0] = angle
# scatter_pts['position'][0, 1] = np.cos(np.radians(angle))
# scatter_pts['color'][0] = (0, 0, 0, 1)
#
# print(scatter_pts)
#
# ##############################################
# scatter_pts = np.roll(scatter_pts, 1, axis=0)
#
# # Make all colors more transparent as time progresses
# scatter_pts['color'][:, 3] -= 1.0 / len(scatter_pts)
# scatter_pts['color'][:, 3] = np.clip(scatter_pts['color'][:, 3], 0, 1)
#
# angle = next(a)
# scatter_pts['position'][0, 0] = angle
# scatter_pts['position'][0, 1] = np.cos(np.radians(angle))
# scatter_pts['color'][0] = (0, 0, 0, 1)
# ##############################################
# print(scatter_pts)
#
# scatter_pts = np.roll(scatter_pts, 1, axis=0)
#
# # Make all colors more transparent as time progresses
# scatter_pts['color'][:, 3] -= 1.0 / len(scatter_pts)
# scatter_pts['color'][:, 3] = np.clip(scatter_pts['color'][:, 3], 0, 1)
#
# angle = next(a)
# scatter_pts['position'][0, 0] = angle
# scatter_pts['position'][0, 1] = np.cos(np.radians(angle))
# scatter_pts['color'][0] = (0, 0, 0, 1)
#
# print(scatter_pts)
#
# raise SystemExit

# Construct scatter plot which updates via animation as rig moves
pts = ax.scatter(scatter_pts['position'][:, 0], scatter_pts['position'][:, 1],
                 s=75, linewidth=0.5, edgecolors='none', facecolors=scatter_pts['color'])


def update(frame_number, scatter_pts):

    scatter_pts = np.roll(scatter_pts, 1, axis=0)

    # Make all colors more transparent as time progresses
    scatter_pts['color'][:, 3] -= 1.0 / len(scatter_pts)
    scatter_pts['color'][:, 3] = np.clip(scatter_pts['color'][:, 3], 0, 1)

    angle = next(a)
    scatter_pts['position'][0, 0] = angle
    scatter_pts['position'][0, 1] = np.cos(np.radians(angle))
    scatter_pts['color'][0] = (0, 0, 0, 1)

    print(scatter_pts)

    # Update the scatter pts collection, with the new colors and positions
    pts.set_facecolors(scatter_pts['color'])
    pts.set_offsets(scatter_pts['position'])

    sleep(0.5)


# Construct the animation, using the update function as the animation director.
animation = FuncAnimation(fig, update, fargs=(scatter_pts, ), interval=50)
plt.show()
