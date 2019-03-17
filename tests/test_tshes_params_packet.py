# cd to tshcal directory, then run following
# /path/to/venv/python.exe -m pytest -v -s  # include -s to see stdout (print statements)

import datetime
from common.tshes_params_packet import TshesParamsPacket
from common.time_utils import ceil_dtm


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


class TestTimeUtils(object):
    """class to test time utils"""

    def setup_method(self, method):
        """setup for general use in test methods of this class"""
        self.dtm = datetime.datetime(2019, 3, 17, 8, 0, 1)
        self.tdelta = datetime.timedelta(minutes=30)

    def test_ceil_dtm(self):
        """test ceil_dtm function"""
        # for this test, we first need to convert to network byte order
        result = ceil_dtm(self.dtm, self.tdelta)
        assert result == datetime.datetime(2019, 3, 17, 8, 30)
