#!/usr/bin/env python3

from serial.serialposix import Serial
from newportESP import ESP

DEBUG_PRINT = False  # use True for debug print lines to stdout; otherwise, False to suppress prints in FakeSerial


class FakeESP(ESP):

    def __init__(self, port):
        self.lock = None
        self.ser = FakeSerial(port=port,
                              baudrate=19200,
                              bytesize=8,
                              timeout=1,
                              parity='N',
                              rtscts=1)
        self.Abort = self.abort


class FakeSerial(Serial):

    def open(self):
        if DEBUG_PRINT:
            print('Serial port opened.')

    def close(self):
        if DEBUG_PRINT:
            print('Serial port closed.')

    def read(self, size=1):
        if DEBUG_PRINT:
            print('Serial port read.')

    def write(self, data):
        if DEBUG_PRINT:
            print('Serial port write', data)


def demo():
    esp = FakeESP('/fake/ttyUSB0')   # open communication with controller
    stage = esp.axis(1)              # open axis no 1
    stage.move_to(90)                # move to position


if __name__ == '__main__':
    demo()
