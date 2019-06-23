import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from time import sleep


x = np.linspace(0, 10, 100)
y = np.sin(x)

fig, ax = plt.subplots()
line, = ax.plot(x, y, color='k')


def update(num, x, y, line):
    line.set_data(x[:num], y[:num])
    line.axes.axis([0, 10, -1, 1])
    return line,


ani = animation.FuncAnimation(fig, update, len(x), fargs=[x, y, line], interval=25, blit=True)
#ani.save('test.gif')
plt.show()
