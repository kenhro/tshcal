# FIXME need to fix TWO_RIG_AX_TO_MOVE here; empirically-derived, like we did with safe trajectories
# define rig_ax to be moved to achieve either min or max given that we are at designated rough home position
TWO_RIG_AX_TO_MOVE = {
# rough_home          ax1  min  max       ax2   min   max
        '+x':   [('pitch', 150, 210), ('pitch', 155,  205)],
        '-x':   [('pitch', 150, 210), ('pitch', 155,  205)],
        '+y':   [('pitch', 150, 210), ('pitch', 155,  205)],
        '-y':   [('pitch', 150, 210), ('pitch', 155,  205)],
        '+z':   [('pitch', 150, 210), ('pitch', 155,  205)],
        '-z':   [('pitch', 150, 210), ('pitch', 155,  205)],
}

# map axis letter to ESP axis (stage) number
ESP_AX = {'roll': 1, 'pitch': 2, 'yaw': 3}

# move sequence for safe trajectories -- minimal moves for rough home to rough home transitions
SAFE_TRAJ_MOVES = [
#  rough_home   ax1  pos1, ax2 pos2, etc.
        ('+x',  [(2,    0)]),
        ('-z',  [(2,   80)]),
        ('+y',  [(3,  -90)]),
        ('-x',  [(2,  170)]),
        ('-y',  [(2, -100), (3, -90)]),
        ('+z',  [(3,    0)]),
]
