#!/usr/bin/env python3

# FIXME the arrays of interest grow without bound (need new "rolling buffer" type container for those)

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap

# TODO refactor to move the following from all caps global vars to config/settings (if appropriate)
SF_COUNTS = 10_000

# Create new figure and axes
fig, ax = plt.subplots(figsize=(16, 9))

# Labels
ax.set_xlabel('Angle (deg.)', size=12)
ax.set_ylabel("Counts (x{:,})".format(SF_COUNTS), size=12)

# TODO set xticks based on current rough home position and/or interval
# TODO set yticks how?  we don't really know good, fairly narrow bounds?
# Adjust axes
ax.axis([0, 1, 0, 1])
ax.set_xlim(0, 1)  # , ax.set_xticks([])
ax.set_ylim(0, 1)  # , ax.set_yticks([])

# Initialize scatter data
x_vals = []
y_vals = []
intensity = []
iterations = 100

colors = [[0, 0, 1, 0], [0, 0, 1, 0.25], [0, 0.2, 0.4, 1]]
cmap = LinearSegmentedColormap.from_list("", colors)
scatter = ax.scatter(x_vals, y_vals, c=[], cmap=cmap, vmin=0, vmax=1)


def get_new_vals():
    n = np.random.randint(1, 5)
    x = np.random.rand(n)
    y = np.random.rand(n)
    return list(x), list(y)


def update(frame_num):
    # global x_vals, y_vals, intensity
    global intensity

    print(x_vals)

    # Get intermediate points
    new_xvals, new_yvals = get_new_vals()
    x_vals.extend(new_xvals)
    y_vals.extend(new_yvals)

    # Put new values in your plot
    scatter.set_offsets(np.c_[x_vals, y_vals])

    # Calculate new color values
    intensity = np.concatenate((np.array(intensity)*0.96, np.ones(len(new_xvals))))
    scatter.set_array(intensity)

    # Set title
    ax.set_title('Iteration: %d (%d pts)' % (frame_num, len(x_vals)))


ani = FuncAnimation(fig, update, interval=50)
plt.show()
