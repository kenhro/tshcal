##################################################################
# to run high-level tests, first change directory
cd /home/pims/dev/programs/python/tshcal


##################################################################
# then run with "tests" directory as argument (without quotes) -- add "-s" to include standard output
python3 -m pytest -v tests
==================== test session starts =============================================================================
platform linux -- Python 3.7.2, pytest-4.3.1, py-1.8.0, pluggy-0.9.0 -- /usr/local/bin/python3
cachedir: .pytest_cache
rootdir: /home/pims/dev/programs/python/tshcal, inifile:
collected 3 items

tests/test_tshes_params_packet.py::TestTshesParamsPacket::test_ntoh PASSED                                      [ 33%]
tests/test_tshes_params_packet.py::TestTshesParamsPacket::test_hton PASSED                                      [ 66%]
tests/test_tshes_params_packet.py::TestTimeUtils::test_ceil_dtm PASSED                                          [100%]

================= 3 passed in 0.02 seconds ===========================================================================


##################################################################
# add "dash s" to include standard output [does not show percentages!?]
python3 -m pytest -v tests -s
==================== test session starts =============================================================================
platform linux -- Python 3.7.2, pytest-4.3.1, py-1.8.0, pluggy-0.9.0 -- /usr/local/bin/python3
cachedir: .pytest_cache
rootdir: /home/pims/dev/programs/python/tshcal, inifile:
collected 3 items

tests/test_tshes_params_packet.py::TestTshesParamsPacket::test_ntoh
BEFORE NTOH 67108864
AFTER NTOH 4
PASSED
tests/test_tshes_params_packet.py::TestTshesParamsPacket::test_hton
BEFORE HTON 4
AFTER HTON 67108864
PASSED
tests/test_tshes_params_packet.py::TestTimeUtils::test_ceil_dtm PASSED

================= 3 passed in 0.07 seconds ===========================================================================
