import os


def create_folder(s):
    try:
        if not os.path.exists(s):
            os.makedirs(s)
    except OSError:
        print('Error: Creating directory. ' % s)
