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

Path is

trajectories
1 start at +x rough home
2 move to -z rough home (pitch +80)
3 currently at -z
4 move to +y (yaw -90)
5 currently at +y rough home
6 move to -x rough home (pitch +170)
7 currently at -x rough home
8 move to -y (pitch -100) and yaw (-90)
9 currently at -y
10 move to +z yaw 0
11 currently at +z
12 move to +x (pitch 0)
