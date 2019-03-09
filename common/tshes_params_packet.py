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
