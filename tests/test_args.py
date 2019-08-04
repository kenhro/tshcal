#!/usr/bin/env python3

import sys
from tshcal.inputs import argparser


class TestArgParser(object):
    """class to test argparser module"""

    def setup_method(self, method):
        """setup for general use in test methods of this class"""
        # hijack sys.argv, which is a list, for testing purposes
        sys.argv = ['t_e_s_t', '-v', '-r', '250.0']
        self.args = argparser.parse_inputs()

    def test_some_parser_booleans(self):
        """test some booleans"""
        assert self.args.plot is True
        assert self.args.debug is False
        assert self.args.fake_esp is False
        assert self.args.fake_tsh is False

    def test_some_parser_defaults(self):
        """test some default args"""
        assert self.args.rate == 250.0
        assert self.args.gain == 1
