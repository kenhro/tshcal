#!/usr/bin/env python3

import numpy as np
import logging

logger = logging.getLogger(__name__)


class Tsh(object):

    def __init__(self, name, rate, gain):
        self.name = name  # i.e. tsh_id (e.g. tshes-13)
        self.rate = rate  # sample rate in sa/sec
        self.gain = gain  # sample rate in sa/sec

    def __str__(self):
        s = 'TSH = %s, ' % self.name
        s += 'rate = %.4f sa/sec, ' % self.rate
        s += 'gain = %.1f' % self.gain
        return s


class TshAccelBuffer(object):

    # TODO mean and std values for spreadsheet format and more robust file writing

    def __init__(self, tsh, sec):
        self.tsh = tsh  # tsh object -- to set/get some operating parameters
        self.sec = sec  # approximate size of data buffer (in seconds)
        self.num = np.int(np.ceil(self.tsh.rate * sec))  # exact size of buffer (num pts)
        # TODO next 2 lines fill array fast, but BE CAREFUL because np.empty is garbage values
        self.xyz = np.empty((self.num, 3))  # NOTE: this will contain garbage values
        self.xyz.fill(np.nan)          # NOTE: this cleans up garbage values, replacing with NaNs
        self.is_full = False           # flag that goes True when data buffer is full
        self.idx = 0

    def __str__(self):
        s = '%s: ' % self.__class__.__name__
        s += '%s, ' % self.tsh
        s += f'sec = {self.sec:,}'  # pattern: f'{value:,}' for thousands comma separator
        return s

    def write_spreadsheet(self, fname):
        print('writing spreadsheet data from %s buffer to %s' % (self.tsh.name, fname))
        np.savetxt(fname, self.xyz, delimiter=',')

    def write_raw(self, fname):
        print('writing raw data from %s buffer to %s' % (self.tsh.name, fname))
        np.save(fname, self.xyz)

    def add(self, more):

        if self.is_full:
            # TODO log entry that we tried to add to a buffer that's already full
            print('Buffer already full')
            logger.info('Buffer already full, array shape is %s' % str(self.xyz.shape))
            return

        offset = more.shape[0]
        if self.idx + offset > self.xyz.shape[0]:
            offset = self.xyz[self.idx:, :].shape[0]
            self.xyz[self.idx:self.idx + offset, :] = more[0:offset, :]
            self.is_full = True
            # TODO add log entry that TshAccelBuffer is now full (with how many rows)
        else:
            self.xyz[self.idx:self.idx + offset, :] = more
        # print(self.idx, self.idx + offset)
        self.idx = self.idx + offset


def demo_buffer():

    import os
    import platform

    # fake/dummy arguments for buffer creationg
    sec = 1  # how many seconds-worth of TSH data (x,y,z acceleration values)
    fs, k = 9.0, 0  # fake/dummy arguments for sample rate and gain

    # create data buffer -- at some pt in code before we need mean(counts), probably just after GSS min/max found
    tsh = Tsh('tshes-44', fs, k)
    buffer = TshAccelBuffer(tsh, sec)

    # add some data to buffer (note shape is Nx3, with 3 columns for xyz)
    b = np.arange(6).reshape(2, 3)
    buffer.add(b)

    # add some data to buffer (note shape is Nx3, with 3 columns for xyz)
    b = np.arange(9).reshape(3, 3)
    buffer.add(b)

    # add some data to buffer (note shape is Nx3, with 3 columns for xyz)
    b = np.arange(30).reshape(10, 3)
    buffer.add(b)

    # buffer should be full by now, but let's try to add more data (should not be able to)
    b = np.arange(60).reshape(20, 3)
    buffer.add(b)

    print(buffer.xyz)

    out_dir = 'c:/temp' if platform.system() == 'Windows' else '/tmp'
    csv_file = os.path.join(out_dir, 'foo.csv')

    buffer.write_spreadsheet(csv_file)

    npy_file = csv_file.replace('.csv', '.npy')
    buffer.write_raw(npy_file)


if __name__ == '__main__':

    demo_buffer()
