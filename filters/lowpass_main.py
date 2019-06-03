#!/usr/bin/env python

import os
import sys
import warnings
import datetime
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt

from tshcal.filters.pylive import live_plot_xy
from tshcal.common.accel_packet import guess_packet, sql_connect
from tshcal.common.time_utils import unix_to_human_time


warnings.filterwarnings("ignore", ".*GUI is implemented")

# input parameters
defaults = {
'table':            'es13', # string to specify sensor db table (eg. es13)
'fs':               '250',  # float value to specify sample rate (sa/sec)
'fc':               '1',    # integer value for cutoff frequency (Hz)
'ax':               '1',    # integer value to designate which axis (x=1, y=2, z=3)
'num_pkts':         '240',  # integer value for num packets for span of interest (maybe 240 pkts for a 1-min. plot span)
'pause_sec':        '0.2',  # float value for pause time in the live plotting loop
}
parameters = defaults.copy()


def get_butter_analog(forder, cutoff):
    """return numerator (b) & denominator (a) polynomial coeffs of IIR lowpass filter"""
    rad_per_sec = 2 * np.pi * cutoff    
    b, a = scipy.signal.butter(forder, rad_per_sec, 'low', analog=True)
    return b, a


def get_butter_digital(fs, fc, norder=4):
    """return numerator (b) & denominator (a) polynomial coeffs of Butterworth LPF"""
    pct_nyq = 2.0 * fc / fs
    # create nth order lowpass butterworth filter
    b, a = scipy.signal.butter(norder, pct_nyq)  # e.g. 5% of Nyquist = 5% of 50 sa/sec = 2.5 Hz
    return b, a


def show_butter(b, a):
    """plot frequency response of butterworth lowpass filter"""
    w, h = scipy.signal.freqs(b, a)
    plt.semilogx(w/2.0/np.pi, 20 * np.log10(abs(h)))
    plt.title('Butterworth filter frequency response')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude [dB]')
    plt.margins(0, 0.1)
    plt.grid(which='both', axis='both')
    plt.axvline(cutoff, color='green')  # cutoff frequency
    plt.show()    


def lowpass_filtfilt(t, xn, fs, fc, b, a):
    """lowpass filter, like MATLAB filtfilt"""
    
    # # apply the filter to xn; use lfilter_zi to choose the initial condition of the filter
    # zi = scipy.signal.lfilter_zi(b, a)
    # z, _ = scipy.signal.lfilter(b, a, xn, zi=zi*xn[0])
    #
    # # apply the filter again, to have a result filtered at an order the same as filtfilt
    # z2, _ = scipy.signal.lfilter(b, a, z, zi=zi*z[0])
    
    # use filtfilt to apply the filter
    y = scipy.signal.filtfilt(b, a, xn)

    return y


def demo_lowpass():
    """demo filtfilt (like MATLAB) scheme for lowpass filtering"""
    
    # create test signal
    fs = 250  # samples per second
    tmin, tmax = -1, 1
    numsteps = (tmax - tmin) * fs + 1
    t = np.linspace(tmin, tmax, numsteps)
    x = (np.sin(2*np.pi*0.77*t*(1-t) + 2.1) +   # LPF preserves this 0.77 Hz
         0.1*np.sin(2*np.pi*1.22*t + 1) +       # LPF preserves this 1.22 Hz
         0.18*np.cos(2*np.pi*3.88*t))           # LPF attenuates this 3.88 Hz
    xn = x + np.random.randn(len(t)) * 0.08     # LPF attenuates "high-freq." noise
    
    # create nth order lowpass butterworth filter
    norder = 4  # order of LPF
    fc = 2.5  # Hz; our desired cutoff freq
    b, a = get_butter_digital(fs, fc, norder=norder)
    
    # use something like MATLAB's filtfilt to apply the filter 
    y = lowpass_filtfilt(t, xn, fs, fc, b, a)
    
    # plot the original signal and the various filtered versions
    plt.figure
    plt.plot(t, xn, 'b', alpha=0.75)
    plt.plot(t, y, 'r')
    plt.legend(('noisy signal', 'filtfilt'), loc='best')
    plt.grid(True)
    plt.show()


def get_accel_from_db(table, ax, num_pkts):
    """get ax'th column from num_pkts from db table"""
    
    results = sql_connect('select * from %s order by time desc limit %d' % (table, num_pkts), 'localhost')
    
    # initialize list array to be returned in flattened form
    x = []
    
    # special handling of first packet to get start time
    # NOTE: we used "desc" in query so gotta index from the "end"
    i1 = results[-1]
    p1 = guess_packet(i1[1])
    start_time = p1.time()
    #print UnixToHumanTime(start_time)
    
    # append first packet's worth to output
    x.append( [ a[ax] for a in p1.txyz() ] )
    
    # NOTE: we used "desc" in query so gotta loop backwards here
    # now iterate over remaining packets to build output
    for i in results[-2::-1]:  # i[0] is time, i[1] is the blob, i[2] is the type
        p = guess_packet(i[1])
        #start_time2 = p.time()
        #print UnixToHumanTime(start_time2)
        x.append( [ a[ax] for a in p.txyz() ] )
        
    # returned flattened array version of x and the start_time for this chunk
    return [ item for sublist in x for item in sublist ], start_time


def display_accel(table, k=0, sleep_sec=1):
    """display kth sample from each packet with MySQL query ("desc limit 1")"""
    title='\33]0;' + table + ' Accel Packets\a'
    stdout.write(bytes(title))
    stdout.flush()
    while 1:
        results = sql_connect('select * from %s order by time desc limit 1' % table, 'localhost')
        os.system('clear')
        os.system('date')
    
        for i in results:
            # i[0] is time, i[1] is the blob, i[2] is the type
            p = guess_packet(i[1])  # just do the guessing once per iteration
            print('Packet Time:', unix_to_human_time(p.time()))
            print('Name:', p.name())
            print('Rate:', p.rate())
            print('Gain:', p.gain())
            print('Unit:', p.unit())
            print('Samples:', p.samples())
            print('Adjustment:', p.adjustment())
            txyz = np.array(p.txyz())  # use numpy array for downstream handling
            #fda = lowpass_old(txyz[:, 1:], 4, 1, 250)  # skip time column for filtering
            # show kth sample of something like 64 samples in this packet
            print('Time   :', txyz[k][0])
            print('X Accel:', txyz[k][1])
            print('Y Accel:', txyz[k][2])
            print('Z Accel:', txyz[k][3])
            print('')
            print('---------------------------')
        
        print('displayAccel.py v1.0')
        print('Press CTRL-C to stop')
        sleep(sleep_sec)


def run(table, fs, fc, ax, num_pkts, xlabel, ylabel, pause_sec):
    """main routine for live LPF plotting"""
    
    # create nth order lowpass butterworth filter
    norder = 4  # order of LPF
    b, a = get_butter_digital(fs, fc, norder=norder)

    # endless plot loop
    line1 = []
    while True:
        
        # get latest set of data from db table (just ax axis)
        data, start_time = get_accel_from_db(table, ax, num_pkts)
        xn = np.array(data)
        
        # generate time vector sequence (FIXME assuming no gaps)
        #t = np.linspace(start_time, start_time+(len(xn)-1)/fs, len(xn), endpoint=True)
        t = np.linspace(0.0, (len(xn)-1)/fs, len(xn), endpoint=True)
        
        # apply LPF
        y = lowpass_filtfilt(t, xn, fs, fc, b, a)
        
        ## plot the original signal and the filtered version
        #plt.figure
        #plt.plot(t, xn, 'b', alpha=0.75)
        #plt.plot(t, y, 'r')
        #plt.legend(('noisy signal', 'filtfilt'), loc='best')
        #plt.grid(True)
        #plt.show()
        
        # call live plotter    
        ident = unix_to_human_time(start_time) + '   [ now: %s ]' % datetime.datetime.now()
        line1 = live_plot_xy(t, y, line1, xlabel=xlabel, ylabel=ylabel, identifier=ident, pause_sec=pause_sec)


def NEWrun(table, fs, fc, ax, num_pkts, xlabel, ylabel, pause_sec):
    """main routine for live LPF plotting"""

    # create 4th order low-pass butterworth filter
    blowpass_filt = ButterworthLowpassFilt(fs, fc, norder=4, has_nan=True)

    # endless plot loop
    line1 = []
    while True:
        # get latest set of data from db table (just ax axis)
        data, start_time = get_accel_from_db(table, ax, num_pkts)
        xn = np.array(data)

        # generate time vector sequence (FIXME assuming no gaps)
        # t = np.linspace(start_time, start_time+(len(xn)-1)/fs, len(xn), endpoint=True)
        t = np.linspace(0.0, (len(xn) - 1) / fs, len(xn), endpoint=True)

        # apply LPF
        # y = lowpass_filtfilt(t, xn, fs, fc, b, a)
        y = blowpass_filt.apply(xn)

        ## plot the original signal and the filtered version
        # plt.figure
        # plt.plot(t, xn, 'b', alpha=0.75)
        # plt.plot(t, y, 'r')
        # plt.legend(('noisy signal', 'filtfilt'), loc='best')
        # plt.grid(True)
        # plt.show()

        # call live plotter
        ident = unix_to_human_time(start_time) + '   [ now: %s ]' % datetime.datetime.now()
        line1 = live_plot_xy(t, y, line1, xlabel=xlabel, ylabel=ylabel, identifier=ident, pause_sec=pause_sec)


def parameters_ok():
    """check for reasonableness of parameters"""    

    # FIXME we do not check table string at all
    
    # make sure we can get an integer value here, as expected
    try:
        parameters['num_pkts'] = int(parameters['num_pkts'])
    except Exception as e:
        print('did not get num_pkts as int: %s' % e.message)
        return False    
    
    # make sure we can get an integer value (1, 2 or 3), as expected
    try:
        parameters['ax'] = int(parameters['ax'])
        assert(0 < parameters['ax'] < 4)
    except Exception as e:
        print('did not get ax as int value (1, 2 or 3): %s' % e.message)
        return False
    
    # make sure we can get an integer value here, as expected
    try:
        parameters['fc'] = int(parameters['fc'])
    except Exception as e:
        print('did not get fc as int: %s' % e.message)
        return False    

    # make sure we can get a float value here, as expected
    try:
        parameters['fs'] = float(parameters['fs'])
    except Exception as e:
        print('did not get fs as float: %s' % e.message)
        return False    

    # make sure we can get a float value here, as expected
    try:
        parameters['pause_sec'] = float(parameters['pause_sec'])
    except Exception as e:
        print('did not get pause_sec as float: %s' % e.message)
        return False
    
    # be sure user did not mistype or include a parameter we are not expecting
    s1, s2 = set(parameters.keys()), set(defaults.keys())
    if s1 != s2:
        extra = list(s1-s2)
        missing = list(s2-s1)
        if extra:   print('extra   parameters -->', extra)
        if missing: print('missing parameters -->', missing)
        return False    

    return True # all OK; otherwise, we'd have returned False somewhere above


def print_usage():
    """print helpful text how to run the program"""
    print('usage: %s [options]' % os.path.abspath(__file__))
    print('       options (and default values) are:')
    for i in list(defaults.keys()):
        print('\t%s=%s' % (i, defaults[i]))


def main(argv):
    """parse command line parameters and branch to mode of operation if parameters are okay"""
    
    # parse command line
    for p in argv[1:]:
        pair = p.split('=')
        if 2 != len(pair):
            print('bad parameter: %s' % p)
            break
        else:
            parameters[pair[0]] = pair[1]
    else:
        if parameters_ok():
            print(parameters)
            table = parameters['table']
            fs = parameters['fs']
            fc = parameters['fc']
            ax = parameters['ax']
            num_pkts = parameters['num_pkts']
            pause_sec = parameters['pause_sec']            
            # branch to different modes here
            if fs == 0 or fc == 0 or num_pkts == 0:
                display_accel(parameters['table'], k=0, sleep_sec=1)
            else:
                # get labels
                xlabel, ylabel = 'time (sec)', 'axis #%d (g)' % parameters['ax']        
                # call main routine to do endless loop live LPF plotting
                run(table, fs, fc, ax, num_pkts, xlabel, ylabel, pause_sec)
                
            return 0  # zero is return code of success for unix
        
    print_usage()  


if __name__ == '__main__':
    """run main with cmd line args and return exit code"""
    sys.exit(main(sys.argv))
