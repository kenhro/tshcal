# use rate_bits as index to get rate (sa/sec) and cutoff_freq (Hz)
TSH_RATES = [
        # rate,  cutoff
        (7.8125,   3.2),  # rate_bits = 0
        (15.625,   6.3),  # rate_bits = 1
        (31.25,   12.7),  # rate_bits = 2
        (62.5,    25.3),  # rate_bits = 3
        (125.0,   50.6),  # rate_bits = 4
        (250.0,  101.4),  # rate_bits = 5
        (500.0,  204.2),  # rate_bits = 6
        (1000.0, 408.5),  # rate_bits = 7
        (125.0,   23.5),  # rate_bits = 8
]

# use unit_bits as index to units
TSH_UNITS = [
        'counts',  # unit_bits = 0
        'volts',   # unit_bits = 1
        'g',       # unit_bits = 2
]

# use gain_bits as key to get gain value and input type
TSH_GAINS = {
# gain_bits  gain     input
        0:   (1.0,   'Ground'),
        1:   (2.5,   'Ground'),
        2:   (8.5,   'Ground'),
        3:   (34.0,  'Ground'),
        4:   (128.0, 'Ground'),
        8:   (1.0,   'Test'),
        9:   (2.5,   'Test'),
        10:  (8.5,   'Test'),
        11:  (34.0,  'Test'),
        12:  (128.0, 'Test'),
        16:  (1.0,   'Signal'),
        17:  (2.5,   'Signal'),
        18:  (8.5,   'Signal'),
        19:  (34.0,  'Signal'),
        20:  (128.0, 'Signal'),
        24:  (1.0,   'Vref'),
        25:  (1.0,   'Sensor test'),
        26:  (2.0,   'Sensor test'),
}
