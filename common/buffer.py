#!/usr/bin/env python3

import re
import socket
import struct
import numpy as np
import logging

from tshcal.common.time_utils import unix_to_human_time
from tshcal.defaults import TSH_BUFFER_SEC
from tshcal.common.tshes_params_packet import TshesMessage
from tshcal.constants_tsh import TSH_RATES, TSH_GAINS, TSH_UNITS
from tshcal.secret import IP_STUB


# create logger
module_logger = logging.getLogger('tshcal')


def divvy_up(num, divisor=16):
    """return tuple with 2 values: floor(num/divisor) and num%divisor
    :param num: integer number of values
    :param divisor: integer divisor, e.g. number of bytes in each record (default is 16)
    :return: a tuple with 2 values: floor(num/divisor) and num%divisor
    """
    return int(np.floor(num/divisor)), num % divisor


def recvall(sock, n):
    """helper function to receive n bytes from (sock)et or return None if EOF is hit"""
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def get_buff_header():
    """something to keep things straight for raw data from socket deal"""
    s = [
    'recv',
    'seqnum',
    'sync',
    'msiz',
    'cksum',
    ' source',
    'destin',
    'sel',
    'dsiz',
    ' tsh',
    '   counter',
    (18 * ' ') + 'start',
    'pstat',
    'num',
    'fsrate',
    'cutoff',
    'gain',
    ' input',
    '  unit',
    '     adjustment',
    (20 * ' ') + 'end',
    'rec',
    'LOB',
    'def',
    'need']
    return ' '.join(s)


def print_header():
    print(get_buff_header())


class Tsh(object):

    def __init__(self, name, rate, gain):
        self._validate_name(name)
        self.name = name  # i.e. tsh_id (e.g. es14)
        self.ip = IP_STUB + self.name[-2:]
        self.rate = rate  # sample rate in sa/sec
        self.gain = gain  # gain [code?]  # FIXME figure out if we want code or actual gain value here [probably code!]
        module_logger.warning("Instantiated %s object but it does not really (yet) do any get/set with TSH commands."
                              % self.__class__.__name__)

    def __str__(self):
        s = '%s, ' % self.name
        s += 'rate = %.4f sa/sec, ' % self.rate
        s += 'gain = %.1f' % self.gain
        return s

    def _validate_name(self, name):
        regexp = re.compile(r'^es\d{2}$')
        if regexp.search(name):
            module_logger.debug("Validated %s object's name attribute = %s." % (self.__class__.__name__, name))
        else:
            module_logger.info("Invalid %s.name = %s, doesn't match regular expression."
                               % (name, self.__class__.__name__))
            raise ValueError("Invalid %s.name = %s, doesn't match regular expression."
                               % (name, self.__class__.__name__))


class TshAccelBuffer(object):

    # TODO mean and std values for spreadsheet format and more robust file writing

    def __init__(self, tsh, sec, logger=module_logger):
        self.tsh = tsh  # tsh object -- to set/get some operating parameters
        self.sec = sec  # approximate size of data buffer (in seconds)
        self.logger = logger
        self.logger.debug('Initializing %s.' % self.__class__.__name__)
        self.num = np.int(np.ceil(self.tsh.rate * sec))  # exact size of buffer (num pts)
        # TODO BE CAREFUL: next 2 lines fill array fast, BUT np.empty will contain garbage values
        self.xyz = np.empty((self.num, 3))  # this will contain garbage values
        self.xyz.fill(np.nan)          # this cleans up garbage values, replacing with NaNs
        self.is_full = False           # flag that goes True when data buffer is full
        self.idx = 0
        self.logger.debug('Done initializing %s.' % self.__class__.__name__)

    def __str__(self):
        s = '%s: ' % self.__class__.__name__
        s += '%s, ' % self.tsh
        s += f'sec = {self.sec:,}'  # pattern: f'{value:,}' for thousands comma separator
        return s

    def write_spreadsheet(self, fname):
        print('writing spreadsheet data from %s buffer to %s' % (self.tsh.name, fname))
        np.savetxt(fname, self.xyz, delimiter=',')

    def write_csv_in_counts(self, fname, fmt='%.1f'):
        """write buffer (array) of XYZ counts to 3-column CSV (x,y,z)"""
        self.logger.info('Writing %s buffer to CSV file "%s".' % (self.tsh.name, fname))
        np.savetxt(fname, self.xyz, delimiter=',', fmt=fmt)

    def add(self, more):

        if self.is_full:
            self.logger.warning('Buffer already full, array shape is %s.' % str(self.xyz.shape))
            return

        offset = more.shape[0]
        if self.idx + offset > self.xyz.shape[0]:
            offset = self.xyz[self.idx:, :].shape[0]
            self.xyz[self.idx:self.idx + offset, :] = more[0:offset, :]
            # self.logger.debug('Buffer added %d xyz records.' % offset)
            self.is_full = True
            self.logger.warning('Buffer now full, so stop adding, the array shape is %s.' % str(self.xyz.shape))
        else:
            self.xyz[self.idx:self.idx + offset, :] = more
            # self.logger.debug('Buffer added %d xyz records.' % offset)

        # print(self.idx, self.idx + offset)
        self.idx = self.idx + offset


# FIXME make this a method in TshAccelBuffer class
def raw_data_from_socket(ip_addr, buff, port=9750):
    """establish socket connection to [tsh] (ip_addr)ess on data port (9750) and show pertinent data"""

    # crude attempt at identifying columns in log entriess
    # module_logger.debug(get_buff_header())

    previous_count = -1

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_addr, port))
        while not buff.is_full:
            data = s.recv(8192)  # FIXME power of 2 is recommended, but not sure what optimum value to use here
            if data:
                if len(data) >= 16:  # FIXME Why 80 in Ted's code [maybe it was MySQL db goodness?]; MAYBE > ZERO??

                    # get selector value
                    byte2 = struct.unpack('c', bytes([data[40]]))[0]
                    byte3 = struct.unpack('c', bytes([data[41]]))[0]
                    selector = ord(byte2) * 256 + ord(byte3)

                    # make sure we have selector that corresponds to a TshesAccelPacket; either real-time or replay
                    accel_pkt = (selector == 170) or (selector == 171)
                    if accel_pkt:

                        # examine structure before "Data" payload (TshesAccelPacket), starts @ byte 44 of tshes message
                        tm = TshesMessage(data)
                        # tm.enum_bytes()

                        # --- NOW HERE WE TRANSITION TO TshesAccelPacket ---

                        # tsh identifier
                        tshes_id = data[44:60]
                        tshes_id = tshes_id.replace(b'-', b'').replace(b'\0', b'')  # delete dashes and nulls
                        tshes_id = tshes_id[-4:]  # keep last 4 characters only, i.e., "es13"

                        # counter
                        counter = struct.unpack('!I', data[60:64])[0]  # Network byte order

                        # let's throw in a line with dashes near counter column when we detect one or more missing count
                        if counter - previous_count != 1:
                            module_logger.debug(' '*60 + '-'*7)
                        previous_count = counter

                        # timestamp
                        sec, usec = struct.unpack('!II', data[64:72])  # Network byte order
                        timestamp = sec + usec / 1000000.0

                        # packet_status
                        packet_status = struct.unpack('!i', data[72:76])[0]  # Network byte order

                        # number of samples
                        num_samples = struct.unpack('!i', data[76:80])[0]  # Network byte order

                        # get rate and cutoff_freq from packet status
                        rate_bits = (packet_status & 0x0f00) >> 8
                        rate, cutoff_freq = TSH_RATES[rate_bits]

                        # get gain and input from packet status
                        gain_bits = packet_status & 0x001f
                        gain, inp = TSH_GAINS[gain_bits]

                        # get unit from packet status
                        unit_bits = (packet_status & 0x0060) >> 5
                        unit = TSH_UNITS[unit_bits]

                        # get adjustment from packet status
                        adj_bits = (packet_status & 0x0080) >> 7
                        adjustment = 'no-compensation'
                        if adj_bits == 1:
                            adjustment = 'temperature-compensation'

                        # compute end time from start, number of samples and rate
                        end_time = timestamp + (num_samples - 1) / rate

                        # build array of accel data
                        xyz = []

                        # compute delta samples missing from current volley of bytes; 1 sample = 16 bytes (x,y,z,dio)
                        received_samples, left_over_bytes = divvy_up(len(data[80:]))
                        deficit_samples = num_samples - received_samples
                        deficit_bytes = deficit_samples * 16 - left_over_bytes

                        # append the samples we have received so far
                        for i in range(received_samples):
                            start = 80 + 16 * i
                            stop = start + 16
                            x, y, z, dio = struct.unpack('!fffI', data[start:stop])  # Network byte order
                            # we are ignoring digital io status (dio)
                            # self.handleDigitalIOstatus(digitalIOstatus, i)
                            # if convert:
                            #     x, y, z = x * mx + bx, y * my + by, z * mz + bz
                            xyz.append((x, y, z))

                        # NOTE: This next bit of code shows we now know we're dealing with stream-based protocol!

                        # keep remainder bytes & prepend'em to balance of samples we'll get for TshesAccelPacket struct
                        more_data = data[stop:]
                        more_data += recvall(s, deficit_bytes)  # remainder of bytes we need to get num_samples filled

                        # append deficit samples to get a total of num_samples (promised in TshesAccelPacket's "Prefix")
                        for i in range(deficit_samples):
                            start = 16 * i
                            stop = start + 16
                            x, y, z, dio = struct.unpack('!fffI', more_data[start:stop])  # Network byte order
                            xyz.append((x, y, z))

                        # module_logger.debug("{:>4} {} {:>4s} {:>10d} {} {:>5d} {:>3d} {:>6.1f} {:>6.2f} {:>4.1f} {:>6s}"
                        #       " {:>6s} {:>15s} {} {:>3d} {:>3d} {:>3d} {:>4d}".format(
                        #     len(data),
                        #     str(tm).replace('\n', ' '),
                        #     tshes_id.decode('utf-8'),
                        #     counter,
                        #     unix_to_human_time(timestamp),
                        #     packet_status,
                        #     num_samples,
                        #     rate,
                        #     cutoff_freq,
                        #     gain,
                        #     inp,
                        #     unit,
                        #     adjustment,
                        #     unix_to_human_time(end_time),
                        #     received_samples,
                        #     left_over_bytes,
                        #     deficit_samples,
                        #     stop - left_over_bytes)
                        # )

                        buff.add(np.array(xyz))

                else:
                    print('unhandled branch with len(data) = %d' % len(data))

            else:
                break


def demo_buffer():

    import os
    import platform

    # fake/dummy arguments for buffer creation
    sec = TSH_BUFFER_SEC  # how many seconds-worth of TSH data (x,y,z acceleration values)
    fs, k = 250.0, 0  # fake/dummy arguments for sample rate and gain

    module_logger.warning('ASSUMING the TSH is configured (sample rate, gain, and so on).')

    # create data buffer -- at some pt in code before we need mean(counts), probably just after GSS min/max found
    tsh = Tsh('es14', fs, k)
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
    buffer.write_csv_in_counts(csv_file, fmt='%.1f')


def demo_proto():

    from tshcal.secret import TSHES14_IPADDR

    HOST = TSHES14_IPADDR  # string with tsh's ip address
    PORT = 9750  # port used by tsh to transmit accel. data

    # fake/dummy arguments for buffer creation
    sec = TSH_BUFFER_SEC  # how many seconds-worth of TSH data (x,y,z acceleration values)
    fs, k = 250.0, 0  # fake/dummy arguments for sample rate and gain

    module_logger.warning('ASSUMING the TSH is configured (sample rate, gain, and so on).')

    # create data buffer -- at some pt in code before we need mean(counts), probably just after GSS min/max found
    tsh = Tsh('tshes-14', fs, k)
    tsh_buff = TshAccelBuffer(tsh, sec, logger=module_logger)
    raw_data_from_socket(HOST, tsh_buff, port=PORT)

    print(tsh_buff.xyz)

    raise SystemExit


if __name__ == '__main__':

    demo_buffer()
