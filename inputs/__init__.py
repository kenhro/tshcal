
# rough homes dictionary defines 6 approximate starting positions and accounts for the shim
HOMES = {
        # POS   R  P  Y
        '+x':  (0, 0, 0),
        '-x':  (1, 1, 1),
        '+y':  (2, 2, 2),
        '-y':  (3, 3, 3),
        '+z':  (4, 4, 4),
        '-z':  (5, 5, 5),
}


# TSH settling time (in seconds) -- amount of time allocated for accelerometer to "settle" after a move & before reading
TSH_SETTLE_SEC = 3

