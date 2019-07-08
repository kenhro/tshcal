#!/usr/bin/env python3


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


class TshAccelFifo(object):

    def __init__(self, tsh, num_pts):
        self.tsh = tsh  # tsh object -- to set/get some operating parameters
        self.num_pts = num_pts  # size of FIFO buffer (i.e. number of points)

    def __str__(self):
        s = '%s: ' % self.__class__.__name__
        s += '%s, ' % self.tsh
        s += f'num_pts = {self.num_pts:,}'
        return s

    def write_spreadsheet(self, fname):
        print('writing spreadsheet data from %s fifo to %s' % (self.tsh.name, fname))

    def write_raw(self, fname):
        print('writing raw data from %s fifo to %s' % (self.tsh.name, fname))


def demo_taf():
    tsh = Tsh('tshes-44', 250.1, 1.2)
    taf = TshAccelFifo(tsh, 15_000)
    print(taf)
    taf.write_spreadsheet('/tmp/somefile.xlsx')
    taf.write_raw('/tmp/filename.csv')


if __name__ == '__main__':
    demo_taf()
