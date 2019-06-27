#!/usr/bin/env python3

import numpy as np
from time import sleep
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from commanding.gsearch import move_rig_get_counts

# FIXME next import line is dummy to show an example
# TODO figure out where these values should be coming from (or how to derive them)
from commanding.plot_progress_helper import SF_COUNTS, NUM_PTS, get_next_angle


class GoalProgression(object):

    def __init__(self, rig_ax, num_pts=NUM_PTS):
        self.rig_ax = rig_ax
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

    def __str__(self):
        return str(self.search_pts)

    def step(self, frame_num):

        self.search_pts = np.roll(self.search_pts, 1, axis=0)

        # Make all colors more transparent as time progresses
        self.search_pts['color'][:, 3] -= 1.0 / len(self.search_pts)
        self.search_pts['color'][:, 3] = np.clip(self.search_pts['color'][:, 3], 0, 1)

        angle = get_next_angle()
        counts = move_rig_get_counts(self.rig_ax, angle)

        self.search_pts['position'][0, 0] = angle
        self.search_pts['position'][0, 1] = counts
        self.search_pts['color'][0] = (0, 0, 0, 1)

        # if frame_num > 20:
        #     print(self.search_pts)

    def plot_step(self, frame_num):

        if frame_num == 0: return  # FIXME FuncAnimation quirk: it runs this callback twice for zero-th (first) frame

        # update title with frame number
        self.step(frame_num)
        self.ax.set_title('Iteration: %d' % frame_num)

        # update scatter pts collection with new edgecolors (transparencies) & positions
        self.scat.set_edgecolors(self.search_pts['color'])
        self.scat.set_offsets(self.search_pts['position'])

        # update xlim on 4th frame (we've gotten to initial golden section interval)
        if frame_num == 4:
            pb = self.search_pts['position'][0]
            pa = self.search_pts['position'][3]
            w = 4.0 * (pb[0] - pa[0]) / 3.0
            self.ax.set_xlim(pa[0] - w / 3.0, pb[0] + w / 3.0)

        # print(frame_num, self)
        sleep(0.15)

    def animate(self):
        # show progress plot animation
        ani = FuncAnimation(self.fig, self.plot_step)  # without LHS output, no updates!?
        plt.show()


if __name__ == '__main__':

    rig_ax = 'yaw'  # FIXME how/where do we establish rig axis we are using?

    # create object to plot our search progress
    gp = GoalProgression(rig_ax, num_pts=NUM_PTS)
    gp.setup_plot()

    # start progress plot animation
    gp.animate()

    print('bye')
