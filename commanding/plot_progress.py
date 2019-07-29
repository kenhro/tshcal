#!/usr/bin/env python3

import datetime
import numpy as np
import matplotlib.pyplot as plt

# TODO figure out where these values should be coming from (or how to derive them)
from tshcal.commanding.plot_progress_helper import SF_COUNTS, NUM_PTS


class GoalProgressPlot(object):

    def __init__(self, rig_ax, num_pts=NUM_PTS):
        self.rig_ax = rig_ax    # which rig_ax we working on
        self.num_pts = num_pts  # how much of faded-plot-points history to keep
        self.search_pts = None
        self.fig = None
        self.ax = None
        self.scat = None
        self.title = None

    def setup_plot(self):

        # initialize array of search points
        self.search_pts = np.zeros(self.num_pts, dtype=[('position', float, 2),
                                                        ('color', float, 4)])

        # create figure and axes for plot
        self.fig, self.ax = plt.subplots(figsize=(16, 9))

        # label plot axes
        self.ax.set_xlabel('Angle (deg.)', size=12)
        self.ax.set_ylabel("Counts (x{:,})".format(SF_COUNTS), size=12)

        # adjust axes
        self.ax.axis([0, 1, 0, 1])
        self.ax.set_xlim(0, 360)  # TODO set xticks based on current rough home position and/or interval
        self.ax.set_ylim(-4.2e6, 4.2e6)  # TODO set yticks how?  how to know good, fairly narrow bounds?

        # construct scatter plot which updates via animation as the rig moves
        self.scat = self.ax.scatter(self.search_pts['position'][:, 0], self.search_pts['position'][:, 1],
                                    s=75, linewidth=1.0, edgecolors=self.search_pts['color'], facecolors='none')

        # initial plot title
        time_str = datetime.datetime.now().strftime('%Y-%m-%d/%H:%M:%S')
        self.title = 'Rig Axis = %s, Time: %s' % (self.rig_ax, time_str)
        self.set_title('')

        # show the progress plot
        plt.ion()
        plt.show()

    def __str__(self):
        return str(self.search_pts)

    def step(self, x, y):

        self.search_pts = np.roll(self.search_pts, 1, axis=0)

        # make colors more transparent with time
        self.search_pts['color'][:, 3] -= 1.0 / len(self.search_pts)
        self.search_pts['color'][:, 3] = np.clip(self.search_pts['color'][:, 3], 0, 1)

        self.search_pts['position'][0, 0] = x  # angle
        self.search_pts['position'][0, 1] = y  # counts
        self.search_pts['color'][0] = (0, 0, 0, 1)

    def plot_step(self, x, y):

        # update search_pts array with next (x=angle, y=counts)
        self.step(x, y)

        # update title with system time
        self.set_title(' Angle = %.4f, Counts/%d = %.1f' % (x, SF_COUNTS, y))

        # update scatter pts collection with new edgecolors (transparencies) & positions
        self.scat.set_edgecolors(self.search_pts['color'])
        self.scat.set_offsets(self.search_pts['position'])

        # update canvas
        plt.draw()

    def set_title(self, suffix):
        self.ax.set_title('%s %s' % (self.title, suffix))

    def plot_point(self, x, y):
        self.plot_step(x, y)
        plt.pause(0.001)

    def debug_plot_point(self, x, y):
        # FIXME mostly placeholder for now, maybe user prompts along the way (much verbosity, etc.)
        # TODO add verbosity for logging
        self.plot_point(x, y)
