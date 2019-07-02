"""
ZIN Nomenclature:
-----------------

MMSAMS Calibration Fixture (MCF) – A 3-stage DC motor/table assembly modified to hold a SAMS TSH-ES sensor in a desired
position relative to the gravity vector.

Newport ESP301 (ESP) Integrated 3-Axis Motion Controller – Controller/driver used for fine control of the MMSAMS
Calibration Test Fixture’s 3 stages.

"""

from newportESP import ESP


class FakeESP(ESP):

    def __init__(self, port):
        """:param port: Fake serial port connected to the controller."""
        self.lock = None
        self.ser = None
        self.Abort = self.abort


esp = FakeESP('/dev/ttyUSB0')
stage = esp.axis(1)   # open axis no 1
stage.move_to(1.2, True)

raise SystemExit


class MmsamsCalibrationFixture(object):

    def __init__(self, esp, tsh, cfg):
        self.esp = esp
        self.tsh = tsh
        self.cfg = cfg

    def __str__(self):
        s = '%s' % self.__class__.__name__
        return s

    def move_to_rough_home(self, pos):
        pass

    def get_tsh(self):
        pass


def main():
    try:
        esp = None
    except:
        esp = None
    tsh = None
    cfg = None
    mfc = MmsamsCalibrationFixture(esp, tsh, cfg)
    print(mfc)


if __name__ == '__main__':
    main()
