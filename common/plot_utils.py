#!/usr/bin/env python3

import time
import datetime
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import TextBox
import matplotlib.dates as mdates

from tshcal.common.sci_utils import is_outlier


DISP_PTS = 1600  # FIXME display width (num pts) for WHAT length of time [use rate to reckon pts]
PKT_SIZE = 256  # we get like 256 or 512 (per second) as typical for TSH -- right?
SLIDE_PTS = 25  # number of data points to "slide" to the left


class RealtimePlot(object):

    def __init__(self, disp_pts=DISP_PTS):

        self.disp_pts = disp_pts
        self.axis_x = deque(maxlen=self.disp_pts)
        self.axis_y = deque(maxlen=self.disp_pts)

        # initialize figure
        self.fig, self.axes = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        self.mng = plt.get_current_fig_manager()
        self.mng.resize(1600, 900)  # width, height in pixels

        self.lineplot, = self.axes.plot([], [], "r")
        self.axes.set_autoscaley_on(True)
        # self.axes.set_ylim([0, PKT_SIZE + 1])
        # self.axes.set_xlim([datetime.datetime(1970, 1, 1), datetime.datetime(1970, 1, 1, 0, 2, 0)])

        # self.axes.fmt_xdata = mdates.DateFormatter('%M:%s')
        self.fig.autofmt_xdate()

    def add(self, xvals, yvals):
        self.axis_x.extend(xvals)
        self.axis_y.extend(yvals)
        self.lineplot.set_data(self.axis_x, self.axis_y)
        self.axes.set_xlim(self.axis_x[0], self.axis_x[-1] + datetime.timedelta(seconds=1e-6))
        self.axes.relim()
        self.axes.autoscale_view(scaley=True)  # rescale the x-axis

    def animate(self, figure, callback, interval=50):
        def wrapper(frame_index):
            self.add(*callback(frame_index))
            self.axes.relim()
            self.axes.autoscale_view()  # rescale the y-axis
            return self.lineplot

        animation.FuncAnimation(figure, wrapper, interval=interval)

    def submit_ymin(self, text): self.submit_ylim('bottom', text)

    def submit_ymax(self, text): self.submit_ylim('top', text)

    def submit_ylim(self, key, txt):
        # TODO gracefully reject bogus values (no change, just warn & restore previous state)
        val = float(txt)
        kwargs = {key: val}
        self.axes.set_ylim(**kwargs)  # define function within function so we have this axes within scope
        plt.draw()


class TshRealtimePlot(RealtimePlot):

    def __init__(self, disp_pts=DISP_PTS):

        super().__init__(disp_pts=disp_pts)

        # set figure to be sure we got right one for these next settings
        # plt.figure(self.fig.number)

        # # establish ymin textbox
        # initial_ymin = "-100000"
        # self.ax_ymin = plt.axes([0.05, 0.06, 0.04, 0.045])
        # self.submit_ylim('bottom', initial_ymin)
        # self.txtbox_ymin = TextBox(self.ax_ymin, 'ymin', initial=initial_ymin)
        # self.txtbox_ymin.on_submit(self.submit_ymin)
        #
        # # establish ymax textbox
        # initial_ymax = "-150000"
        # self.ax_ymax = plt.axes([0.05, 0.9, 0.04, 0.045])
        # self.submit_ylim('top', initial_ymax)
        # self.txtbox_ymax = TextBox(self.ax_ymax, 'ymax', initial=initial_ymax)
        # self.txtbox_ymax.on_submit(self.submit_ymax)

        # # establish tspan textbox
        # initial_tspan = "30"  # seconds
        # self.ax_tspan = plt.axes([0.25, 0.06, 0.04, 0.045])
        # self.submit_tspan(initial_tspan)
        # self.txtbox_tspan = TextBox(self.ax_tspan, 'tspan', initial=initial_tspan)
        # self.txtbox_tspan.on_submit(self.submit_tspan)

    # def submit_tspan(self, txt):
    #     val = float(txt)
    #     # ax = self.ax ax.get_yaxis()
    #     # tmin, tmax = self.axes.get_xlim()
    #     # tmax = mdates.num2date(tmax)
    #     # tmin = tmax - datetime.timedelta(seconds=val)
    #     # self.axes.set_xlim([tmin, tmax])
    #     time.sleep(0.25)

    def run(self):

        # other parameters related to plotting
        sleep_sec = 0.1  # a built-in breather for animated plotting loop (keep this less than 0.25 seconds or so)
        base_time = datetime.datetime(1970, 1, 1)
        delta_sec = 1

        while True:
            # let's ballpark it takes about 3-4 seconds for loop to get from and back to this point
            # print(datetime.datetime.now())

            t_values = np.array([base_time + datetime.timedelta(seconds=i) for i in range(PKT_SIZE)])
            y_values = np.linspace(1.0, PKT_SIZE, num=PKT_SIZE) + np.random.standard_normal(PKT_SIZE) * 40.0

            # add in slide_pts at a time
            i1 = 0
            while i1 < len(y_values):
                i2 = i1 + SLIDE_PTS
                t = t_values[i1:i2]
                y = y_values[i1:i2]
                self.add(t, y)
                base_time = t[-1] + datetime.timedelta(seconds=delta_sec)
                plt.pause(sleep_sec)
                i1 = i2 + 1


def main():

    display = TshRealtimePlot()
    display.run()


if __name__ == "__main__":
    main()
