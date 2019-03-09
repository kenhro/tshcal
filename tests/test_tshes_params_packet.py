# in tshcal directory, run
# /path/to/venv/python.exe -m pytest -v -s

from common.tshes_params_packet import TshesParamsPacket


class TestTshesParamsPacket(object):

    def setup_method(self, method):
        self.tpp = TshesParamsPacket('one', 'two', 'three', 4)

    def test_ntoh(self):
        print('\nBEFORE NTOH', self.tpp.val)
        self.tpp.ntoh()
        print('AFTER NTOH', self.tpp.val)
        assert self.tpp.val == 4

    def test_hton(self):
        print('\nBEFORE HTON', self.tpp.val)
        self.tpp.hton()
        print('AFTER HTON', self.tpp.val)
        assert self.tpp.val == 67108864  # 4 converted from host to network byte order
