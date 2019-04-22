#!/usr/bin/env python3

import datetime
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import TextBox


PKT_SIZE = 9  # 256 or 512 is typical for TSH -- right?
DISPLAY_PTS = PKT_SIZE * 5  # FIXME display width (num pts) for WHAT length of time [use rate to reckon pts]


class RealtimePlot(object):

    def __init__(self, max_pts=DISPLAY_PTS):

        # initialize figure
        self.fig, self.axes = plt.subplots()
        plt.subplots_adjust(bottom=0.2)
        self.mng = plt.get_current_fig_manager()
        self.mng.resize(1600, 900)  # width, height in pixels

        self.axis_x = deque(maxlen=max_pts)
        self.axis_y = deque(maxlen=max_pts)
        self.max_pts = max_pts
        self.lineplot, = self.axes.plot([], [], "ro-")
        self.axes.set_autoscaley_on(False)
        self.axes.set_ylim([0, PKT_SIZE + 1])
        # self.fig = self.axes.figure
        self.fig.autofmt_xdate()

    def add(self, xvals, yvals):
        self.axis_x.extend(xvals)
        self.axis_y.extend(yvals)
        self.lineplot.set_data(self.axis_x, self.axis_y)
        self.axes.set_xlim(self.axis_x[0], self.axis_x[-1] + datetime.timedelta(seconds=1e-6))
        self.axes.relim()
        self.axes.autoscale_view(scaley=False)  # rescale the x-axis

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

    def __init__(self, max_pts=DISPLAY_PTS):

        super().__init__(max_pts=max_pts)

        # set figure to be sure we got right one for these next settings
        plt.figure(self.fig.number)

        # establish ymin textbox
        initial_ymin = "-2"
        self.ax_ymin = plt.axes([0.05, 0.06, 0.04, 0.045])
        self.submit_ylim('bottom', initial_ymin)
        self.txtbox_ymin = TextBox(self.ax_ymin, 'ymin', initial=initial_ymin)
        self.txtbox_ymin.on_submit(self.submit_ymin)

        # establish ymax textbox
        initial_ymax = "10"
        self.ax_ymax = plt.axes([0.05, 0.9, 0.04, 0.045])
        self.submit_ylim('top', initial_ymax)
        self.txtbox_ymax = TextBox(self.ax_ymax, 'ymax', initial=initial_ymax)
        self.txtbox_ymax.on_submit(self.submit_ymax)

    def run(self):

        # other parameters related to plotting
        sleep_sec = 1
        base_time = datetime.datetime(1970, 1, 1)
        delta_sec = 1

        while True:
            t_values = np.array([base_time + datetime.timedelta(seconds=i) for i in range(PKT_SIZE)])
            y_values = np.linspace(1.0, PKT_SIZE, num=PKT_SIZE) + np.random.standard_normal(PKT_SIZE) / 3.0
            self.add(t_values, y_values)
            base_time = t_values[-1] + datetime.timedelta(seconds=delta_sec)
            plt.pause(sleep_sec)


def OLDmain():

    def submit_ymin(text): submit_ylim('bottom', text)

    def submit_ymax(text): submit_ylim('top', text)

    def submit_ylim(key, txt):
        # TODO gracefully reject bogus values (no change, just warn & restore previous state)
        val = float(txt)
        kwargs = {key: val}
        axes.set_ylim(**kwargs)  # define function within function so we have this axes within scope
        plt.draw()

    # initialize figure
    fig, axes = plt.subplots()
    plt.subplots_adjust(bottom=0.2)
    display = RealtimePlot(axes)
    mng = plt.get_current_fig_manager()
    mng.resize(1600, 900)  # width, height in pixels

    # establish ylim textboxes
    txtbox_ymin = plt.axes([0.05, 0.06, 0.04, 0.045])
    initial_text = "-1"
    ymin = float(initial_text)
    axes.set_ylim(bottom=float(ymin))
    text_box_ymin = TextBox(txtbox_ymin, 'ymin', initial=initial_text)
    text_box_ymin.on_submit(submit_ymin)

    txtbox_ymax = plt.axes([0.05, 0.9, 0.04, 0.045])
    initial_text = "10"
    ymax = float(initial_text)
    axes.set_ylim(top=float(ymax))
    text_box_ymax = TextBox(txtbox_ymax, 'ymax', initial=initial_text)
    text_box_ymax.on_submit(submit_ymax)

    # other parameters related to plotting
    sleep_sec = 1
    base_time = datetime.datetime(1970, 1, 1)
    delta_sec = 1

    while True:
        t_values = np.array([base_time + datetime.timedelta(seconds=i) for i in range(PKT_SIZE)])
        y_values = np.linspace(1.0, PKT_SIZE, num=PKT_SIZE) + np.random.standard_normal(PKT_SIZE) / 3.0
        display.add(t_values, y_values)
        base_time = t_values[-1] + datetime.timedelta(seconds=delta_sec)
        plt.pause(sleep_sec)


def main():

    # # initialize figure
    # fig, axes = plt.subplots()
    # plt.subplots_adjust(bottom=0.2)
    # mng = plt.get_current_fig_manager()
    # mng.resize(1600, 900)  # width, height in pixels

    display = TshRealtimePlot()
    display.run()


if __name__ == "__main__":
    # OLDmain()
    main()
