# in tshcal directory, run
# /path/to/venv/python.exe -m pytest -v -s  # include -s to see stdout (print statements)

from common.tshes_params_packet import TshesParamsPacket


class TestTshesParamsPacket(object):
    """class to test TshesParamsPacket"""

    def setup_method(self, method):
        """setup for general use in test methods of this class"""
        self.tpp = TshesParamsPacket('one', 'two', 'three', 4)  # note last arg, val = 4

    def test_ntoh(self):
        """test network to host byte order conversion"""
        # for this test, we first need to convert to network byte order
        self.tpp.hton()
        print('\nBEFORE NTOH', self.tpp.val)
        self.tpp.ntoh()
        print('AFTER NTOH', self.tpp.val)
        assert self.tpp.val == 4

    def test_hton(self):
        """test host to network byte order conversion"""
        print('\nBEFORE HTON', self.tpp.val)
        self.tpp.hton()
        print('AFTER HTON', self.tpp.val)
        assert self.tpp.val == 67108864  # 4 converted from host to network byte order
