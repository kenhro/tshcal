#!/usr/bin/env python3

import struct
from time import time
import MySQLdb as sql

from tshcal.secret import SDB, SUSER, SPASSWD
from tshcal.common.time_utils import unix_to_human_time


class WrongTypeOfPacket(Exception):
    def __init__(self, args=None):
        if args:
            self.args = args


def binary_coded_decimal(char):
    """byte to BCD conversion"""
    byte = ord(char)
    tens = (byte & 0xf0) >> 4
    ones = (byte & 0x0f)
    if (tens > 9) or (ones > 9):
        raise BCDConversionException('tens: %s, ones:%s' % (tens, ones))
    return tens*10+ones


def sql_connect(command, shost='localhost', suser=SUSER, spasswd=SPASSWD, sdb=SDB):
    """SQL helper routines ---------------------------------------------------------------
    create a connection (with possible defaults), submit command, return all results
    try to do all connecting through this function to handle exceptions"""
    sqlRetryTime =30
    repeat = 1
    while repeat:
        try:
            con = sql.Connection(host=shost, user=suser, passwd=spasswd, db=sdb)
            cursor = con.cursor()
            cursor.execute(command)
            results = cursor.fetchall()
            # print(results)
            repeat = 0
            cursor.close()
            con.close()
        except MySQLError as msg:
            t = unix_to_human_time(time(), 1) + '\n' + msg[1] + '\nMySQL call failed, will try again in %s seconds' % sqlRetryTime
            printLog(t)
            if idleWait(sqlRetryTime):
                return []

    return results


def guess_packet(packet, showWarnings=0):
    """try to create a packet of the appropriate type"""
    subtypes = [SamsTshEs, Sams2Packet]
    for i in subtypes:
        try:
            p = i(packet, showWarnings=0)
            return p
        except WrongTypeOfPacket:
            pass
    if showWarnings:
        t = unix_to_human_time(time(), 1) + 'unknown packet type detected'
        printLog(t)
    return AccelPacket(packet)


DigitalIOstatusHolder = {}  # global dictionary to hold SAMS TSH-ES DigitalIOstatus between packets


class AccelPacket(object):
    """class to represent all types of accel data (SAMS2, MAMS, etc.)"""

    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet):
        self.p = packet
        self._rep_ = None
        self.type = 'unknown'
        self._time_ = None
        self._dqmIndicator_ = 0
        self._additionalDQMtext_ = ''

    # return the name of the data directory appropriate for this packet:
    def dataDirName(self):
        return self.type

        # return anything that should be inserted into the DQM header

    def additionalDQM(self):
        return self._additionalDQMtext_

    # add something to the DQM header (note: only one packet in the PAD file is checked for
    #    additionalDQM, so you can't just call this any time and expect it to show up)
    def addAdditionalDQM(self, text):
        self._additionalDQMtext_ = self._additionalDQMtext_ + text

    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        raise Exception('Subclass responsibility')

    # return sensor name appropriate for this packet (for database table)
    def name(self):
        raise Exception('Subclass responsibility')

    # return xyz info appropriate for this packet
    def xyz(self):
        raise Exception('Subclass responsibility')

    # return txyz info appropriate for this packet
    def txyz(self):
        raise Exception('Subclass responsibility')

    # return extraColumns info appropriate for this packet
    def extraColumns(self):
        return None

    # return starting time appropriate for this packet
    def time(self):
        raise Exception('Subclass responsibility')

    # return ending time appropriate for this packet
    def endTime(self):
        raise Exception('Subclass responsibility')

    # return data sample appropriate for this packet
    def rate(self):
        raise Exception('Subclass responsibility')

    # return header info in XML format for this packet
    def xmlHeader(self):
        raise Exception('Subclass responsibility')

    # return true if this packet is contiguous with the supplied packet
    def contiguous(self, other):
        if not other:
            # print('contiguous: no other')
            return 0
        if self.type != other.type:  # maybe we should throw an exception here
            # print('contiguous: other type mis-match')
            return 0
        if self.rate() != other.rate():
            # print('contiguous: other rate mis-match')
            return 0
        if self._dqmIndicator_ != other._dqmIndicator_:
            # print('contiguous: other dqm mis-match')
            return 0
        ostart = other.time()
        oend = other.endTime()
        start = self.time()
        if self.rate() == 0:  # non-periodic data
            # print('contiguous: OK non-periodic')
            return (start > oend)
        gap = start - oend
        # when samples == 1, any jitter can cause a delay that shows up as a gap, so inflate allowableGap
        if self.samples() == 1:
            allowAbleGap = 1.5 * self.samples() / self.rate()
        else:
            allowAbleGap = self.samples() / self.rate()
        result = (start >= ostart) and (gap <= allowAbleGap)
        # if not result:
        # print('contiguous:%s ostart:%.4lf oend:%.4lf start:%.4lf gap:%.4lf allowAbleGap:%.4lf') % (result, ostart, oend, start, gap, allowAbleGap)
        return result

    # print a representation of this packet
    def dump(self, accelData=0):
        if not self._rep_:
            header = self.header()
            hkeys = list(header.keys())
            className = split(str(self.__class__), '.')[1]
            self._rep_ = '%s(' % className
            for i in hkeys:
                if i == 'time' or i == 'endTime':  # work around Python 3 decimal place default for times
                    self._rep_ = self._rep_ + ' %s:%.4f' % (i, header[i])
                else:
                    self._rep_ = self._rep_ + ' %s:%s' % (i, header[i])
            if accelData:
                self._rep_ = self._rep_ + '\ndata:'
                for j in self.xyz():
                    self._rep_ = self._rep_ + '\n%.7e %.7e %.7e' % tuple(j)
        #                for j in self.txyz():
        #                    self._rep_ = self._rep_ + '\n%.4f %.7e %.7e %.7e' % j
        return self._rep_

    def hexDump(self):
        self._hex_ = ''
        start = 0
        size = 16
        ln = len(self.p)
        while start < ln:
            # print line number
            line = '%04x  ' % start
            # print hex representation
            c = 0
            asc = self.p[start:min(start + size, ln)]
            for b in asc:
                if c == 8:
                    line = line + '  '
                # line = line + '%02x ' % ord(b)
                line = line + format(b, '02x') + ' '
                c = c + 1
            # line = ljust(line, 58) + '"'
            line = line.ljust(58) + '"'
            # print ascii representation, replace unprintable characters with spaces [or now it's b'\x00' - kh]
            for i in range(len(asc)):
                # if ord(asc[i]) < 32 or ord(asc[i]) == 209:
                if asc[i] < 32 or asc[i] == 209:
                    asc = asc[:i] + b'\x00' + asc[i+1:]
            line = line + str(asc) + '"\n'
            self._hex_ = self._hex_ + line
            start = start + size
        return self._hex_


class Sams2Packet(AccelPacket):
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        AccelPacket.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._sams2_ = None
        self._samples_ = None
        self._adjustment_ = None
        if not self.isSams2Packet():
            raise WrongTypeOfPacket
        self.type = 'sams2_accel'
        self._name_ = None
        self._header_ = {}
        self._eeId_ = None
        self._seId_ = None
        self._head_ = None
        self._status_ = None
        self._rate_ = None
        self._gain_ = None
        self._unit_ = None
        self._time_ = None
        self._endTime_ = None
        self._xyz_ = []
        self._txyz_ = []
        self._xmlHeader_ = None

    def dataDirName(self):
        return 'sams2_accel_' + self.seId()

    def measurementsPerSample(self):
        return 3

        # return true if this packet is contiguous with the supplied packet

    # sams-ii packets vary in size, we need to correctly catch a missing minimum size packet
    # every half second, packets of the following sizes are sent:
    #     at   62.5 Hz: 32 or 31
    #     at  125   Hz: 63 or 62
    #     at  250   Hz: 74, 51
    #     at  500   Hz: 74, 74, 74, 28
    #     at 1000   Hz: 74, 74, 74, 74, 74, 74, 56
    def contiguous(self, other):
        minSamples = {62.5: 31, 125.0: 62, 250.0: 51, 500.0: 28, 1000.0: 56}
        if not other:
            # print('contiguous: no other')
            return 0
        if self.type != other.type:  # maybe we should throw an exception here
            # print('contiguous: other type mis-match')
            return 0
        if self.rate() != other.rate():
            # print('contiguous: other rate mis-match')
            return 0
        if self._dqmIndicator_ != other._dqmIndicator_:
            # print('contiguous: other dqm mis-match')
            return 0
        ostart = other.time()
        oend = other.endTime()
        start = self.time()
        if self.rate() == 0:  # non-periodic data
            # print('contiguous: OK non-periodic')
            return (start > oend)
        gap = start - oend
        allowAbleGap = minSamples[self.rate()] / self.rate()
        result = (start >= ostart) and (gap <= allowAbleGap)
        # if not result:
        # print('contiguous:%s ostart:%.4lf oend:%.4lf start:%.4lf gap:%.4lf') % (result, ostart, oend, start, gap)
        return result

    # name of the database table this data should be in (no dashes)
    def name(self):
        if not self._name_:
            self._name_ = self.seId()
        return self._name_

    # return true if this appears to be a sams2 acceleration packet
    def isSams2Packet(self):  # struct.unpack doesn't seem to think 'h' is 2 bytes

        if not self._sams2_:
            if len(self.p) < 68:
                self._sams2_ = 0
                if self._showWarnings_:
                    t = 'SAMSII packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                    t = t + ' packet too short (%s) to be a sams-ii acceleration packet' % len(self.p)
                    printLog(t)
                return self._sams2_
            # byte0 = struct.unpack('c', self.p[0])[0]
            # byte1 = struct.unpack('c', self.p[1])[0]
            byte0 = struct.unpack('c', bytes([self.p[0]]))[0]
            byte1 = struct.unpack('c', bytes([self.p[1]]))[0]
            if not (byte0 == chr(0xda) and byte1 == chr(0xbe)):
                self._sams2_ = 0
                if self._showWarnings_:
                    t = 'SAMSII packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                    t = t + ' packet cannot be sams-ii accel because it does not start with 0xdabe'
                    printLog(t)
                return self._sams2_
            byte2 = struct.unpack('c', self.p[12])[0]
            byte3 = struct.unpack('c', self.p[13])[0]
            accelpacket = (byte2 == chr(100)) and (byte3 == chr(0))
            if not accelpacket and self._showWarnings_:
                self._sams2_ = 0
                t = 'SAMSII packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                t = t + ' packet cannot be sams-ii accel because it does not have 0x6400 at offset 12'
                printLog(t)
                return self._sams2_
            if len(self.p) < 52 + 16 * self.samples():
                self._sams2_ = 0
                t = 'SAMSII packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                t = t + ' packet is not a complete sams-ii accel packet, %s samples are not present' % self.samples()
                printLog(t)
                return self._sams2_
            self._sams2_ = 1
            self.addAdditionalDQM(self.adjustment())
        return self._sams2_

    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % unix_to_human_time(self.time())
            self._xmlHeader_ = self._xmlHeader_ + '\t<Gain>%s</Gain>\n' % self.gain()
            # self._xmlHeader_ = self._xmlHeader_ + '\t<Units>%s</Units>\n' % self.unit()
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % (self.rate() * 0.4)
        return self._xmlHeader_

    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['eeId'] = self.eeId()
            self._header_['seId'] = self.seId()
            self._header_['head'] = self.head()
            self._header_['isSams2Packet'] = self.isSams2Packet()
            self._header_['status'] = self.status()
            self._header_['rate'] = self.rate()
            self._header_['gain'] = self.gain()
            self._header_['unit'] = self.unit()
            self._header_['adjustment'] = self.adjustment()
            self._header_['samples'] = self.samples()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
        return self._header_

    def eeId(self):
        if not self._eeId_:
            self._eeId_ = self.p[16:24]
            self._eeId_ = replace(self._eeId_, chr(0), '')  # delete nulls
            self._eeId_ = join(split(self._eeId_, '-'), '')  # delete dashes
        return self._eeId_

    def seId(self):
        if not self._seId_:
            self._seId_ = self.p[24:32]
            self._seId_ = replace(self._seId_, chr(0), '')  # delete nulls
            self._seId_ = join(split(self._seId_, '-'), '')  # delete dashes
        return self._seId_

    def head(self):
        if not self._head_:
            self._head_ = struct.unpack('c', self.p[32])[0]
            self._head_ = (self._head_ == 1)
        return self._head_

    def status(self):
        if not self._status_:
            self._status_ = struct.unpack('I', self.p[44:48])[0]
        return self._status_

    def samples(self):
        if not self._samples_:
            self._samples_ = struct.unpack('i', self.p[48:52])[0]
        return self._samples_

    def rate(self):
        if not self._rate_:
            self._rate_ = struct.unpack('b', self.p[64])[0] & 0x07
            if self._showWarnings_:  # check for mis-matched rate bytes
                for i in range(16, 161, 16):  # check next 10 rate bytes
                    if 64 + i >= len(self.p):
                        break
                    dupRate = struct.unpack('b', self.p[64 + i])[0] & 0x07
                    if dupRate != self._rate_:
                        t = unix_to_human_time(time(), 1) + '\n'
                        t = t + ' mis-matched rate bytes, %s at offset 64 and %s at offset %s\n' % (
                        self._rate_, dupRate, 64 + i)
                        t = t + self.dump()
                        printLog(t)
                        break
            if (self._rate_ == 0):
                self._rate_ = 62.5
            elif (self._rate_ == 1):
                self._rate_ = 125.0
            elif (self._rate_ == 2):  # will have to split packet for this rate and above
                self._rate_ = 250.0
            elif (self._rate_ == 3):
                self._rate_ = 500.0
            elif (self._rate_ == 4):
                self._rate_ = 1000.0
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' bogusRateByte: %s at time %.4f, assuming rate=1000' % (self._rate_, self.time())
                    printLog(t)
                self._rate_ = 1000.0
        return self._rate_

    def gain(self):
        if not self._gain_:
            self._gain_ = (struct.unpack('b', self.p[64])[0] & 0x18) >> 3
            if (self._gain_ == 0):
                self._gain_ = 1.0
            elif (self._gain_ == 1):
                self._gain_ = 10.0
            elif (self._gain_ == 2):
                self._gain_ = 100.0
            elif (self._gain_ == 3):
                self._gain_ = 1000.0
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' bogusGainByte: %s at time %.4f, assuming gain=1' % (self._gain_, self.time())
                    printLog(t)
                self._gain_ = 1.0
        return self._gain_

    def unit(self):
        if not self._unit_:
            self._unit_ = (struct.unpack('b', self.p[65])[0])
            if (self._unit_ == 1):
                self._unit_ = 'counts'
            elif (self._unit_ == 2):
                self._unit_ = 'volts'
            elif (self._unit_ == 3):
                self._unit_ = 'g'
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' bogusUnitByte: %s at time %.4f, assuming unit=ug' % (self._unit_, self.time())
                    printLog(t)
                self._unit_ = 'ug'
        return self._unit_

    def adjustment(self):
        if not self._adjustment_:
            a = (struct.unpack('b', self.p[66])[0])
            self._dqmIndicator_ = a & 0x07
            self._adjustment_ = ''
            if (a & 0x01 == 1):
                self._adjustment_ = 'temperature'
            if (a & 0x02 == 2):
                if self._adjustment_:
                    self._adjustment_ = self._adjustment_ + '+'
                self._adjustment_ = self._adjustment_ + 'gain'
            if (a & 0x04 == 4):
                if self._adjustment_:
                    self._adjustment_ = self._adjustment_ + '+'
                self._adjustment_ = self._adjustment_ + 'axial-mis-alignment'
            if (a & 0x07 == 0):
                self._adjustment_ = 'no-adjustments'
            if a > 7:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' bogusAdjustmentByte: %s at time %.4f, ignoring' % (a, self.time())
                    printLog(t)
        return self._adjustment_

    def time(self):
        if not self._time_:
            sec, usec = struct.unpack('II', self.p[36:44])
            self._time_ = sec + usec / 1000000.0
        return self._time_

    def endTime(self):
        if not self._endTime_:
            self._endTime_ = self.time() + (self.samples() - 1) / self.rate()
        return self._endTime_

    def xyz(self):
        if not self._xyz_:
            convert = 0
            if self.unit() != 'g':
                convert = 1
                if self.unit() == 'volts':
                    m = 1.0 / 3.89791388
                    b = 0
                else:  # must be counts
                    if self.gain() == 1.0:
                        m = 2.18538e-07
                        b = -0.026280804
                    elif self.gain() == 10.0:
                        m = 2.18538e-08
                        b = -0.00262381
                    elif self.gain() == 100.0:
                        m = 2.18538e-09
                        b = -0.00026280804
                    elif self.gain() == 1000.0:
                        m = 2.18538e-10
                        b = -0.000026280804
            for i in range(self.samples()):
                start = 52 + 16 * i
                stop = start + 16
                x, y, z, j = struct.unpack('fffI', self.p[start:stop])
                if convert:
                    x, y, z = x * m + b, y * m + b, z * m + b
                self._xyz_.append((x, y, z))
        return self._xyz_

    def txyz(self):
        if not self._txyz_:
            dt = 1.0 / self.rate()
            convert = 0
            if self.unit() != 'g':
                convert = 1
                if self.unit() == 'volts':
                    m = 1.0 / 3.89791388
                    b = 0
                else:  # must be counts
                    if self.gain() == 1.0:
                        m = 2.18538e-07
                        b = -0.026280804
                    elif self.gain() == 10.0:
                        m = 2.18538e-08
                        b = -0.00262381
                    elif self.gain() == 100.0:
                        m = 2.18538e-09
                        b = -0.00026280804
                    elif self.gain() == 1000.0:
                        m = 2.18538e-10
                        b = -0.000026280804
            for i in range(self.samples()):
                start = 52 + 16 * i
                stop = start + 16
                x, y, z, j = struct.unpack('fffI', self.p[start:stop])
                if convert:
                    x, y, z = x * m + b, y * m + b, z * m + b
                t = i * dt
                self._txyz_.append((t, x, y, z))
        return self._txyz_


class SamsTshEs(AccelPacket):
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        AccelPacket.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._samsTshEs_ = None
        self._samples_ = None
        self._adjustment_ = None
        self._status_ = None
        if not self.isSamsTshEsPacket():
            raise WrongTypeOfPacket
        self.type = 'samses_accel'
        self._name_ = None
        self._header_ = {}
        self._Id_ = None
        self._head_ = None
        self._counter_ = None
        self._rate_ = None
        self._gain_ = None
        self._unit_ = None
        self._adjustment_ = None
        self._time_ = None
        self._endTime_ = None
        self._xyz_ = []
        self._txyz_ = []
        self._xmlHeader_ = None
        self._cutoffFreq_ = None

    def dataDirName(self):
        return 'samses_accel_' + self.Id()

    def measurementsPerSample(self):
        return 3  # what about 'something interesting happened' bit?

    # return true if this packet is contiguous with the supplied packet
    def contiguous(self, other):
        if not other:
            # print('contiguous: no other')
            return 0
        if self.type != other.type:  # maybe we should throw an exception here
            # print('contiguous: other type mis-match')
            return 0
        if self.rate() != other.rate():
            # print('contiguous: other rate mis-match')
            return 0
        if self._dqmIndicator_ != other._dqmIndicator_:
            # print('contiguous: other dqm mis-match')
            return 0
        ostart = other.time()
        oend = other.endTime()
        start = self.time()
        if self.rate() == 0:  # non-periodic data
            # print('contiguous: OK non-periodic')
            return (start > oend)
        #### during testing, all tsh-es packets are maximum size and very regular
        #### on orbit, they will be broken into multiple smaller packets of unknown size
        #### once we know the correct sizes, minSamples should be reduced
        minSamples = {1000.0: 512, 500.0: 512, 250.0: 256, 125.0: 128, 62.5: 64, 31.25: 64, 15.625: 64, 7.8125: 32}
        gap = start - oend
        allowAbleGap = minSamples[self.rate()] / self.rate()
        result = (start >= ostart) and (gap <= allowAbleGap)
        # if not result:
        # print('contiguous:%s ostart:%.4lf oend:%.4lf start:%.4lf gap:%.4lf') % (result, ostart, oend, start, gap)
        return result

    # name of the database table this data should be in (no dashes)
    def name(self):
        if not self._name_:
            self._name_ = self.Id()
        return self._name_

    # return true if this appears to be a samsTshEs acceleration packet
    def isSamsTshEsPacket(self):  # struct.unpack doesn't seem to think 'h' is 2 bytes
        if not self._samsTshEs_:
            if len(self.p) < 80:
                self._samsTshEs_ = 0
                if self._showWarnings_:
                    t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                    t = t + ' packet too short (%s) to be a samsTshEs acceleration packet' % len(self.p)
                    printLog(t)
                return self._samsTshEs_

            # get sync bytes & verify match for tsh
            byte0 = struct.unpack('c', bytes([self.p[0]]))[0]
            byte1 = struct.unpack('c', bytes([self.p[1]]))[0]
            if not (byte0 == bytes([0xac]) and byte1 == bytes([0xd3])):
                self._samsTshEs_ = 0
                if self._showWarnings_:
                    t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                    t = t + ' packet cannot be samsTshEs accel because it does not start with 0xacd3'
                    printLog(t)
                return self._samsTshEs_

            # get selector value
            byte2 = struct.unpack('c', bytes([self.p[40]]))[0]
            byte3 = struct.unpack('c', bytes([self.p[41]]))[0]
            selector = ord(byte2) * 256 + ord(byte3)

            accelpacket = (selector == 170) or (selector == 171)  # || (selector == 177)
            if not accelpacket:
                self._samsTshEs_ = 0
                if self._showWarnings_:
                    t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                    t = t + ' packet cannot be samsTshEs accel because it does not have an TshesAccelPacket selector at offset 40'
                    printLog(t)
                return self._samsTshEs_
            # print(len(self.p), 80 + 16 * self.samples())

            statusInt = self.status()
            rateBits = (statusInt & 0x0f00) >> 8
            # print(rateBits)

            if len(self.p) < 80 + 16 * self.samples():
                self._sams2_ = 0
                t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + unix_to_human_time(time(), 1) + '\n'
                t = t + ' packet is not a complete samsTshEs accel packet, %s samples are not present' % self.samples()
                print('LOG: ' + t)
                return self._samsTshEs_
            self._samsTshEs_ = 1
            self.addAdditionalDQM(self.adjustment())
        return self._samsTshEs_

    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % unix_to_human_time(self.time())
            self._xmlHeader_ = self._xmlHeader_ + '\t<Gain>%s</Gain>\n' % self.gain()
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % self._cutoffFreq_
        return self._xmlHeader_

    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['Id'] = self.Id()
            self._header_['isSamsTshEsPacket'] = self.isSamsTshEsPacket()
            self._header_['counter'] = self.counter()
            self._header_['status'] = self.status()
            self._header_['rate'] = self.rate()
            self._header_['gain'] = self.gain()
            self._header_['unit'] = self.unit()
            self._header_['adjustment'] = self.adjustment()
            self._header_['samples'] = self.samples()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
        return self._header_

    def Id(self):
        """16 bytes starting at byte 44 of a tshes message are first 16 bytes [char:tshes_id] of TshesAccelPacket"""
        if not self._Id_:
            self._Id_ = self.p[44:60]
            # self._Id_ = replace(self._Id_ , chr(0), '')  # delete nulls
            # self._Id_ = join(split(self._Id_, '-'), '')  # delete dashes
            self._Id_ = self._Id_.replace(b'-', b'').replace(b'\0', b'')  # delete dashes and nulls
            self._Id_ = self._Id_[-4:]  # keep last 4 characters only, i.e., "es13"
        return self._Id_

    def counter(self):
        """4 bytes starting at byte 60 of a tshes message are [unsigned int:counter] of TshesAccelPacket"""
        if not self._counter_:
            self._counter_ = struct.unpack('!I', self.p[60:64])[0]  # Network byte order
        return self._counter_

    def time(self):
        """8 bytes starting at byte 64 of a tshes message are [timeval:timestamp] of TshesAccelPacket"""
        if not self._time_:
            sec, usec = struct.unpack('!II', self.p[64:72])  # Network byte order
            self._time_ = sec + usec / 1000000.0
        return self._time_

    def status(self):
        """4 bytes starting at byte 72 of a tshes message are [int:packet_status] of TshesAccelPacket"""
        if not self._status_:
            self._status_ = struct.unpack('!i', self.p[72:76])[0]  # Network byte order
        return self._status_

    def samples(self):
        """4 bytes starting at byte 76 of a tshes message are [int:num_samples] of TshesAccelPacket"""
        if not self._samples_:
            self._samples_ = struct.unpack('!i', self.p[76:80])[0]  # Network byte order
        return self._samples_

    # see xyz method; rest of bytes starting at byte 80 of tshes message are [AccelSample:accel_data] of TshesAccelPacket

    def rate(self):
        """get rate bits from status int"""
        if not self._rate_:
            statusInt = self.status()
            rateBits = (statusInt & 0x0f00) >> 8

            if (rateBits == 0):
                self._rate_ = 7.8125
                self._cutoffFreq_ = 3.2
            elif (rateBits == 1):
                self._rate_ = 15.625
                self._cutoffFreq_ = 6.3
            elif (rateBits == 2):
                self._rate_ = 31.25
                self._cutoffFreq_ = 12.7
            elif (rateBits == 3):
                self._rate_ = 62.5
                self._cutoffFreq_ = 25.3
            elif (rateBits == 4):
                self._rate_ = 125.0
                self._cutoffFreq_ = 50.6
            elif (rateBits == 5):
                self._rate_ = 250.0
                self._cutoffFreq_ = 101.4
            elif (rateBits == 6):
                self._rate_ = 500.0
                self._cutoffFreq_ = 204.2
            elif (rateBits == 7):
                self._rate_ = 1000.0
                self._cutoffFreq_ = 408.5
            elif (rateBits == 8):
                self._rate_ = 125.0
                self._cutoffFreq_ = 23.5
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' bogusRateByte: %s at time %.4f, assuming rate=1000' % (rateBits, self.time())
                    printLog(t)
                self._rate_ = 1000.0
        return self._rate_

    def gain(self):
        """get gain bits from status int"""
        if not self._gain_:
            statusInt = self.status()
            gainBits = statusInt & 0x001f

            if (gainBits == 0):
                self._gain_ = 1.0
                self._input_ = 'Ground'  # _input_ is not used as far as I can tell
            elif (gainBits == 1):
                self._gain_ = 2.5
                self._input_ = 'Ground'
            elif (gainBits == 2):
                self._gain_ = 8.5
                self._input_ = 'Ground'
            elif (gainBits == 3):
                self._gain_ = 34.0
                self._input_ = 'Ground'
            elif (gainBits == 4):
                self._gain_ = 128.0
                self._input_ = 'Ground'
            elif (gainBits == 8):
                self._gain_ = 1.0
                self._input_ = 'Test'
            elif (gainBits == 9):
                self._gain_ = 2.5
                self._input_ = 'Test'
            elif (gainBits == 10):
                self._gain_ = 8.5
                self._input_ = 'Test'
            elif (gainBits == 11):
                self._gain_ = 34.0
                self._input_ = 'Test'
            elif (gainBits == 12):
                self._gain_ = 128.0
                self._input_ = 'Test'
            elif (gainBits == 16):
                self._gain_ = 1.0
                self._input_ = 'Signal'
            elif (gainBits == 17):
                self._gain_ = 2.5
                self._input_ = 'Signal'
            elif (gainBits == 18):
                self._gain_ = 8.5
                self._input_ = 'Signal'
            elif (gainBits == 19):
                self._gain_ = 34.0
                self._input_ = 'Signal'
            elif (gainBits == 20):
                self._gain_ = 128.0
                self._input_ = 'Signal'
            elif (gainBits == 24):
                self._gain_ = 1.0
                self._input_ = 'Vref'
            elif (gainBits == 25):
                self._gain_ = 1.0
                self._input_ = 'Sensor test'
            elif (gainBits == 26):
                self._gain_ = 2.0
                self._input_ = 'Sensor test'
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' TSH-ES bogusGainByte: %s at time %.4f, assuming gain=1' % (gainBits, self.time())
                    printLog(t)
                self._gain_ = 1.0
        return self._gain_

    def unit(self):
        """get unit bits from status int"""
        if not self._unit_:
            statusInt = self.status()
            unitBits = (statusInt & 0x0060) >> 5

            if (unitBits == 0):
                self._unit_ = 'counts'
            elif (unitBits == 1):
                self._unit_ = 'volts'
            elif (unitBits == 2):
                self._unit_ = 'g'
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' + self.dump()
                    t = t + '\n' + unix_to_human_time(time(), 1),
                    t = t + '\n' + ' TSH-ES bogusUnitByte: %s at time %.4f, assuming unit=g' % (unitBits, self.time())
                    printLog(t)
                self._unit_ = 'g'
        return self._unit_

    def adjustment(self):
        """get adjustment bits from status int"""
        if not self._adjustment_:
            statusInt = self.status()
            adjBits = (statusInt & 0x0080) >> 7

            self._dqmIndicator_ = adjBits
            self._adjustment_ = 'no-compensation'
            if (adjBits == 1):
                self._adjustment_ = 'temperature-compensation'
        return self._adjustment_

    def endTime(self):
        """compute end time from start, number of samples and rate"""
        if not self._endTime_:
            self._endTime_ = self.time() + (self.samples() - 1) / self.rate()
        return self._endTime_

    def handleDigitalIOstatus(self, digitalIOstatus, sampleNumber):
        # check for the 'something interesting happened' bit for this sensor and do something with it
        enabled = digitalIOstatus & 0x0001
        if enabled:
            inputIO = (digitalIOstatus & 0x0004) > 2
            if self.name() in DigitalIOstatusHolder:
                interestingBit = DigitalIOstatusHolder[self.name()]
                if interestingBit != inputIO:  # state change
                    DigitalIOstatusHolder[self.name()] = inputIO
                    # state change detected, what should be do with that information?
                    eventTime = self.time() + sampleNumber / self.rate()
                    msg = ' (inputIO_state_change:%s time:%.4f)' % (inputIO, eventTime)
                    # print self.name(), msg
            else:
                DigitalIOstatusHolder[self.name()] = inputIO

    def xyz(self):
        """xyz array of accel_data"""
        if not self._xyz_:
            convert = 0
            ##            if self.unit() != 'g':   #### need calibration numbers for flight units
            ##                convert = 1
            ##                if self.unit() == 'volts':
            ##                    mx = my = mz = 1.0/3.89791388
            ##                    bx = by = bz = 0
            ##                else: # must be counts
            ##                    if self.gain() == 1.0:
            ##                        mx = my = mz = 2.18538e-07
            ##                        bx = by = bz = -0.026280804
            ##                    elif self.gain() == 10.0:
            ##                        mx = my = mz = 2.18538e-08
            ##                        bx = by = bz = -0.00262381
            ##                    elif self.gain() == 100.0:
            ##                        mx = my = mz = 2.18538e-09
            ##                        bx = by = bz = -0.00026280804
            ##                    elif self.gain() == 1000.0:
            ##                        m = 2.18538e-10
            ##                        bx = by = bz = -0.000026280804
            for i in range(self.samples()):
                start = 80 + 16 * i
                stop = start + 16
                x, y, z, digitalIOstatus = struct.unpack('!fffI', self.p[start:stop])  # Network byte order
                self.handleDigitalIOstatus(digitalIOstatus, i)
                if convert:
                    x, y, z = x * mx + bx, y * my + by, z * mz + bz
                self._xyz_.append((x, y, z))
        return self._xyz_

    def txyz(self):
        """txyz array of accel_data"""
        if not self._txyz_:
            dt = 1.0 / self.rate()
            convert = 0
            ##            if self.unit() != 'g':
            ##                convert = 1
            ##                if self.unit() == 'volts':
            ##                    mx = my = mz = 1.0/3.89791388
            ##                    bx = by = bz = 0
            ##                else: # must be counts
            ##                    if self.gain() == 1.0:
            ##                        mx = my = mz = 2.18538e-07
            ##                        bx = by = bz = -0.026280804
            ##                    elif self.gain() == 10.0:
            ##                        mx = my = mz = 2.18538e-08
            ##                        bx = by = bz = -0.00262381
            ##                    elif self.gain() == 100.0:
            ##                        mx = my = mz = 2.18538e-09
            ##                        bx = by = bz = -0.00026280804
            ##                    elif self.gain() == 1000.0:
            ##                        m = 2.18538e-10
            ##                        bx = by = bz = -0.000026280804
            for i in range(self.samples()):
                start = 80 + 16 * i
                stop = start + 16
                x, y, z, digitalIOstatus = struct.unpack('!fffI', self.p[start:stop])  # Network byte order
                self.handleDigitalIOstatus(digitalIOstatus, i)
                if convert:
                    x, y, z = x * mx + bx, y * my + by, z * mz + bz
                t = i * dt
                self._txyz_.append((t, x, y, z))
        return self._txyz_
