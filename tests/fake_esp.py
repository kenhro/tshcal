#!/usr/bin/env python3

from time import sleep
from serial.serialposix import Serial
from newportESP import ESP, Axis

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
        self._pos = -999.999

    def axis(self, axis_index=1):
        """create fake Axis object"""
        return FakeAxis(self, axis=axis_index)


class FakeAxis(Axis):

    def move_to(self, pos, wait=False):
        """go to absolute position (wait if 2nd axis is True)"""
        self.write("PA" + str(pos))
        if wait:
            sleep(0.25)
        self._pos = pos - 1.0

    @property
    def position(self):
        """current position (angle in degrees -- not mm, right?_"""
        return self._pos


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
    stage.move_to(90, True)          # move to position
    print(stage.position)

if __name__ == '__main__':
    demo()
