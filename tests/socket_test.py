#!/usr/bin/env python3

import sys
import json
import struct
import socket
import datetime
from tshcal.secret import TSHES13_IPADDR, PIHOLE_IPADDR, STAN_IPADDR
from tshcal.common.tshes_params_packet import TshesMessage
from tshcal.lowpass.lowpass import SamsTshEs


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


def raw_data_from_socket(ip_addr, port=9750):
    """establish socket connection to tsh on data port (9750) and show raw data"""

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip_addr, port))

    while True:
        data = s.recv(1024)
        if data:
            if len(data) >= 80:

                # examine bytes, just enough (similar to "peek" Eric noted) to be sure we are onto a TshesAccelPacket

                # get selector value
                byte2 = struct.unpack('c', bytes([data[40]]))[0]
                byte3 = struct.unpack('c', bytes([data[41]]))[0]
                selector = ord(byte2) * 256 + ord(byte3)

                # make sure we have selector that corresponds to a TshesAccelPacket; either real-time or replay
                accel_pkt = (selector == 170) or (selector == 171)  # || (selector == 177)
                if accel_pkt:

                    # examine header/wrapper around "Data", TshesAccelPacket, which starts @ byte 44 of "tshes message"
                    tm = TshesMessage(data)
                    # tm.enum_bytes()

                    # --- HERE WE TRANSITION TO TshesAccelPacket INFO ---

                    # tsh identifier
                    tshes_id = data[44:60]
                    tshes_id = tshes_id.replace(b'-', b'').replace(b'\0', b'')  # delete dashes and nulls
                    tshes_id = tshes_id[-4:]  # keep last 4 characters only, i.e., "es13"

                    # counter
                    counter = struct.unpack('!I', data[60:64])[0]  # Network byte order

                    # timestamp
                    sec, usec = struct.unpack('!II', data[64:72])  # Network byte order
                    timestamp = sec + usec / 1000000.0

                    # TODO convert timestamp to human readable

                    # packet_status
                    packet_status = struct.unpack('!i', data[72:76])[0]  # Network byte order

                    # number of samples
                    num_samples = struct.unpack('!i', data[76:80])[0]  # Network byte order

                    # TODO get end_time from timestamp [which effectively is start_time], num_samples and rate

                    print(str(tm).replace('\n', ' '), tshes_id, counter, timestamp, packet_status, num_samples)

                    # pkt = SamsTshEs(data)

                    # print(pkt)

        else:
            break

    s.close()


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
    #HOST = '192.112.237.68'
    PORT = 9750  # port used by tsh to transmit accel. data
    #eric_example(HOST, PORT)
    raw_data_from_socket(HOST, PORT)
    sys.exit(0)

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
