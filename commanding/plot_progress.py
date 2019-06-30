#!/usr/bin/env python3

import numpy as np
import datetime
import matplotlib.pyplot as plt

from tshcal.commanding.gsearch import move_rig_get_counts

# FIXME next import line is dummy to show an example
# TODO figure out where these values should be coming from (or how to derive them)
from tshcal.commanding.plot_progress_helper import SF_COUNTS, NUM_PTS, get_next_angle


class DataSource(object):

    def __init__(self, rig_ax):
        self.rig_ax = rig_ax

    def next_pt(self):
        angle = get_next_angle()
        counts = move_rig_get_counts(self.rig_ax, angle)
        return angle, counts


class GoalProgression(object):

    def __init__(self, src, num_pts=NUM_PTS):
        self.src = src
        self.num_pts = num_pts
        self.search_pts = None
        self.fig = None
        self.ax = None
        self.scat = None

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
        self.ax.set_ylim(-4.2e6, 4.2e6)  # TODO set yticks how?  we don't really know good, fairly narrow bounds?

        # construct scatter plot which updates via animation as the rig moves
        self.scat = self.ax.scatter(self.search_pts['position'][:, 0], self.search_pts['position'][:, 1],
                                    s=75, linewidth=1.0, edgecolors=self.search_pts['color'], facecolors='none')

        # show the progress plot
        plt.ion()
        plt.show()

    def __str__(self):
        return str(self.search_pts)

    def step(self):

        self.search_pts = np.roll(self.search_pts, 1, axis=0)

        # make colors more transparent with time
        self.search_pts['color'][:, 3] -= 1.0 / len(self.search_pts)
        self.search_pts['color'][:, 3] = np.clip(self.search_pts['color'][:, 3], 0, 1)

        angle, counts = self.src.next_pt()
        # angle = get_next_angle()
        # counts = move_rig_get_counts(self.src.rig_ax, angle)

        self.search_pts['position'][0, 0] = angle
        self.search_pts['position'][0, 1] = counts
        self.search_pts['color'][0] = (0, 0, 0, 1)

    def plot_step(self):

        # update search_pts array with next (angle, counts)
        self.step()

        # update title with system time
        self.ax.set_title('Time: %s' % datetime.datetime.now())

        # update scatter pts collection with new edgecolors (transparencies) & positions
        self.scat.set_edgecolors(self.search_pts['color'])
        self.scat.set_offsets(self.search_pts['position'])

        # print(frame_num, self)
        plt.draw()

    def run(self):
        while True:
            self.plot_step()
            plt.pause(0.001)
            ans = input("Type [enter] to step, or [x] exit: ")
            if ans == 'x':
                break
        print('user pressed x, so exiting')


if __name__ == '__main__':

    rig_ax = 'pitch'  # FIXME how/where do we establish rig axis we are using?

    # create data source object, which can get next point (angle, counts)
    source = DataSource('yaw')

    # create object to plot our search progress
    gp = GoalProgression(source, num_pts=NUM_PTS)
    gp.setup_plot()

    # start progress plot animation
    gp.run()

    print('done')
