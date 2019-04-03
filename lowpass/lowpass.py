#!/usr/bin/env python

import sys
from sys import *
import struct
import os

# from MySQLdb import *  # TODO find all MySQL calls and put explicit (NOT STAR) imports here
# from _mysql_exceptions import *
import MySQLdb as sql
import MySQLdb._exceptions as _mysql_exceptions

import datetime
from time import *
from subprocess import *
from syslog import *
import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
from pylive import live_plot_xy
import warnings

from tshcal.secret import SDB, SUSER, SPASSWD

warnings.filterwarnings("ignore", ".*GUI is implemented")

# input parameters
defaults = {
'table':            'es13', # string to specify sensor db table (eg. es13)
'fs':               '250',  # float value to specify sample rate (sa/sec)
'fc':               '1',    # integer value for cutoff frequency (Hz)
'ax':               '1',    # integer value to designate which axis (x=1, y=2, z=3)
'num_pkts':         '240',  # integer value for num packets for span of interest (maybe 240 pkts for a 1-min. plot span)
'pause_sec':        '0.2',  # float value for pause time in the live plotting loop
}
parameters = defaults.copy()


def how_to_handle_exceptions_in_three_point_seven(month, day, year):
    cmd = 'date -u -d "%d/%d/%d 00:00:00 UTC" +%%s' % tuple((month, day, year))
    result = 0
    try:
        result = int(getoutput(cmd)) + fraction
    except ValueError as err:
        t = 'date conversion error\ndate command was: %sdate command returned: %s' % (cmd, result)
        raise ValueError from err
    return result


class BCDConversionException(Exception):
    def __init__(self, args=None):
        if args:
            self.args = args


class WrongTypeOfPacket(Exception):
    def __init__(self, args=None):
        if args:
            self.args = args

# pluggable 0-argument function to be called when idling. It can return true to stop idling. 
addIdleFunction = None
addLogFunction = None


def addIdle(idleFunction):
    global addIdleFunction
    addIdleFunction = idleFunction


def idleWait(seconds = 0):
    for i in range(seconds):
        if addIdleFunction:
            if addIdleFunction():
                return 1
        sleep(1)
    else: # always execute at least once
        if addIdleFunction:
            return addIdleFunction()
    return 0


def addLog(logFunction):
    """pluggable function to be called to log something"""
    global addLogFunction
    addLogFunction = logFunction


def printLog(message):
    """write message to syslog, console and maybe more"""
    print(message)
    syslog(LOG_WARNING|LOG_LOCAL0, message)
    if addLogFunction:
        addLogFunction(message)


def UnixToHumanTime(utime, altFormat = 0):
    """convert "Unix time" to "Human readable" time"""
    try:
        fraction = utime - int(utime)
    except OverflowError as err:
        t = 'Unix time %s too long to convert, substituting 0' % utime
        printLog(t)
        fraction = utime = 0
    # handle special case of -1 (not handled correctly by 'date')
    if int(utime == -1):
        return (1969,12,31,23,59,59)
    cmd = 'date -u -d "1970-01-01 %d sec" +"%%Y %%m %%d %%H %%M %%S"' % int(utime)
    try:
        result = getoutput(cmd)
        # s = split(result)
        s = result.split()
        # s[5] = atoi(s[5]) + fraction
        s[5] = int(s[5]) + fraction
    except ValueError as err:
        t = 'date conversion error\ndate command was: %sdate command returned: %s' % (cmd, result)
        printLog(t)
        raise ValueError(err)
    if altFormat == 0:
        return "%s_%s_%s_%s_%s_%06.3f" % tuple(s)
    elif altFormat == 1:
        return "%s/%s/%s %s:%s:%06.3f" % tuple(s)
    else: # altformat == 2
        s[0:5]=list(map(atoi, s[0:5]))
        return tuple(s)


def HumanToUnixTime(month, day, year, hour, minute, second, fraction = 0.0):
    """convert "Human readable" to "Unix time" time"""
    cmd = 'date -u -d "%d/%d/%d %d:%d:%d UTC" +%%s' % tuple((month, day, year, hour, minute, second))
    result = 0
    try:
        result=int(getoutput(cmd)) + fraction
    except ValueError as err:
        t = 'date conversion error\ndate command was: %sdate command returned: %s' % (cmd, result)
        printLog(t)
        raise ValueError(err)
    return result
    

def BCD(char):
    """# byte to BCD conversion"""
    byte = ord(char)
    tens = (byte & 0xf0) >> 4
    ones = (byte & 0x0f)
    if (tens > 9) or (ones > 9):
        raise BCDConversionException('tens: %s, ones:%s' % (tens, ones))
    return tens*10+ones


def xmlEscape(s):
    """# escape characters that are special to XML"""
    s=join(split(s, '&'), '&amp;')
    s=join(split(s, '<'), '&lt;')
    s=join(split(s, '>'), '&gt;')
    s=join(split(s, '"'), '&quot;')
    s=join(split(s, '\''), '&apos;')
    return s


def sqlConnect(command, shost='localhost', suser=SUSER, spasswd=SPASSWD, sdb=SDB):
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
            t = UnixToHumanTime(time(), 1) + '\n' + msg[1] + '\nMySQL call failed, will try again in %s seconds' % sqlRetryTime
            printLog(t)
            if idleWait(sqlRetryTime):
                return []

    return results

# -----------------------------------------------------------------------------------


def guessPacket(packet, showWarnings=0):
    """try to create a packet of the appropriate type"""
    subtypes = [samsTshEs, sams2Packet, hirap, oss, oare, besttmf, finaltmf, finalbias, radgse, samsff, artificial]
    for i in subtypes:
        try:
            p = i(packet, showWarnings=0)
            return p
        except WrongTypeOfPacket:
            pass
    if showWarnings:
        t = UnixToHumanTime(time(), 1) + 'unknown packet type detected'
        printLog(t)
    return accelPacket(packet)

DigitalIOstatusHolder = {} # global dictionary to hold SAMS TSH-ES DigitalIOstatus between packets

###############################################################################    
# class to represent all types of accel data (SAMS2, MAMS, etc)
class accelPacket:
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
#            print('contiguous: no other')
            return 0
        if self.type != other.type: # maybe we should throw an exception here
#            print('contiguous: other type mis-match')
            return 0
        if self.rate() != other.rate():
#            print('contiguous: other rate mis-match')
            return 0
        if self._dqmIndicator_ != other._dqmIndicator_:
#            print('contiguous: other dqm mis-match')
            return 0
        ostart = other.time()
        oend = other.endTime()
        start = self.time()
        if self.rate() == 0: # non-periodic data
#            print('contiguous: OK non-periodic')
            return (start > oend)
        gap = start - oend
        # when samples == 1, any jitter can cause a delay that shows up as a gap, so inflate allowableGap
        if self.samples() == 1:
            allowAbleGap = 1.5*self.samples()/self.rate()
        else:
            allowAbleGap = self.samples()/self.rate()
        result =  (start >= ostart) and (gap <= allowAbleGap)
#        if not result:
#             print('contiguous:%s ostart:%.4lf oend:%.4lf start:%.4lf gap:%.4lf allowAbleGap:%.4lf') % (result, ostart, oend, start, gap, allowAbleGap) 
        return result
    
    # print a representation of this packet
    def dump(self, accelData=0):
        if not self._rep_:
            header = self.header()
            hkeys = list(header.keys())
            className = split(str(self.__class__), '.')[1] 
            self._rep_ = '%s(' % className
            for i in hkeys:
                if i == 'time' or i == 'endTime': # work around Python 3 decimal place default for times
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
            #print hex representation
            c = 0
            asc = self.p[start:min(start+size, ln)]
            for b in asc:
                if c == 8:
                    line = line + '  '
                line = line + '%02x ' % ord(b)
                c = c + 1
            line = ljust(line, 58) + '"'
            # print ascii representation, replace unprintable characters with spaces
            for i in range(len(asc)):
                if ord(asc[i])<32 or ord(asc[i]) == 209:
                    asc = replace(asc, asc[i], ' ')
            line = line + asc + '"\n'  
            self._hex_ = self._hex_ + line
            start = start + size
        return self._hex_
        
###############################################################################    
class oss(accelPacket):
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        accelPacket.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._oss_ = None
        if not self.isOSSPacket():
            raise WrongTypeOfPacket
        self.type = 'mams_accel_ossraw'
        self._name_ = None
        self._rate_ = 10.0
        self._header_ = {}
        self._samples_ = None
        self._time_ = None
        self._endTime_ = None
        self._temperature_ = None
        self._Ts_ = []
        self._xyz_ = []
        self._txyz_ = []
        self._xmlHeader_ = None
        
    # print a representation of this packet
    def dump(self, accelData=0):
        if not self._rep_:
            header = self.header()
            hkeys = list(header.keys())
            className = split(str(self.__class__), '.')[1] 
            self._rep_ = '%s(' % className
            for i in hkeys:
                if i == 'time' or i == 'endTime': # work around Python 3 decimal place default for times
                    self._rep_ = self._rep_ + ' %s:%.4f' % (i, header[i])
                else:
                    self._rep_ = self._rep_ + ' %s:%s' % (i, header[i])
            if accelData:
                self._rep_ = self._rep_ + '\ndata:'
                for j in self.xyz():
                    self._rep_ = self._rep_ + '\n%.7e %.7e %.7e' % j
                self._rep_ = self._rep_ + '\ntemperature, status'
                for j in self._Ts_:
                    self._rep_ = self._rep_ + '\n%.7f %.1f' % j
#                for j in self.txyz():
#                    self._rep_ = self._rep_ + '\n%.4f %.7e %.7e %.7e' % j
        return self._rep_
         
    # return true if this appears to be a oss raw acceleration packet
    def isOSSPacket(self):
        if 1074 != len(self.p): # all oss raw packets have the same length
            if 1084 != len(self.p): # unless they are extended by 10 bytes for ccsds time
                self._oss_ = 0
                return self._oss_
        try:
            self.time() # make sure time is really BCD compatible values
            self.extractPerPacketData() # might as well extract it now, maybe check for errors
            self._oss_ = 1
        except 'ValueError' as value:
            t = UnixToHumanTime(time(), 1) + ' packet with bad time ignored'
            printLog(t)
            self._oss_ = 0
        except BCDConversionException as value:
            self._oss_ = 0
        return self._oss_
    
    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % UnixToHumanTime(self.time())
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % 1
#            self._xmlHeader_ = self._xmlHeader_ + '\t<Gain>%s</Gain>\n' % 1
        return self._xmlHeader_
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isOSSPacket'] = self.isOSSPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
        return self._header_

    def name(self):
        if not self._name_:
            self._name_ = 'ossraw'
        return self._name_

    def rate(self):
        if not self._rate_:
            self._rate_ = 10.0
        return self._rate_

    def time(self):
        if not self._time_:
            century = BCD(self.p[0])
            year =    BCD(self.p[1]) + 100*century
            month =   BCD(self.p[2])
            day =     BCD(self.p[3])
            hour =    BCD(self.p[4])
            minute =  BCD(self.p[5])
            second =  BCD(self.p[6])
            millisec = struct.unpack('h', self.p[8:10])[0]
            millisec = millisec & 0xffff
            self._time_ = HumanToUnixTime(month, day, year, hour, minute, second, millisec/1000.0)
        return self._time_
    
    def endTime(self):
        if not self._endTime_:
            # all oss-raw packets have 160 samples
            self._endTime_ = self.time() + 159.0 / self.rate() 
        return self._endTime_

    def samples(self): # all oss-raw packets have 160 samples
        if not self._samples_:
            self._samples_ = 160
        return self._samples_

    def extractPerPacketData(self):
        temperatureBytes = struct.unpack('h', self.p[10:12])[0]
        temperatureBytes = temperatureBytes & 0xffff
        self._temperature_ = (32768 - temperatureBytes) * (20.0/65536.0) * 20.0 - 17.8

    def txyz(self):
        if not self._txyz_:
            if not self._temperature_:
                self.extractPerPacketData()
            dt = 1.0/self.rate()
            begin = 50
            for s in range(16):
                sstart = begin + s*64
                dataStatus, rangeStatus, gimbalStatus = struct.unpack('BxBB', self.p[sstart:sstart+4])
                status = ((dataStatus<<16) + (rangeStatus<<8) + gimbalStatus) * 1.0 # pack and convert to float
                
                if rangeStatus & 0x03 == 0: #range A
                    zRange = 2500
                elif rangeStatus & 0x03 == 1: #range B
                    zRange = 197
                elif rangeStatus & 0x03 == 2: #range C
                    zRange = 15
                else:
                    raise Exception('rangeStatus value out of range')
                rangeStatus = rangeStatus >> 2
                if rangeStatus & 0x03 == 0: #range A
                    yRange = 2500
                elif rangeStatus & 0x03 == 1: #range B
                    yRange = 197
                elif rangeStatus & 0x03 == 2: #range C
                    yRange = 15
                else:
                    raise Exception('rangeStatus value out of range')
                rangeStatus = rangeStatus >> 2
                if rangeStatus & 0x03 == 0: #range A
                    xRange = 1000
                elif rangeStatus & 0x03 == 1: #range B
                    xRange = 100
                elif rangeStatus & 0x03 == 2: #range C
                    xRange = 10
                else:
                    raise Exception('rangeStatus value out of range')                

                x_coeff = ((20.0 / 65536.0) * xRange) / 1000000.0
                y_coeff = ((20.0 / 65536.0) * yRange) / 1000000.0
                z_coeff = ((20.0 / 65536.0) * zRange) / 1000000.0

                for i in range(10):
                    start = sstart + 4 + i*6
                    stop = start+6
                    x, y, z = struct.unpack('hhh', self.p[start:stop])
                    x = x & 0xffff
                    y = y & 0xffff
                    z = z & 0xffff
                    x = (32768.0 - x) * x_coeff
                    y = (32768.0 - y) * y_coeff
                    z = (32768.0 - z) * z_coeff
                    t = (s*10+i)*dt
                    self._txyz_.append((t, x, y, z))
                    self._Ts_.append((self._temperature_, status))
        return self._txyz_

    def xyz(self):
        if not self._xyz_:
            if not self._temperature_:
                self.extractPerPacketData()
            begin = 50
            for s in range(16):
                sstart = begin + s*64
                dataStatus, rangeStatus, gimbalStatus = struct.unpack('BxBB', self.p[sstart:sstart+4])
                status = ((dataStatus<<16) + (rangeStatus<<8) + gimbalStatus) * 1.0 # pack and convert to float
                
                if rangeStatus & 0x03 == 0: #range A
                    zRange = 2500
                elif rangeStatus & 0x03 == 1: #range B
                    zRange = 197
                elif rangeStatus & 0x03 == 2: #range C
                    zRange = 15
                else:
                    raise Exception('rangeStatus value out of range')
                rangeStatus = rangeStatus >> 2
                if rangeStatus & 0x03 == 0: #range A
                    yRange = 2500
                elif rangeStatus & 0x03 == 1: #range B
                    yRange = 197
                elif rangeStatus & 0x03 == 2: #range C
                    yRange = 15
                else:
                    raise Exception('rangeStatus value out of range')
                rangeStatus = rangeStatus >> 2
                if rangeStatus & 0x03 == 0: #range A
                    xRange = 1000
                elif rangeStatus & 0x03 == 1: #range B
                    xRange = 100
                elif rangeStatus & 0x03 == 2: #range C
                    xRange = 10
                else:
                    raise Exception('rangeStatus value out of range')                

                x_coeff = ((20.0 / 65536.0) * xRange) / 1000000.0
                y_coeff = ((20.0 / 65536.0) * yRange) / 1000000.0
                z_coeff = ((20.0 / 65536.0) * zRange) / 1000000.0
    
                for i in range(10):
                    start = sstart + 4 + i*6
                    stop = start+6
                    x, y, z = struct.unpack('hhh', self.p[start:stop])
                    x = x & 0xffff
                    y = y & 0xffff
                    z = z & 0xffff
                    x = (32768.0 - x) * x_coeff
                    y = (32768.0 - y) * y_coeff
                    z = (32768.0 - z) * z_coeff
                    self._xyz_.append((x, y, z))
                    self._Ts_.append((self._temperature_, status))
        return self._xyz_
    
    def extraColumns(self):
        return self._Ts_
    
###############################################################################
class oare(accelPacket): # similar to oss, but everything is in a different place
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        accelPacket.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._oare_ = None
        if not self.isOAREPacket():
            raise WrongTypeOfPacket
        self.type = 'mams_accel_oare'
        self._name_ = None
        self._rate_ = 10.0
        self._header_ = {}
        self._samples_ = None
        self._time_ = None
        self._endTime_ = None
        self._temperature_ = None
        self._Ts_ = []
        self._xyz_ = []
        self._txyz_ = []
        self._xmlHeader_ = None

    # print a representation of this packet
    def dump(self, accelData=0):
        if not self._rep_:
            header = self.header()
            hkeys = list(header.keys())
            className = split(str(self.__class__), '.')[1]
            self._rep_ = '%s(' % className
            for i in hkeys:
                if i == 'time' or i == 'endTime': # work around Python 3 decimal place default for times
                    self._rep_ = self._rep_ + ' %s:%.4f' % (i, header[i])
                else:
                    self._rep_ = self._rep_ + ' %s:%s' % (i, header[i])
            if accelData:
                self._rep_ = self._rep_ + '\ndata:'
                for j in self.xyz():
                    self._rep_ = self._rep_ + '\n%.7e %.7e %.7e' % j
                self._rep_ = self._rep_ + '\ntemperature, status'
                for j in self._Ts_:
                    self._rep_ = self._rep_ + '\n%.7f %.1f' % j
        return self._rep_

    # return true if this appears to be a oare raw acceleration packet
    def isOAREPacket(self):
        if 75 != len(self.p): # all oare raw packets have the same length
            self._oare_ = 0
            return self._oare_
        try:
            self.time() # make sure time is really BCD compatible values
            self.extractPerPacketData() # might as well extract it now, maybe check for errors
            self._oare_ = 1
        except 'ValueError' as value:
            t = UnixToHumanTime(time(), 1) + ' packet with bad time ignored'
            printLog(t)
            self._oare_ = 0
        except BCDConversionException as value:
            self._oare_ = 0
        return self._oare_

    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % UnixToHumanTime(self.time())
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % 1
        return self._xmlHeader_

    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isOAREPacket'] = self.isOAREPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
        return self._header_

    def name(self):
        if not self._name_:
            self._name_ = 'oare'
        return self._name_

    def rate(self):
        if not self._rate_:
            self._rate_ = 10.0
        return self._rate_

    def time(self):
        if not self._time_:
            century = BCD(self.p[0])
            year =    BCD(self.p[1]) + 100*century
            month =   BCD(self.p[2])
            day =     BCD(self.p[3])
            hour =    BCD(self.p[4])
            minute =  BCD(self.p[5])
            second =  BCD(self.p[6])
            millisec = struct.unpack('h', self.p[8:10])[0]
            millisec = millisec & 0xffff
            self._time_ = HumanToUnixTime(month, day, year, hour, minute, second, millisec/1000.0)
        return self._time_

    def endTime(self):
        if not self._endTime_:
            # all oare packets have 10 samples
            self._endTime_ = self.time() + 9.0 / self.rate()
        return self._endTime_

    def samples(self): # all oare packets have 10 samples
        if not self._samples_:
            self._samples_ = 10
        return self._samples_

    def extractPerPacketData(self):
        temperatureBytes = struct.unpack('h', self.p[70:72])[0]
        temperatureBytes = temperatureBytes & 0xffff
        self._temperature_ = (32768 - temperatureBytes) * (20.0/65536.0) * 20.0 - 17.8
        self.dataStatus, self.rangeStatus, self.gimbalStatus = struct.unpack('BBB', self.p[72:75])

    def txyz(self):
        if not self._txyz_:
            if not self._temperature_:
                self.extractPerPacketData()
            dt = 1.0/self.rate()
            sstart = 10
            status = ((self.dataStatus<<16) + (self.rangeStatus<<8) + self.gimbalStatus) * 1.0 # pack and convert to float

            if self.rangeStatus & 0x03 == 0: #range A
                zRange = 2500
            elif self.rangeStatus & 0x03 == 1: #range B
                zRange = 197
            elif self.rangeStatus & 0x03 == 2: #range C
                zRange = 15
            else:
                raise Exception('rangeStatus value out of range %s') % (self.rangeStatus & 0x03)
            self.rangeStatus = self.rangeStatus >> 2
            if self.rangeStatus & 0x03 == 0: #range A
                yRange = 2500
            elif self.rangeStatus & 0x03 == 1: #range B
                yRange = 197
            elif self.rangeStatus & 0x03 == 2: #range C
                yRange = 15
            else:
                raise Exception('rangeStatus value out of range')
            self.rangeStatus = self.rangeStatus >> 2
            if self.rangeStatus & 0x03 == 0: #range A
                xRange = 1000
            elif self.rangeStatus & 0x03 == 1: #range B
                xRange = 100
            elif self.rangeStatus & 0x03 == 2: #range C
                xRange = 10
            else:
                raise Exception('rangeStatus value out of range')

            x_coeff = ((20.0 / 65536.0) * xRange) / 1000000.0
            y_coeff = ((20.0 / 65536.0) * yRange) / 1000000.0
            z_coeff = ((20.0 / 65536.0) * zRange) / 1000000.0

            for i in range(10):
                start = sstart + i*6
                stop = start+6
                x, y, z = struct.unpack('hhh', self.p[start:stop])
                x = x & 0xffff
                y = y & 0xffff
                z = z & 0xffff
                x = (32768.0 - x) * x_coeff
                y = (32768.0 - y) * y_coeff
                z = (32768.0 - z) * z_coeff
                t = i*dt
                self._txyz_.append((t, x, y, z))
                self._Ts_.append((self._temperature_, status))
        return self._txyz_

    def xyz(self):
        if not self._xyz_:
            if not self._temperature_:
                self.extractPerPacketData()
            sstart = 10
            status = ((self.dataStatus<<16) + (self.rangeStatus<<8) + self.gimbalStatus) * 1.0 # pack and convert to float

            if self.rangeStatus & 0x03 == 0: #range A
                zRange = 2500
            elif self.rangeStatus & 0x03 == 1: #range B
                zRange = 197
            elif self.rangeStatus & 0x03 == 2: #range C
                zRange = 15
            else:
                raise Exception('rangeStatus value out of range')
            self.rangeStatus = self.rangeStatus >> 2
            if self.rangeStatus & 0x03 == 0: #range A
                yRange = 2500
            elif self.rangeStatus & 0x03 == 1: #range B
                yRange = 197
            elif self.rangeStatus & 0x03 == 2: #range C
                yRange = 15
            else:
                raise Exception('rangeStatus value out of range')
            self.rangeStatus = self.rangeStatus >> 2
            if self.rangeStatus & 0x03 == 0: #range A
                xRange = 1000
            elif self.rangeStatus & 0x03 == 1: #range B
                xRange = 100
            elif self.rangeStatus & 0x03 == 2: #range C
                xRange = 10
            else:
                raise Exception('rangeStatus value out of range')

            x_coeff = ((20.0 / 65536.0) * xRange) / 1000000.0
            y_coeff = ((20.0 / 65536.0) * yRange) / 1000000.0
            z_coeff = ((20.0 / 65536.0) * zRange) / 1000000.0

            for i in range(10):
                start = sstart + i*6
                stop = start+6
                x, y, z = struct.unpack('hhh', self.p[start:stop])
                x = x & 0xffff
                y = y & 0xffff
                z = z & 0xffff
                x = (32768.0 - x) * x_coeff
                y = (32768.0 - y) * y_coeff
                z = (32768.0 - z) * z_coeff
                self._xyz_.append((x, y, z))
                self._Ts_.append((self._temperature_, status))
        return self._xyz_

    def extraColumns(self):
        return self._Ts_
   
###############################################################################    
class artificial(accelPacket):
    def __init__(self, packet, showWarnings=0):
        accelPacket.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._artificial_ = None
        if not self.isArtificialPacket():
            raise WrongTypeOfPacket
        self.type = 'artificial'
        self._name_ = 'Artificial'
        self._deviceId_ = None
        self._rate_ = None
        self._samples_ = None
        self._measurementsPerSample_ = None
        self._dataOffset_ = None
        self._header_ = {}
        self._time_ = None
        self._endTime_ = None
        self._xyz_ = []
        self._txyz_ = []
        self._xmlHeader_ = None

    # return true if this appears to be an artificial packet
    def isArtificialPacket(self):
        if 32 > len(self.p): # minimum length 
            self._artificial_ = 0
            return self._artificial_
        # byte0 = struct.unpack('c', self.p[0])[0]
        # byte1 = struct.unpack('c', self.p[1])[0]
        byte0 = struct.unpack('c', bytes([self.p[0]]))[0]
        byte1 = struct.unpack('c', bytes([self.p[1]]))[0]
        if not (byte0 == chr(0xfa) and byte1 == chr(0xce)):
            self._artificial_ = 0
            return self._artificial_
        self._artificial_ = 1
        return self._artificial_
    
    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % self.time()
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
        return self._xmlHeader_
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isArtificialPacket'] = self.isArtificialPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
            self._header_['samples'] = self.samples()
            self._header_['measurementsPerSample'] = self.measurementsPerSample()
            self._header_['deviceId'] = self.deviceId()
        return self._header_

    def name(self):
        if not self._name_:
            self._name_ = 'Artificial'
        return self._name_

    def deviceId(self):
        if not self._deviceId_:
            self._deviceId_ = ord(struct.unpack('c', self.p[3])[0])
        return self._deviceId_

    def rate(self):
        if not self._rate_:
            self._rate_ = struct.unpack('f', self.p[12:16])[0]
        return self._rate_

    def samples(self):
        if not self._samples_:
            self._samples_ = struct.unpack('i', self.p[16:20])[0]
        return self._samples_
    
    def measurementsPerSample(self):
        if not self._measurementsPerSample_:
            self._measurementsPerSample_ = struct.unpack('i', self.p[20:24])[0]
        return self._measurementsPerSample_
    
    def dataOffset(self):
        if not self._dataOffset_:
            self._dataOffset_ = struct.unpack('i', self.p[24:28])[0]
        return self._dataOffset_

    def time(self):
        if not self._time_:
            self._time_ = struct.unpack('d', self.p[4:12])[0]
        return self._time_
    
    def endTime(self):
        if not self._endTime_:
            if self.rate() == 0:
                self._endTime_ = self.time()
            else:
                self._endTime_ = self.time() + (self.samples() - 1) / self.rate() 
        return self._endTime_

    def xyz(self):
        if not self._xyz_:
            index = start = self.dataOffset()
            samples = self.samples()
            for i in range(samples):
                row = []
                for j in range(self.measurementsPerSample()):
                    x = struct.unpack('f', self.p[index:index+4])[0]
                    row.append(x)
                    index = index + 4                
                self._xyz_.append(row)
        return self._xyz_

    def txyz(self):
        if not self._txyz_:
            index = start = self.dataOffset()
            # rate = 0 means non-periodic, and implies only 1 sample per packet
            if self.rate() == 0 and self.samples() == 1:
                dt = 1 # does not matter
            else:
                dt = 1.0/self.rate()
            for i in range(self.samples()):
                t = i*dt
                row = [t]
                for j in range(self.measurementsPerSample()):
                    x = struct.unpack('f', self.p[index:index+4])[0]
                    row.append(x)
                    index = index + 4                
                self._txyz_.append(row) 
        return self._txyz_

    # print a representation of this packet
    def dump(self, accelData=0):
        if not self._rep_:
            header = self.header()
            hkeys = list(header.keys())
            className = split(str(self.__class__), '.')[1] 
            self._rep_ = '%s(' % className
            for i in hkeys:
                if i == 'time' or i == 'endTime': # work around Python 3 decimal place default for times
                    self._rep_ = self._rep_ + ' %s:%.4f' % (i, header[i])
                else:
                    self._rep_ = self._rep_ + ' %s:%s' % (i, header[i])
            if accelData:
                self._rep_ = self._rep_ + '\ndata:'
                for j in self.xyz():
                    self._rep_ = self._rep_ + '\n'
                    for k in j:
                        self._rep_ = self._rep_ + '%.7e ' % (k)
        return self._rep_
    
###############################################################################    
class besttmf(artificial):
    def __init__(self, packet, showWarnings=0):
        artificial.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._besttmf_ = None
        if not self.isBesttmfPacket():
            raise WrongTypeOfPacket
        self.type = 'mams_accel_ossbtmf'
        self._name_ = None

    # return true if this appears to be an besttmf packet
    def isBesttmfPacket(self):
        if not artificial.isArtificialPacket(self):
            self._besttmf_ = 0
            return self._besttmf_
        byte2 = struct.unpack('c', self.p[2])[0]
        if not byte2 == chr(0x01):
            self._besttmf_ = 0
            return self._besttmf_
        self._besttmf_ = 1
        return self._besttmf_
    
    def name(self):
        if not self._name_:
            self._name_ = 'ossbtmf'
        return self._name_
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isBesttmfPacket'] = self.isBesttmfPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
            self._header_['samples'] = self.samples()
            self._header_['measurementsPerSample'] = self.measurementsPerSample()
            self._header_['deviceId'] = self.deviceId()
            self._header_['biasCoeff'] = '%.7e %.7e %.7e' % self.biasValues()
        return self._header_
    
    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % self.time()
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % 0.01
            self._xmlHeader_ = self._xmlHeader_ + '\t<BiasCoeff x="%.7e" y="%.7e" z="%.7e"/>\n' % self.biasValues()
        return self._xmlHeader_

    def biasValues(self):
        # return the 3 bias values
        return struct.unpack('fff', self.p[28:40])
        
    # print a representation of this packet
    def dump(self, accelData=0):
        if not self._rep_:
            header = self.header()
            hkeys = list(header.keys())
            className = split(str(self.__class__), '.')[1] 
            self._rep_ = '%s(' % className
            for i in hkeys:
                if i == 'time' or i == 'endTime': # work around Python 3 decimal place default for times
                    self._rep_ = self._rep_ + ' %s:%.4f' % (i, header[i])
                else:
                    self._rep_ = self._rep_ + ' %s:%s' % (i, header[i])
            if accelData:
                self._rep_ = self._rep_ + '\ndata:'
                for j in self.xyz():
                    self._rep_ = self._rep_ + '\n%.7e %.7e %.7e' % tuple(j)
        return self._rep_
  
   
###############################################################################    
class finaltmf(artificial):
    def __init__(self, packet, showWarnings=0):
        artificial.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._finaltmf_ = None
        if not self.isFinaltmfPacket():
            raise WrongTypeOfPacket
        self.type = 'mams_accel_ossftmf'
        self._name_ = None

    # return true if this appears to be an finaltmf packet
    def isFinaltmfPacket(self):
        if not artificial.isArtificialPacket(self):
            self._finaltmf_ = 0
            return self._finaltmf_
        byte2 = struct.unpack('c', self.p[2])[0]
        if not byte2 == chr(0x02):
            self._finaltmf_ = 0
            return self._finaltmf_
        self._finaltmf_ = 1
        return self._finaltmf_
    
    def name(self):
        if not self._name_:
            self._name_ = 'ossftmf'
        return self._name_
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isFinaltmfPacket'] = self.isFinaltmfPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
            self._header_['samples'] = self.samples()
            self._header_['measurementsPerSample'] = self.measurementsPerSample()
            self._header_['deviceId'] = self.deviceId()
        return self._header_  
   
###############################################################################    
class finalbias(artificial):
    def __init__(self, packet, showWarnings=0):
        artificial.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._finalbias_ = None
        if not self.isFinalbiasPacket():
            raise WrongTypeOfPacket
        self.type = 'mams_accel_ossfbias'
        self._name_ = None

    # return true if this appears to be an finalbias packet
    def isFinalbiasPacket(self):
        if not artificial.isArtificialPacket(self):
            self._finalbias_ = 0
            return self._finalbias_
        byte2 = struct.unpack('c', self.p[2])[0]
        if not byte2 == chr(0x03):
            self._finalbias_ = 0
            return self._finalbias_
        self._finalbias_ = 1
        return self._finalbias_
    
    def name(self):
        if not self._name_:
            self._name_ = 'ossfbias'
        return self._name_
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isFinalbiasPacket'] = self.isFinalbiasPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
            self._header_['samples'] = self.samples()
            self._header_['measurementsPerSample'] = self.measurementsPerSample()
            self._header_['deviceId'] = self.deviceId()
        return self._header_
    
###############################################################################    
class radgse(artificial):
    def __init__(self, packet, showWarnings=0):
        artificial.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._radgse_ = None
        if not self.isRadgsePacket():
            raise WrongTypeOfPacket
        self.type = 'iss_rad'
        self._name_ = None

    # return true if this appears to be an finalbias packet
    def isRadgsePacket(self):
        if not artificial.isArtificialPacket(self):
            self._radgse_ = 0
            return self._radgse_
        byte2 = struct.unpack('c', self.p[2])[0]
        if not byte2 == chr(0x04):
            self._radgse_ = 0
            return self._radgse_
        self._radgse_ = 1
        return self._radgse_
    
    def name(self):
        if not self._name_:
            self._name_ = 'radgse'
        return self._name_
    
    def dataDirName(self):
        return 'iss_rad_radgse'
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isRadgsePacket'] = self.isRadgsePacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
            self._header_['samples'] = self.samples()
            self._header_['measurementsPerSample'] = self.measurementsPerSample()
            self._header_['deviceId'] = self.deviceId()
        return self._header_
    
    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % self.time()
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % 1.0
        return self._xmlHeader_
     
###############################################################################    
class samsff(artificial):
    def __init__(self, packet, showWarnings=0):
        artificial.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._samsff_ = None
        if not self.isSamsffPacket():
            raise WrongTypeOfPacket
        self.type = 'samsff_accel'
        self._name_ = None

    # return true if this appears to be an samsff packet
    def isSamsffPacket(self):
        if not artificial.isArtificialPacket(self):
            self._samsff_ = 0
            return self._samsff_
        byte2 = struct.unpack('c', self.p[2])[0]
        if not byte2 == chr(0x05):
            self._samsff_ = 0
            return self._samsff_
        self._samsff_ = 1
        return self._samsff_
    
    def name(self):
        if not self._name_:
            self._name_ = 'samsff%02d' % self.deviceId()
        return self._name_
    
    def dataDirName(self):
        return 'samsff_accel_samsff%02d' % self.deviceId()

    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % self.time()
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % (self.rate()/3.8)
        return self._xmlHeader_

    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isSamsffPacket'] = self.isSamsffPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
            self._header_['samples'] = self.samples()
            self._header_['measurementsPerSample'] = self.measurementsPerSample()
            self._header_['deviceId'] = self.deviceId()
        return self._header_
       
###############################################################################    
class hirap(accelPacket):
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        accelPacket.__init__(self, packet)
        self._showWarnings_ = showWarnings
        self._hirap_ = None
        if not self.isHirapPacket():
            raise WrongTypeOfPacket
        self.type = 'mams_accel_hirap'
        self._name_ = 'hirap'
        self._rate_ = 1000.0
        self._samples_ = 192 # all hirap packets have 192 samples
        self._header_ = {}
        self._time_ = None
        self._endTime_ = None
        self._xyz_ = []
        self._txyz_ = []
        self._xmlHeader_ = None
            
    # return true if this appears to be a hirap acceleration packet
    def isHirapPacket(self):
        if 1172 != len(self.p): # all Hirap packets have the same length
            self._hirap_ = 0
            return self._hirap_
        try:
            self.time() # make sure time is really BCD compatible values
            self._hirap_ = 1
        except 'ValueError' as value:
            t = UnixToHumanTime(time(), 1) + ' packet with bad time ignored'
            printLog(t)
            self._oss_ = 0
        except BCDConversionException as value:
            self._hirap_ = 0
        return self._hirap_
    
    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % UnixToHumanTime(self.time())
            self._xmlHeader_ = self._xmlHeader_ + '\t<SampleRate>%s</SampleRate>\n' % self.rate()
            self._xmlHeader_ = self._xmlHeader_ + '\t<CutoffFreq>%s</CutoffFreq>\n' % 100
            self._xmlHeader_ = self._xmlHeader_ + '\t<Gain>%s</Gain>\n' % 1
        return self._xmlHeader_
    
    # return header dictionary appropriate for this packet (everything except the accel data)
    def header(self):
        if not self._header_:
            self._header_['name'] = self.name()
            self._header_['isHirapPacket'] = self.isHirapPacket()
            self._header_['rate'] = self.rate()
            self._header_['time'] = self.time()
            self._header_['endTime'] = self.endTime()
        return self._header_

    def name(self):
        if not self._name_:
            self._name_ = 'osshirap'
        return self._name_

    def rate(self):
        if not self._rate_:
            self._rate_ = 1000.0
        return self._rate_

    def time(self):
        if not self._time_:
            century = BCD(self.p[0])
            year =    BCD(self.p[1]) + 100*century
            month =   BCD(self.p[2])
            day =     BCD(self.p[3])
            hour =    BCD(self.p[4])
            minute =  BCD(self.p[5])
            second =  BCD(self.p[6])
            millisec = struct.unpack('h', self.p[8:10])[0]
            millisec = millisec & 0xffff
            self._time_ = HumanToUnixTime(month, day, year, hour, minute, second, millisec/1000.0)
        return self._time_
    
    def endTime(self):
        if not self._endTime_:
            # all hirap packets have 192 samples
            self._endTime_ = self.time() + (self.samples() - 1.0) / self.rate() 
        return self._endTime_

    def samples(self): 
        if not self._samples_:
            self._samples_ = 192.0
        return self._samples_

    def xyz(self):
        if not self._xyz_:
            for i in range(192):
                start = 20+6*i
                stop = start+6
                x, y, z = struct.unpack('hhh', self.p[start:stop])
                self._xyz_.append((x/2048000.0, y/2048000.0, z/2048000.0)) # 16 / 32768 / 1000= 1/2048000
        return self._xyz_

    def txyz(self):
        if not self._txyz_:
            dt = 1.0/self.rate()
            for i in range(192):
                start = 20+6*i
                stop = start+6
                x, y, z = struct.unpack('hhh', self.p[start:stop])
                t = i*dt
                self._txyz_.append((t, x/2048000.0, y/2048000.0, z/2048000.0)) # 16 / 32768 / 1000= 1/2048000
        return self._txyz_
   
###############################################################################    
class sams2Packet(accelPacket):
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        accelPacket.__init__(self, packet)
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
        minSamples = { 62.5:31, 125.0:62, 250.0:51, 500.0:28, 1000.0:56 }
        if not other:
#            print('contiguous: no other')
            return 0
        if self.type != other.type: # maybe we should throw an exception here
#            print('contiguous: other type mis-match')
            return 0
        if self.rate() != other.rate():
#            print('contiguous: other rate mis-match')
            return 0
        if self._dqmIndicator_ != other._dqmIndicator_:
#            print('contiguous: other dqm mis-match')
            return 0
        ostart = other.time()
        oend = other.endTime()
        start = self.time()
        if self.rate() == 0: # non-periodic data
#            print('contiguous: OK non-periodic')
            return (start > oend)
        gap = start - oend
        allowAbleGap = minSamples[self.rate()]/self.rate()
        result =  (start >= ostart) and (gap <= allowAbleGap)
#        if not result:
#             print('contiguous:%s ostart:%.4lf oend:%.4lf start:%.4lf gap:%.4lf') % (result, ostart, oend, start, gap) 
        return result

    # name of the database table this data should be in (no dashes)
    def name(self):
        if not self._name_:
             self._name_ = self.seId()
        return  self._name_

    # return true if this appears to be a sams2 acceleration packet
    def isSams2Packet(self): # struct.unpack doesn't seem to think 'h' is 2 bytes

        if not self._sams2_:
            if len(self.p) < 68:
                self._sams2_ = 0
                if self._showWarnings_:
                    t = 'SAMSII packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
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
                    t = 'SAMSII packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
                    t = t + ' packet cannot be sams-ii accel because it does not start with 0xdabe'
                    printLog(t)
                return self._sams2_
            byte2 = struct.unpack('c', self.p[12])[0]
            byte3 = struct.unpack('c', self.p[13])[0]
            accelpacket = (byte2 == chr(100)) and (byte3 == chr(0))
            if not accelpacket and self._showWarnings_:
                self._sams2_ = 0
                t = 'SAMSII packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
                t = t + ' packet cannot be sams-ii accel because it does not have 0x6400 at offset 12'
                printLog(t)
                return self._sams2_
            if len(self.p) < 52+16*self.samples():
                self._sams2_ = 0
                t = 'SAMSII packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
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
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % UnixToHumanTime(self.time())
            self._xmlHeader_ = self._xmlHeader_ + '\t<Gain>%s</Gain>\n' % self.gain()
            #self._xmlHeader_ = self._xmlHeader_ + '\t<Units>%s</Units>\n' % self.unit()
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
            self._eeId_ = replace(self._eeId_ , chr(0), '') # delete nulls
            self._eeId_ = join(split(self._eeId_, '-'), '') # delete dashes
        return self._eeId_
    
    def seId(self):
        if not self._seId_:
            self._seId_ = self.p[24:32]
            self._seId_ = replace(self._seId_ , chr(0), '') # delete nulls
            self._seId_ = join(split(self._seId_, '-'), '') # delete dashes
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
            if self._showWarnings_: # check for mis-matched rate bytes
                for i in range(16, 161, 16): # check next 10 rate bytes
                    if 64+i >= len(self.p):
                        break
                    dupRate = struct.unpack('b', self.p[64+i])[0] & 0x07
                    if dupRate != self._rate_:
                        t = UnixToHumanTime(time(), 1) + '\n'  
                        t = t + ' mis-matched rate bytes, %s at offset 64 and %s at offset %s\n' % (self._rate_, dupRate, 64+i)
                        t = t + self.dump()
                        printLog(t)
                        break
            if (self._rate_ == 0):
                self._rate_ = 62.5
            elif (self._rate_ == 1):
                self._rate_ = 125.0
            elif (self._rate_ == 2): # will have to split packet for this rate and above
                self._rate_ = 250.0
            elif (self._rate_ == 3):
                self._rate_ = 500.0
            elif (self._rate_ == 4):
                self._rate_ = 1000.0
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' bogusRateByte: %s at time %.4f, assuming rate=1000' % (self._rate_, self.time())
                    printLog(t)
                self._rate_ = 1000.0
        return self._rate_
    
    def gain(self):
        if not self._gain_:
            self._gain_ = (struct.unpack('b', self.p[64])[0] & 0x18 ) >> 3
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
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' bogusGainByte: %s at time %.4f, assuming gain=1' % (self._gain_, self.time())
                    printLog(t)
                self._gain_ = 1.0
        return self._gain_

    def unit(self):
        if not self._unit_:
            self._unit_ = (struct.unpack('b', self.p[65])[0] )
            if (self._unit_ == 1):
                self._unit_ = 'counts'
            elif (self._unit_ == 2):
                self._unit_ = 'volts'
            elif (self._unit_ == 3):
                self._unit_ = 'g'
            else:
                if self._showWarnings_:
                    t = '\n' + self.hexDump()
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' bogusUnitByte: %s at time %.4f, assuming unit=ug' % (self._unit_, self.time())
                    printLog(t)
                self._unit_ = 'ug'
        return self._unit_

    def adjustment(self):
        if not self._adjustment_:
            a = (struct.unpack('b', self.p[66])[0] )
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
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' bogusAdjustmentByte: %s at time %.4f, ignoring' % (a, self.time())
                    printLog(t)
        return self._adjustment_

    def time(self):
        if not self._time_:
            sec, usec = struct.unpack('II', self.p[36:44])
            self._time_ = sec + usec/1000000.0
        return self._time_
    
    def endTime(self):
        if not self._endTime_:
            self._endTime_ = self.time() + (self.samples()-1) / self.rate() 
        return self._endTime_

    def xyz(self):
        if not self._xyz_:
            convert = 0
            if self.unit() != 'g':
                convert = 1
                if self.unit() == 'volts':
                    m = 1.0/3.89791388
                    b = 0
                else: # must be counts
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
                start = 52+16*i
                stop = start+16
                x, y, z, j = struct.unpack('fffI', self.p[start:stop])
                if convert:
                    x, y, z = x*m+b, y*m+b, z*m+b
                self._xyz_.append((x,y,z))
        return self._xyz_
    
    def txyz(self):
        if not self._txyz_:
            dt = 1.0/self.rate()
            convert = 0
            if self.unit() != 'g':
                convert = 1
                if self.unit() == 'volts':
                    m = 1.0/3.89791388
                    b = 0
                else: # must be counts
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
                start = 52+16*i
                stop = start+16
                x, y, z, j = struct.unpack('fffI', self.p[start:stop])
                if convert:
                    x, y, z = x*m+b, y*m+b, z*m+b
                t = i*dt
                self._txyz_.append((t,x,y,z))
        return self._txyz_
    
###############################################################################   
class samsTshEs(accelPacket):
    # packets don't change, so we can cache all the calculated values for reuse
    def __init__(self, packet, showWarnings=0):
        accelPacket.__init__(self, packet)
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
        return 3 # what about 'something interesting happened' bit?

    # return true if this packet is contiguous with the supplied packet
    def contiguous(self, other): 
        if not other:
#            print('contiguous: no other')
            return 0
        if self.type != other.type: # maybe we should throw an exception here
#            print('contiguous: other type mis-match')
            return 0
        if self.rate() != other.rate():
#            print('contiguous: other rate mis-match')
            return 0
        if self._dqmIndicator_ != other._dqmIndicator_:
#            print('contiguous: other dqm mis-match')
            return 0
        ostart = other.time()
        oend = other.endTime()
        start = self.time()
        if self.rate() == 0: # non-periodic data
#            print('contiguous: OK non-periodic')
            return (start > oend)
        #### during testing, all tsh-es packets are maximum size and very regular
        #### on orbit, theu will be broken into multiple smaller packets of unknown size
        #### once we know the correct sizes, minSamples should be reduced
        minSamples = { 1000.:512, 500.0:512, 250.0:256, 125.0:128, 62.5:64, 31.25:64, 15.625:64, 7.8125:32 }
        gap = start - oend
        allowAbleGap = minSamples[self.rate()]/self.rate()
        result =  (start >= ostart) and (gap <= allowAbleGap)
#        if not result:
#             print('contiguous:%s ostart:%.4lf oend:%.4lf start:%.4lf gap:%.4lf') % (result, ostart, oend, start, gap) 
        return result

    # name of the database table this data should be in (no dashes)
    def name(self):
        if not self._name_:
             self._name_ = self.Id()
        return  self._name_

    # return true if this appears to be a samsTshEs acceleration packet
    def isSamsTshEsPacket(self): # struct.unpack doesn't seem to think 'h' is 2 bytes
        if not self._samsTshEs_:
            if len(self.p) < 80:
                self._samsTshEs_ = 0
                if self._showWarnings_:
                    t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
                    t = t + ' packet too short (%s) to be a samsTshEs acceleration packet' % len(self.p)
                    printLog(t)
                return self._samsTshEs_
            # byte0 = struct.unpack('c', self.p[0])[0]
            # byte1 = struct.unpack('c', self.p[1])[0]
            byte0 = struct.unpack('c', bytes([self.p[0]]))[0]
            byte1 = struct.unpack('c', bytes([self.p[1]]))[0]
            # if not (byte0 == chr(0xac) and byte1 == chr(0xd3)):
            if not (byte0 == bytes([0xac]) and byte1 == bytes([0xd3])):
                self._samsTshEs_ = 0
                if self._showWarnings_:
                    t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
                    t = t + ' packet cannot be samsTshEs accel because it does not start with 0xacd3'
                    printLog(t)
                return self._samsTshEs_
            # byte2 = struct.unpack('c', self.p[40])[0]
            # byte3 = struct.unpack('c', self.p[41])[0]
            byte2 = struct.unpack('c', bytes([self.p[40]]))[0]
            byte3 = struct.unpack('c', bytes([self.p[41]]))[0]
            selector = ord(byte2)*256+ord(byte3)
            accelpacket = (selector == 170) or (selector == 171)  # || (selector == 177)
            if not accelpacket:
                self._samsTshEs_ = 0
                if self._showWarnings_:
                    t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
                    t = t + ' packet cannot be samsTshEs accel because it does not have an TshesAccelPacket selector at offset 40'
                    printLog(t)
                return self._samsTshEs_
            if len(self.p) < 80+16*self.samples():
                self._sams2_ = 0
                t = 'SAMS TSH-ES packet warning\n' + self.hexDump() + UnixToHumanTime(time(), 1) + '\n'  
                t = t + ' packet is not a complete samsTshEs accel packet, %s samples are not present' % self.samples()
                printLog(t)
                return self._samsTshEs_
            self._samsTshEs_ = 1
            self.addAdditionalDQM(self.adjustment())
        return self._samsTshEs_

    # return header info in XML format for this packet
    def xmlHeader(self):
        if not self._xmlHeader_:
            self._xmlHeader_ = ''
            self._xmlHeader_ = self._xmlHeader_ + '\t<SensorID>%s</SensorID>\n' % self.name()
            self._xmlHeader_ = self._xmlHeader_ + '\t<TimeZero>%s</TimeZero>\n' % UnixToHumanTime(self.time())
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
        if not self._Id_:
            self._Id_ = self.p[44:60]
            # self._Id_ = replace(self._Id_ , chr(0), '')  # delete nulls
            # self._Id_ = join(split(self._Id_, '-'), '')  # delete dashes
            self._Id_ = self._Id_.replace(b'-', b'').replace(b'\0', b'')  # delete dashes and nulls
            self._Id_ = self._Id_[-4:]                   # keep last 4 characters only, i.e., "es13"
        return self._Id_
        
    def status(self): # packet status
        if not self._status_:
            self._status_ = struct.unpack('!i', self.p[72:76])[0] # Network byte order
        return self._status_

    def samples(self):
        if not self._samples_:
            self._samples_ = struct.unpack('!i', self.p[76:80])[0] # Network byte order
        return self._samples_

    def rate(self):
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
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' bogusRateByte: %s at time %.4f, assuming rate=1000' % (rateBits, self.time())
                    printLog(t)
                self._rate_ = 1000.0
        return self._rate_
    
    def gain(self):
        if not self._gain_:
            statusInt = self.status()
            gainBits = statusInt & 0x001f
            
            if (gainBits == 0):
                self._gain_ = 1.0
                self._input_ = 'Ground' # _input_ is not used as far as I can tell
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
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' TSH-ES bogusGainByte: %s at time %.4f, assuming gain=1' % (gainBits, self.time())
                    printLog(t)
                self._gain_ = 1.0
        return self._gain_

    def unit(self):
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
                    t = t + '\n' +  self.dump()
                    t = t + '\n' +  UnixToHumanTime(time(), 1),  
                    t = t + '\n' +  ' TSH-ES bogusUnitByte: %s at time %.4f, assuming unit=g' % (unitBits, self.time())
                    printLog(t)
                self._unit_ = 'g'
        return self._unit_

    def adjustment(self):
        if not self._adjustment_:
            statusInt = self.status()
            adjBits = (statusInt & 0x0080) >> 7

            self._dqmIndicator_ = adjBits
            self._adjustment_ = 'no-compensation'
            if (adjBits == 1):
                self._adjustment_ = 'temperature-compensation'
        return self._adjustment_

    def time(self):
        if not self._time_:
            sec, usec = struct.unpack('!II', self.p[64:72]) # Network byte order
            self._time_ = sec + usec/1000000.0
        return self._time_
    
    def endTime(self): 
        if not self._endTime_:
            self._endTime_ = self.time() + (self.samples()-1) / self.rate() 
        return self._endTime_
    
    def handleDigitalIOstatus(self, digitalIOstatus, sampleNumber):
        # check for the 'something interesting happened' bit for this sensor and do something with it
        enabled = digitalIOstatus & 0x0001
        if enabled:
            inputIO = (digitalIOstatus & 0x0004) > 2
            if self.name() in DigitalIOstatusHolder:
                interestingBit = DigitalIOstatusHolder[self.name()]
                if interestingBit != inputIO: # state change
                    DigitalIOstatusHolder[self.name()] = inputIO
                    # state change detected, what should be do with that information?
                    eventTime = self.time() + sampleNumber/self.rate()
                    msg = ' (inputIO_state_change:%s time:%.4f)' % (inputIO, eventTime)
                    #print self.name(), msg
            else:
                DigitalIOstatusHolder[self.name()] = inputIO

    def xyz(self):
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
                start = 80+16*i
                stop = start+16
                x, y, z, digitalIOstatus = struct.unpack('!fffI', self.p[start:stop]) # Network byte order
                self.handleDigitalIOstatus(digitalIOstatus, i)
                if convert:
                    x, y, z = x*mx+bx, y*my+by, z*mz+bz
                self._xyz_.append((x,y,z))
        return self._xyz_
    
    def txyz(self):
        if not self._txyz_:
            dt = 1.0/self.rate()
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
                start = 80+16*i
                stop = start+16
                x, y, z, digitalIOstatus = struct.unpack('!fffI', self.p[start:stop]) # Network byte order
                self.handleDigitalIOstatus(digitalIOstatus, i)
                if convert:
                    x, y, z = x*mx+bx, y*my+by, z*mz+bz
                t = i*dt
                self._txyz_.append((t,x,y,z))
        return self._txyz_


def get_butter_analog(forder, cutoff):
    """return numerator (b) & denominator (a) polynomial coeffs of IIR lowpass filter"""
    rad_per_sec = 2 * np.pi * cutoff    
    b, a = scipy.signal.butter(forder, rad_per_sec, 'low', analog=True)
    return b, a


def get_butter_digital(fs, fc, norder=4):
    """return numerator (b) & denominator (a) polynomial coeffs of Butterworth LPF"""
    pct_nyq = 2.0 * fc / fs
    # create nth order lowpass butterworth filter
    b, a = scipy.signal.butter(norder, pct_nyq)  # e.g. 5% of Nyquist = 5% of 50 sa/sec = 2.5 Hz
    return b, a


def show_butter(b, a):
    """plot frequency response of butterworth lowpass filter"""
    w, h = scipy.signal.freqs(b, a)
    plt.semilogx(w/2.0/np.pi, 20 * np.log10(abs(h)))
    plt.title('Butterworth filter frequency response')
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Amplitude [dB]')
    plt.margins(0, 0.1)
    plt.grid(which='both', axis='both')
    plt.axvline(cutoff, color='green')  # cutoff frequency
    plt.show()    


def lowpass_filtfilt(t, xn, fs, fc, b, a):
    """lowpass filter, like MATLAB filtfilt"""
    
    # apply the filter to xn; use lfilter_zi to choose the initial condition of the filter   
    zi = scipy.signal.lfilter_zi(b, a)
    z, _ = scipy.signal.lfilter(b, a, xn, zi=zi*xn[0])
    
    # apply the filter again, to have a result filtered at an order the same as filtfilt
    z2, _ = scipy.signal.lfilter(b, a, z, zi=zi*z[0])
    
    # use filtfilt to apply the filter
    y = scipy.signal.filtfilt(b, a, xn)

    return y


def demo_lowpass():
    """demo filtfilt (like MATLAB) scheme for lowpass filtering"""
    
    # create test signal
    fs = 250  # samples per second
    tmin, tmax = -1, 1
    numsteps = (tmax - tmin) * fs + 1
    t = np.linspace(tmin, tmax, numsteps)
    x = (np.sin(2*np.pi*0.77*t*(1-t) + 2.1) +   # LPF preserves this 0.77 Hz
         0.1*np.sin(2*np.pi*1.22*t + 1) +       # LPF preserves this 1.22 Hz
         0.18*np.cos(2*np.pi*3.88*t))           # LPF attenuates this 3.88 Hz
    xn = x + np.random.randn(len(t)) * 0.08     # LPF attenuates "high-freq." noise
    
    # create nth order lowpass butterworth filter
    norder = 4  # order of LPF
    fc = 2.5  # Hz; our desired cutoff freq
    b, a = get_butter_digital(fs, fc, norder=norder)
    
    # use something like MATLAB's filtfilt to apply the filter 
    y = lowpass_filtfilt(t, xn, fs, fc, b, a)
    
    # plot the original signal and the various filtered versions
    plt.figure
    plt.plot(t, xn, 'b', alpha=0.75)
    plt.plot(t, y, 'r')
    plt.legend(('noisy signal', 'filtfilt'), loc='best')
    plt.grid(True)
    plt.show()


def get_accel_from_db(table, ax, num_pkts):
    """get ax'th column from num_pkts from db table"""
    
    results = sqlConnect('select * from %s order by time desc limit %d' % (table, num_pkts), 'localhost')
    
    # initialize list array to be returned in flattened form
    x = []
    
    # special handling of first packet to get start time
    # NOTE: we used "desc" in query so gotta index from the "end"
    i1 = results[-1]
    p1 = guessPacket(i1[1])
    start_time = p1.time()
    #print UnixToHumanTime(start_time)
    
    # append first packet's worth to output
    x.append( [ a[ax] for a in p1.txyz() ] )
    
    # NOTE: we used "desc" in query so gotta loop backwards here
    # now iterate over remaining packets to build output
    for i in results[-2::-1]:  # i[0] is time, i[1] is the blob, i[2] is the type
        p = guessPacket(i[1])
        #start_time2 = p.time()
        #print UnixToHumanTime(start_time2)
        x.append( [ a[ax] for a in p.txyz() ] )
        
    # returned flattened array version of x and the start_time for this chunk
    return [ item for sublist in x for item in sublist ], start_time


def display_accel(table, k=0, sleep_sec=1):
    """display kth sample from each packet with MySQL query ("desc limit 1")"""
    title='\33]0;' + table + ' Accel Packets\a'
    stdout.write(bytes(title))
    stdout.flush()
    while 1:
        results = sqlConnect('select * from %s order by time desc limit 1' % table, 'localhost')
        os.system('clear')
        os.system('date')
    
        for i in results:
            # i[0] is time, i[1] is the blob, i[2] is the type
            p = guessPacket(i[1])  # just do the guessing once per iteration
            print('Packet Time:', UnixToHumanTime(p.time()))
            print('Name:', p.name())
            print('Rate:', p.rate())
            print('Gain:', p.gain())
            print('Unit:', p.unit())
            print('Samples:', p.samples())
            print('Adjustment:', p.adjustment())
            txyz = np.array(p.txyz())  # use numpy array for downstream handling
            #fda = lowpass_old(txyz[:, 1:], 4, 1, 250)  # skip time column for filtering
            # show kth sample of something like 64 samples in this packet
            print('Time   :', txyz[k][0])
            print('X Accel:', txyz[k][1])
            print('Y Accel:', txyz[k][2])
            print('Z Accel:', txyz[k][3])
            print('')
            print('---------------------------')
        
        print('displayAccel.py v1.0')
        print('Press CTRL-C to stop')
        sleep(sleep_sec)


def run(table, fs, fc, ax, num_pkts, xlabel, ylabel, pause_sec):
    """main routine for live LPF plotting"""
    
    # create nth order lowpass butterworth filter
    norder = 4  # order of LPF
    b, a = get_butter_digital(fs, fc, norder=norder)

    # endless plot loop
    line1 = []
    while True:
        
        # get latest set of data from db table (just ax axis)
        data, start_time = get_accel_from_db(table, ax, num_pkts)
        xn = np.array(data)
        
        # generate time vector sequence (FIXME assuming no gaps)
        #t = np.linspace(start_time, start_time+(len(xn)-1)/fs, len(xn), endpoint=True)
        t = np.linspace(0.0, (len(xn)-1)/fs, len(xn), endpoint=True)
        
        # apply LPF
        y = lowpass_filtfilt(t, xn, fs, fc, b, a)
        
        ## plot the original signal and the filtered version
        #plt.figure
        #plt.plot(t, xn, 'b', alpha=0.75)
        #plt.plot(t, y, 'r')
        #plt.legend(('noisy signal', 'filtfilt'), loc='best')
        #plt.grid(True)
        #plt.show()
        
        # call live plotter    
        ident = UnixToHumanTime(start_time) + '   [ now: %s ]' % datetime.datetime.now()
        line1 = live_plot_xy(t, y, line1, xlabel=xlabel, ylabel=ylabel, identifier=ident, pause_sec=pause_sec)


def parameters_ok():
    """check for reasonableness of parameters"""    

    # FIXME we do not check table string at all
    
    # make sure we can get an integer value here, as expected
    try:
        parameters['num_pkts'] = int(parameters['num_pkts'])
    except Exception as e:
        print('did not get num_pkts as int: %s' % e.message)
        return False    
    
    # make sure we can get an integer value (1, 2 or 3), as expected
    try:
        parameters['ax'] = int(parameters['ax'])
        assert(0 < parameters['ax'] < 4)
    except Exception as e:
        print('did not get ax as int value (1, 2 or 3): %s' % e.message)
        return False
    
    # make sure we can get an integer value here, as expected
    try:
        parameters['fc'] = int(parameters['fc'])
    except Exception as e:
        print('did not get fc as int: %s' % e.message)
        return False    

    # make sure we can get a float value here, as expected
    try:
        parameters['fs'] = float(parameters['fs'])
    except Exception as e:
        print('did not get fs as float: %s' % e.message)
        return False    

    # make sure we can get a float value here, as expected
    try:
        parameters['pause_sec'] = float(parameters['pause_sec'])
    except Exception as e:
        print('did not get pause_sec as float: %s' % e.message)
        return False
    
    # be sure user did not mistype or include a parameter we are not expecting
    s1, s2 = set(parameters.keys()), set(defaults.keys())
    if s1 != s2:
        extra = list(s1-s2)
        missing = list(s2-s1)
        if extra:   print('extra   parameters -->', extra)
        if missing: print('missing parameters -->', missing)
        return False    

    return True # all OK; otherwise, we'd have returned False somewhere above


def print_usage():
    """print helpful text how to run the program"""
    print('usage: %s [options]' % os.path.abspath(__file__))
    print('       options (and default values) are:')
    for i in list(defaults.keys()):
        print('\t%s=%s' % (i, defaults[i]))


def main(argv):
    """parse command line parameters and branch to mode of operation if parameters are okay"""
    
    # parse command line
    for p in argv[1:]:
        pair = p.split('=')
        if (2 != len(pair)):
            print('bad parameter: %s' % p)
            break
        else:
            parameters[pair[0]] = pair[1]
    else:
        if parameters_ok():
            print(parameters)
            table = parameters['table']
            fs = parameters['fs']
            fc = parameters['fc']
            ax = parameters['ax']
            num_pkts = parameters['num_pkts']
            pause_sec = parameters['pause_sec']            
            # branch to different modes here
            if fs == 0 or fc == 0 or num_pkts == 0:
                display_accel(parameters['table'], k=0, sleep_sec=1)
            else:
                # get labels
                xlabel, ylabel = 'time (sec)', 'axis #%d (g)' % parameters['ax']        
                # call main routine to do endless loop live LPF plotting
                run(table, fs, fc, ax, num_pkts, xlabel, ylabel, pause_sec)
                
            return 0  # zero is return code of success for unix
        
    print_usage()  


if __name__ == '__main__':
    """run main with cmd line args and return exit code"""
    sys.exit(main(sys.argv))

