#!/usr/bin/env python3

import sys
import json
import struct
import socket
import datetime
import numpy as np
import matplotlib.pyplot as plt

from tshcal.secret import TSHES13_IPADDR
from tshcal.filters.lowpass import ButterworthLowpassFilt
from tshcal.common.tshes_params_packet import TshesMessage
from tshcal.common.time_utils import unix_to_human_time
from tshcal.common.plot_utils import TshRealtimePlot
from tshcal.common.sci_utils import is_outlier


def eric_example(ip_addr, port=9750):
    """establish socket connection to tsh on data port (9750); Eric's proof of concept"""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_addr, port))

    while True:
        data = s.recv(1024)

        if data:
            print('Received', repr(data))
        else:
            break

    s.close()


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


def print_header():
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
    print(' '.join(s))


def raw_data_from_socket(ip_addr, bytes_ctr, port=9750):
    """establish socket connection to [tsh] (ip_addr)ess on data port (9750) and show pertinent data"""

    print_header()
    previous_count = -1

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_addr, port))
        while True:
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
                            print(' '*60 + '-'*7)
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
                        if rate_bits == 0:
                            rate, cutoff_freq = 7.8125, 3.2
                        elif rate_bits == 1:
                            rate, cutoff_freq = 15.625, 6.3
                        elif rate_bits == 2:
                            rate, cutoff_freq = 31.25, 12.7
                        elif rate_bits == 3:
                            rate, cutoff_freq = 62.5, 25.3
                        elif rate_bits == 4:
                            rate, cutoff_freq = 125.0, 50.6
                        elif rate_bits == 5:
                            rate, cutoff_freq = 250.0, 101.4
                        elif rate_bits == 6:
                            rate, cutoff_freq = 500.0, 204.2
                        elif rate_bits == 7:
                            rate, cutoff_freq = 1000.0, 408.5
                        elif rate_bits == 8:
                            rate, cutoff_freq = 125.0, 23.5
                        else:
                            # FIXME how do we gracefully proceed with wrong rate info?
                            rate, cutoff_freq = 0.0, 0.0

                        # get gain and input from packet status
                        gain_bits = packet_status & 0x001f
                        if gain_bits == 0:
                            gain, inp = 1.0, 'Ground'  # _input_ is not used as far as I can tell
                        elif gain_bits == 1:
                            gain, inp = 2.5, 'Ground'
                        elif gain_bits == 2:
                            gain, inp = 8.5, 'Ground'
                        elif gain_bits == 3:
                            gain, inp = 34.0, 'Ground'
                        elif gain_bits == 4:
                            gain, inp = 128.0, 'Ground'
                        elif gain_bits == 8:
                            gain, inp = 1.0, 'Test'
                        elif gain_bits == 9:
                            gain, inp = 2.5, 'Test'
                        elif gain_bits == 10:
                            gain, inp = 8.5, 'Test'
                        elif gain_bits == 11:
                            gain, inp = 34.0, 'Test'
                        elif gain_bits == 12:
                            gain, inp = 128.0, 'Test'
                        elif gain_bits == 16:
                            gain, inp = 1.0, 'Signal'
                        elif gain_bits == 17:
                            gain, inp = 2.5, 'Signal'
                        elif gain_bits == 18:
                            gain, inp = 8.5, 'Signal'
                        elif gain_bits == 19:
                            gain, inp = 34.0, 'Signal'
                        elif gain_bits == 20:
                            gain, inp = 128.0, 'Signal'
                        elif gain_bits == 24:
                            gain, inp = 1.0, 'Vref'
                        elif gain_bits == 25:
                            gain, inp = 1.0, 'Sensor test'
                        elif gain_bits == 26:
                            gain, inp = 2.0, 'Sensor test'
                        else:
                            # FIXME how do we gracefully proceed with wrong gain info?
                            gain, inp = 0.0, 'Unknown'

                        # get unit from packet status
                        unit_bits = (packet_status & 0x0060) >> 5
                        if unit_bits == 0:
                            unit = 'counts'
                        elif unit_bits == 1:
                            unit = 'volts'
                        elif unit_bits == 2:
                            unit = 'g'
                        else:
                            # FIXME how do we gracefully proceed with wrong units info?
                            unit = 'g'

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

                        # print('len(data) = %d' % len(data), 'tm:[', str(tm).replace('\n', ' '), ']', tshes_id, counter,
                        #       unix_to_human_time(timestamp), packet_status, num_samples, rate, cutoff_freq, gain,
                        #       input, unit, adjustment, unix_to_human_time(end_time), received_samples, left_over_bytes,
                        #       deficit_samples, stop)

                        print("{:>4} {} {:>4s} {:>10d} {} {:>5d} {:>3d} {:>6.1f} {:>6.2f} {:>4.1f} {:>6s}"
                              " {:>6s} {:>15s} {} {:>3d} {:>3d} {:>3d} {:>4d}".format(
                            len(data),
                            str(tm).replace('\n', ' '),
                            tshes_id.decode('utf-8'),
                            counter,
                            unix_to_human_time(timestamp),
                            packet_status,
                            num_samples,
                            rate,
                            cutoff_freq,
                            gain,
                            inp,
                            unit,
                            adjustment,
                            unix_to_human_time(end_time),
                            received_samples,
                            left_over_bytes,
                            deficit_samples,
                            stop - left_over_bytes
                        )
                        )

                else:
                    print('unhandled branch with len(data) = %d' % len(data))

            else:
                break


def axis_str2idx(a):
    """return index (0, 1, 2) for given axis designation (x, y, z)"""
    d = {'x': 0, 'y': 1, 'z': 2}
    return d[a.lower()[0]]


def plot_raw_data_from_socket(fs, fc, ax, ip_addr, port=9750, norder=4, has_nan=False):
    """establish socket connection to [tsh] (ip_addr)ess on port (9750) and plot (ax)is"""

    # create 4th order low-pass butterworth filter
    lowpass_filt = ButterworthLowpassFilt(fs, fc, norder=norder, has_nan=has_nan)

    disp_sec = 30
    disp_pts = int(np.ceil(fs * disp_sec))
    display = TshRealtimePlot(fs, disp_pts=disp_pts, filt=lowpass_filt, mask_outlier=True)

    # other parameters related to plotting
    sleep_sec = 0.05  # a built-in breather for animated plotting loop (keep this less than 0.25 seconds or so)
    # delta_sec = 1.0 / fs

    print_header()
    previous_count = -1

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_addr, port))
        while True:
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

                        # let's throw in a line with dashes near counter when we detect one or more missing count
                        if counter - previous_count != 1:
                            print(' '*60 + '-'*7)
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
                        if rate_bits == 0:
                            rate, cutoff_freq = 7.8125, 3.2
                        elif rate_bits == 1:
                            rate, cutoff_freq = 15.625, 6.3
                        elif rate_bits == 2:
                            rate, cutoff_freq = 31.25, 12.7
                        elif rate_bits == 3:
                            rate, cutoff_freq = 62.5, 25.3
                        elif rate_bits == 4:
                            rate, cutoff_freq = 125.0, 50.6
                        elif rate_bits == 5:
                            rate, cutoff_freq = 250.0, 101.4
                        elif rate_bits == 6:
                            rate, cutoff_freq = 500.0, 204.2
                        elif rate_bits == 7:
                            rate, cutoff_freq = 1000.0, 408.5
                        elif rate_bits == 8:
                            rate, cutoff_freq = 125.0, 23.5
                        else:
                            # FIXME how do we gracefully proceed with wrong rate info?
                            rate, cutoff_freq = 0.0, 0.0

                        if rate != fs:
                            raise RuntimeError('sample rate does not match fs input')

                        # get gain and input from packet status
                        gain_bits = packet_status & 0x001f
                        if gain_bits == 0:
                            gain, inp = 1.0, 'Ground'  # _input_ is not used as far as I can tell
                        elif gain_bits == 1:
                            gain, inp = 2.5, 'Ground'
                        elif gain_bits == 2:
                            gain, inp = 8.5, 'Ground'
                        elif gain_bits == 3:
                            gain, inp = 34.0, 'Ground'
                        elif gain_bits == 4:
                            gain, inp = 128.0, 'Ground'
                        elif gain_bits == 8:
                            gain, inp = 1.0, 'Test'
                        elif gain_bits == 9:
                            gain, inp = 2.5, 'Test'
                        elif gain_bits == 10:
                            gain, inp = 8.5, 'Test'
                        elif gain_bits == 11:
                            gain, inp = 34.0, 'Test'
                        elif gain_bits == 12:
                            gain, inp = 128.0, 'Test'
                        elif gain_bits == 16:
                            gain, inp = 1.0, 'Signal'
                        elif gain_bits == 17:
                            gain, inp = 2.5, 'Signal'
                        elif gain_bits == 18:
                            gain, inp = 8.5, 'Signal'
                        elif gain_bits == 19:
                            gain, inp = 34.0, 'Signal'
                        elif gain_bits == 20:
                            gain, inp = 128.0, 'Signal'
                        elif gain_bits == 24:
                            gain, inp = 1.0, 'Vref'
                        elif gain_bits == 25:
                            gain, inp = 1.0, 'Sensor test'
                        elif gain_bits == 26:
                            gain, inp = 2.0, 'Sensor test'
                        else:
                            # FIXME how do we gracefully proceed with wrong gain info? or do we?
                            gain, inp = 0.0, 'Unknown'

                        # get unit from packet status
                        unit_bits = (packet_status & 0x0060) >> 5
                        if unit_bits == 0:
                            unit = 'counts'
                        elif unit_bits == 1:
                            unit = 'volts'
                        elif unit_bits == 2:
                            unit = 'g'
                        else:
                            # FIXME how do we gracefully proceed with wrong units info? or do we?
                            unit = 'g'

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

                        # NOTE: This next bit of code shows that we know we're dealing with stream-based protocol!

                        # keep remainder bytes & prepend'em to balance of samples we'll get for TshesAccelPacket struct
                        more_data = data[stop:]
                        more_data += recvall(s, deficit_bytes)  # remainder of bytes we need to get num_samples filled

                        # append deficit samples to get a total of num_samples (promised in TshesAccelPacket's "Prefix")
                        for i in range(deficit_samples):
                            start = 16 * i
                            stop = start + 16
                            x, y, z, dio = struct.unpack('!fffI', more_data[start:stop])  # Network byte order
                            xyz.append((x, y, z))

                        # print('len(data) = %d' % len(data), 'tm:[', str(tm).replace('\n', ' '), ']', tshes_id, counter,
                        #       unix_to_human_time(timestamp), packet_status, num_samples, rate, cutoff_freq, gain,
                        #       input, unit, adjustment, unix_to_human_time(end_time), received_samples, left_over_bytes,
                        #       deficit_samples, stop)

                        print("{:>4} {} {:>4s} {:>10d} {} {:>5d} {:>3d} {:>6.1f} {:>6.2f} {:>4.1f} {:>6s}"
                              " {:>6s} {:>15s} {} {:>3d} {:>3d} {:>3d} {:>4d}".format(
                            len(data),
                            str(tm).replace('\n', ' '),
                            tshes_id.decode('utf-8'),
                            counter,
                            unix_to_human_time(timestamp),
                            packet_status,
                            num_samples,
                            rate,
                            cutoff_freq,
                            gain,
                            inp,
                            unit,
                            adjustment,
                            unix_to_human_time(end_time),
                            received_samples,
                            left_over_bytes,
                            deficit_samples,
                            stop - left_over_bytes
                        )
                        )

                        # get index for desired axis to be plotted
                        idx = axis_str2idx(ax)

                        # dispense with most recent values
                        base_time = datetime.datetime.utcfromtimestamp(timestamp)
                        t_values = np.array([base_time + datetime.timedelta(seconds=i/fs) for i in range(len(xyz))])
                        # print(t_values[0], t_values[-1], len(xyz))
                        y_values = np.array([i[idx] for i in xyz])
                        display.add(t_values, y_values)
                        # base_time = t_values[-1] + datetime.timedelta(seconds=delta_sec)
                        plt.pause(sleep_sec)

                else:
                    print('unhandled branch with len(data) = %d' % len(data))

            else:
                break


def ken_json_echo_client_example(ip_addr, port, json_data):
    """a simple echo example...bounce data off the server and show what we get back here

    :param ip_addr: string with ip address; pihole is RaspberryPi
    :param port: must match on here on client and "there" on server side
    :param json_data: json.dumps(your_data)
    :return: number of bytes received, that we bounced off the echo server
    """

    # encode and send json dumps data
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ip_addr, port))
        s.sendall(json_data.encode())
        data = s.recv(1024)

    # decode the encoded json dumps data that we bounced off the server
    data_decoded = data.decode()

    # now we "unjsonify" to get dict from json.loads
    data_dict = json.loads(data_decoded)

    # show data we got back from server
    print('Received:', repr(data_dict))
    for k, v in data_dict.items():
        print(k, v)

    return sys.getsizeof(data_decoded)


def main():
    """some other testing may be appropriate here too, but try this for now"""

    HOST = TSHES13_IPADDR  # string with es13's ip address
    PORT = 9750  # port used by tsh to transmit accel. data
    # raw_data_from_socket(HOST, PORT)
    fs, fc = 250.0, 10.0
    plot_raw_data_from_socket(fs, fc, 'y', HOST, PORT)
    sys.exit(-2)

    # hit a simple echo server running on my pihole
    HOST = STAN_IPADDR  # string with rpi server's ip address
    PORT = 65432  # port being used for this service by the server
    arr1 = ([1, 2, 3, 4, 5, 6], [11, 22, 33, 44, 55, 66])
    arr2 = ([0.1, 0.2, 0.3, 0.4, 0.5], [1.1, 2.2, 3.3, 4.4, 5.5])
    val3 = 'green_eggs'
    d4 = datetime.datetime.now()  # JSON cannot serialize datetime...so need default=str keyword arg
    d = dict()
    d['a'] = arr1
    d['b'] = arr2
    d['c'] = val3
    d['d'] = d4
    d['e'] = 5
    d['f'] = 6
    d['g'] = 7
    d['h'] = 8
    d['i'] = 9
    json_dumps_data = json.dumps(d, default=str)

    print('Sending %d bytes' % sys.getsizeof(json_dumps_data))

    num_bytes = ken_json_echo_client_example(HOST, PORT, json_dumps_data)

    print('Received %d bytes' % num_bytes)

    return 0


if __name__ == '__main__':
    sys.exit(main())
