import matplotlib.pyplot as plt
import numpy as np

# use ggplot style for better visuals
plt.style.use('ggplot')


def handle_close(evt):
    print('closed figure')


def live_plot(x_vec, y1_data, line1, identifier='', pause_sec=0.1):
    if line1 == []:
        # this is the call to matplotlib that allows dynamic plotting
        plt.ion()
        fig = plt.figure(figsize=(13,6))
        fig.canvas.mpl_connect('close_event', handle_close)
        ax = fig.add_subplot(111)
        # create a variable for the line so we can later update it
        line1, = ax.plot(x_vec,y1_data,'-o',alpha=0.8)        
        #update plot label/title
        plt.ylabel('Y Label')
        plt.title('Title: {}'.format(identifier))
        plt.show()
    
    # after the figure, axis, and line are created, we only need to update the y-data
    line1.set_ydata(y1_data)
    # adjust limits if new data goes beyond bounds
    if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
        plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])
    # this pauses the data so the figure/axis can catch up - the amount of pause can be altered above
    plt.pause(pause_sec)
    
    # return line so we can update it again in the next iteration
    return line1

# FIXME we can probably figure out a better way to reckon limits?
def get_lims(y):
    """get decent plot limits (not optimal though)"""
    s = np.std(y)
    m = np.mean(y)
    bot, top = m - 4 * s, m + 4 * s
    return bot, top, m, s

def get_special_median(a, n=20):
    """split array into n pieces and return special median value after ignoring the end pieces"""
    # this allows for edge effects (initially was mean, which makes sense, but median not so much)
    a2 = np.concatenate(np.array_split(a, n)[-6:-4])
    return np.median(a2)

def get_special_median2(a, n=20):
    """split array into n pieces and return special median value after ignoring the end pieces"""
    # this allows for edge effects (initially was mean, which makes sense, but median not so much)
    a2 = np.concatenate(np.array_split(a, n)[3:-3])
    return np.median(a2)

# the function below is for updating both x and y values (like for updating dates on the x-axis)
def live_plot_xy(x_vec, y1_data, line1, xlabel='xlabel', ylabel='ylabel', identifier='', pause_sec=0.1):
    # this first part happens once at the very beginning
    if line1 == []:
        plt.ion()
        #fig = plt.figure(figsize=(13,6))
        fig = plt.figure(figsize=(15, 7))
        fig.canvas.mpl_connect('close_event', handle_close)
        ax = fig.add_subplot(111)
        line1, = ax.plot(x_vec, y1_data, 'r', alpha=0.77)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        bot, top, _, _ = get_lims(y1_data)
        plt.ylim([bot, top])        
        plt.show()
        print('initial 5-second pause')
        plt.pause(5)
    
    # now we do crude animation plot stuff starting here
    #mm = np.median(y1_data)
    mm = get_special_median(y1_data)
    mm2 = get_special_median2(y1_data)
    title_str1 = 'median = %d g  ' % mm + 'Start Time: {}'.format(identifier)
    title_str2 = 'pedian = %d g  ' % mm2 + 'Start Time: {}'.format(identifier)
    title_str = '\n'.join([title_str1, title_str2])
    plt.title(title_str)
    line1.set_data(x_vec,y1_data)
    plt.xlim(np.min(x_vec),np.max(x_vec))
    
    #if np.min(y1_data)<=line1.axes.get_ylim()[0] or np.max(y1_data)>=line1.axes.get_ylim()[1]:
    #    plt.ylim([np.min(y1_data)-np.std(y1_data),np.max(y1_data)+np.std(y1_data)])
    
    bot, top, m, s = get_lims(y1_data)
    if bot<=line1.axes.get_ylim()[0] or top>=line1.axes.get_ylim()[1]:
        plt.ylim([bot - 2 * s, top + 2 * s])
       
    # pause is necessary for fig/ax to keep caught up
    plt.pause(pause_sec)
    
    return line1
