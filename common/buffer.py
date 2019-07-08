#!/usr/bin/env python3

import numpy as np


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

    def __init__(self, tsh, num):
        self.tsh = tsh  # tsh object -- to set/get some operating parameters
        self.num = num  # size of data buffer (i.e. number of points)
        # TODO next 2 lines will fill very fast, but be careful...np.empty is garbage values
        self.xyz = np.empty((num, 3))  # NOTE: this will contain garbage values
        self.xyz.fill(np.nan)          # NOTE: this cleans up garbage values, replacing with NaNs
        self.is_full = False           # flag that goes True when data buffer is full
        self.idx = 0

    def __str__(self):
        s = '%s: ' % self.__class__.__name__
        s += '%s, ' % self.tsh
        s += f'num = {self.num:,}'  # pattern: f'{value:,}' for thousands comma separator
        return s

    def write_spreadsheet(self, fname):
        print('writing spreadsheet data from %s buffer to %s' % (self.tsh.name, fname))

    def write_raw(self, fname):
        print('writing raw data from %s buffer to %s' % (self.tsh.name, fname))

    def add(self, more):

        if self.is_full:
            # TODO log entry that we tried to add to a buffer that's already full
            print('buffer already full')
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

    # create data buffer
    num_rows = 9  # how many rows of x,y,z values
    tsh = Tsh('tshes-44', 250.1, 1.2)  # last 2 args put/gotten for convenience here
    buffer = TshAccelBuffer(tsh, num_rows)

    b = np.arange(6).reshape(2, 3)
    buffer.add(b)

    b = np.arange(9).reshape(3, 3)
    buffer.add(b)

    b = np.arange(30).reshape(10, 3)
    buffer.add(b)

    b = np.arange(60).reshape(20, 3)
    buffer.add(b)

    print(buffer.xyz)

    buffer.write_spreadsheet('/tmp/somefile.xlsx')
    buffer.write_raw('/tmp/filename.csv')


if __name__ == '__main__':

    demo_buffer()
