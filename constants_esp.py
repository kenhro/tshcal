# FIXME need to verify TWO_RIG_AX_TO_MOVE appropriate; empirically-derived, like we did with safe trajectories
# define rig_ax to be moved to achieve either min or max given that we are at designated rough home position
TWO_RIG_AX_TO_MOVE = {
# rough_home          ax1  min  max       ax2   min   max
        '+x':   [('pitch', 150, 210), ('which',   0,   20)],
        '-x':   [('which',   0,   0), ('which',   0,    0)],
        '+y':   [('which',   0,   0), ('which',   0,    0)],
        '-y':   [('which',   0,   0), ('which',   0,    0)],
        '+z':   [('which',   0,   0), ('which',   0,    0)],
        '-z':   [('which',   0,   0), ('which',   0,    0)],
}

ESP_AX = {'x': 1, 'y': 2, 'z': 3}  # map axis letter to ESP axis (stage) number
