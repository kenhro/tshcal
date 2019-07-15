import os


def get_basename_noext(f):
    """return basename of path, f, without extension"""
    return os.path.splitext(os.path.basename(f))[0]


def create_folder(s):
    try:
        if not os.path.exists(s):
            os.makedirs(s)
    except OSError:
        print('Error: Creating directory. ' % s)
