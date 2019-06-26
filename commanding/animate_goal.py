#!/usr/bin/env python3

import numpy as np
from time import sleep
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class GoalProgression(object):

    def __init__(self, initial):
        self.state = initial

    def __str__(self):
        return str(self.state)

    def step(self, frame_num):
        # Either assign a new value to self.state, or modify it
        self.state.append(frame_num)

    def plot_step(self, frame_num):
        # FIXME workaround a quirk with FuncAnimation; it runs twice the first frame (repeats zeroth frame)
        if frame_num > 0:
            self.step(frame_num)
            # TODO: Plot here
            print(frame_num, self)
            sleep(1)


# Create new figure and axes
fig, ax = plt.subplots(figsize=(16, 9))

initial = [150, 175, 198, 210]
gp = GoalProgression(initial)

ani = FuncAnimation(fig, gp.plot_step)
plt.show()
