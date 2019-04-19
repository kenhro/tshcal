import struct
import socket

class TshesParamsPacket(object):
    """A class used in TSH-ES command messages to send values and password info to the TSH-ES.
    Note that since byte ordering might not be same on sending and receiving machines, the user should be sure to
    call ntoh() on a received packet and call hton() before sending one out.  This only affects the integer attribute,
    val, because according to Daveware, character arrays [strings in Python?] do not suffer from endian-ness."""

    def __init__(self, id, usr, pw, val):
        self.id = id
        self.usr = usr
        self.pw = pw
        self.val = val

    def __str__(self):
        return 'DeviceID:%s User:%s Pwd:%s Val:%d' % (self.id, self.usr, self.pw, self.val)

    def __setattr__(self, name, value):
        """override the set attribute method with type checking...C'mon man...type-checking in Python, really?!"""
        if name == 'val' and not isinstance(value, int):
            raise TypeError('TshesParamsPacket.val must be an int')
        elif name in ['id', 'usr', 'pw'] and not isinstance(value, str):
            raise TypeError('TshesParamsPacket.%s must be a string' % name)
        super().__setattr__(name, value)

    def ntoh(self):
        """For a received packet, convert 32-bit positive integers from network to host byte order. On machines where
        the host byte order is the same as network byte order, this is a no-op; otherwise, it performs a 4-byte swap
        operation.  Only do this for the integer attribute, val."""
        self.val = socket.ntohl(self.val)

    def hton(self):
        """For a received packet, convert 32-bit positive integers from host to network byte order. On machines where
        the host byte order is the same as network byte order, this is a no-op; otherwise, it performs a 4-byte swap
        operation.  Only do this for the integer attribute, val."""
        self.val = socket.htonl(self.val)


class TshesMessage(object):
    """A class to handle tshes message packets."""

    def __init__(self, p):
        self.p = p

    def enum_bytes(self):
        for idx, b in enumerate(self.p):
            # print('{:<8}{:<#8x}{}'.format(idx, b, self.p[i:i+1]))
            print('{:<8}{:<#8x}'.format(idx, b))
        print('-.' * 22)

    def __str__(self):

        # two sync bytes
        byte0 = struct.unpack('c', bytes([self.p[0]]))[0]
        byte1 = struct.unpack('c', bytes([self.p[1]]))[0]
        if not (byte0 == bytes([0xac]) and byte1 == bytes([0xd3])):
            raise ValueError('bad sync bytes for TshesMessage')

        # msg_size is total number of bytes in message (includes sync bytes and msg_size)
        byte2 = struct.unpack('c', bytes([self.p[2]]))[0]
        byte3 = struct.unpack('c', bytes([self.p[3]]))[0]
        msg_size = ord(byte2) * 256 + ord(byte3)

        # sequence number
        byte4 = struct.unpack('c', bytes([self.p[4]]))[0]
        byte5 = struct.unpack('c', bytes([self.p[5]]))[0]
        seq_num = ord(byte4) * 256 + ord(byte5)

        # check sum
        byte6 = struct.unpack('c', bytes([self.p[6]]))[0]
        byte7 = struct.unpack('c', bytes([self.p[7]]))[0]
        chk_sum = ord(byte6) * 256 + ord(byte7)

        # source identifier
        src = self.p[8:24]
        src = src.replace(b'-', b'').replace(b'\0', b'')  # delete dashes and nulls
        # src = src[-4:]  # keep last 4 characters only, i.e., "es13"

        # destination identifier
        dst = self.p[24:40]
        dst = dst.replace(b'-', b'').replace(b'\0', b'')  # delete dashes and nulls

        # get selector value
        byte40 = struct.unpack('c', bytes([self.p[40]]))[0]
        byte41 = struct.unpack('c', bytes([self.p[41]]))[0]
        selector = ord(byte40) * 256 + ord(byte41)

        # get data size
        byte42 = struct.unpack('c', bytes([self.p[42]]))[0]
        byte43 = struct.unpack('c', bytes([self.p[43]]))[0]
        data_size = ord(byte42) * 256 + ord(byte43)

        # print(msg_size)
        # print(struct.unpack('H',  self.p[2:4]))

        # print(struct.unpack('16c',  self.p[8:24]))

        s = 'seq_num = ' + '{:>5d}'.format(seq_num)
        s += ', sync bytes: ' + str(byte0) + ' & ' + str(byte1)
        s += ', msg_size = ' + str(msg_size) + ' bytes'
        s += ', chk_sum = ' + '{:>6d}'.format(chk_sum)
        s += ', src: ' + str(src.decode('utf-8'))
        s += ', dst: ' + str(dst.decode('utf-8'))
        s += ', selector = ' + str(selector)
        s += ', data_size = ' + str(data_size)

        return s
