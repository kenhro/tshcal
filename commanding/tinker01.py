import numpy as np
import matplotlib.pyplot as plt
from fractions import Fraction
from operator import lt, le, eq, gt, ge


OLD_VALUES = [1.0, 2.0, 49.8, 49.9, 50.0, 50.1, 33, 34, 34.7, 34.8, 34.9, 35, 35.1, 36]  # note scope of this object


def zero_gt49p9(x):
    """return zero if x > 49.9; otherwise, return x
    Note: the input, x, is expected to be a scalar value (i.e. not an array)"""
    if x > 49.9:
        return 0.0
    else:
        return x


def clamp(x, thresh=49.9, oper=gt, newval=0.0):
    """return newval if operation 'x cmp thresh' is True; otherwise, return x
    Note: thie input, x, is expected to be a scalar value (i.e. not an array)
    """
    need_newval = oper(x, thresh)  # interpret RHS like 'x > thresh' (or maybe 'x <= thresh' depending on oper)
    # if need_newval:
    #     return newval
    # else:
    #     return x
    return newval if need_newval else x  # this is equivalent to the more verbose if/else lines above


def my_filter(v, predicate=zero_gt49p9):
    """return list of filtered values (e.g. values > 49.9 become zero)"""
    return [predicate(x) for x in v]


def my_round(x, base=5):
    """return x rounded to nearest multiple of base
    Note: the input, x, is expected to be a scalar value (i.e. not an array)"""
    return base * round(x/base)


def clamp_array(x, thresh=49.9, oper=gt, newval=0.0):
    """return array x with values that meet oper/thresh criteria replaced by newval"""
    return np.where(oper(x, thresh), newval, x)


def demo_round_scalars(olds):
    for v in olds:
        print('original = ', v, ', rounded = ', my_round(v, base=10))


def demo_round_array(old_arr):
    new_arr = np.around(old_arr, decimals=-1)
    print('original array:', old_arr)
    print('rounded array:', new_arr)


def demo_clamp_array_plot():
    x = np.linspace(0, 10, 500)
    y = 60 * np.sin(x)

    fig, ax = plt.subplots()

    # Using set_dashes() to modify dashing of an existing line
    line1, = ax.plot(x, y, label='sine')
    line1.set_dashes([2, 2, 10, 2])  # 2pt line, 2pt break, 10pt line, 2pt break

    # Using plot(..., dashes=...) to set the dashing when creating a line
    line2, = ax.plot(x, clamp_array(y, thresh=0), dashes=[6, 2], label='zeroed-values sine')

    ax.legend()
    plt.show()


def demo_fractions():
    nums = [1, 2, 3]
    dens = [4, 5, 6]
    zipped = zip(nums, dens)
    fracs = [Fraction(n, d) for n, d in zip(nums, dens)]
    print(fracs)


def demos():
    def print_dashed_line(n):
        print('-' * n)

    print('Demo round scalars...')
    demo_round_scalars(OLD_VALUES)
    print_dashed_line(66)

    print('Demo round array...')
    demo_round_array(np.array(OLD_VALUES))
    print_dashed_line(66)

    print('Demo fractions...')
    demo_fractions()
    print_dashed_line(44)

    print('Demo clamp array (see plot figure window)...')
    demo_clamp_array_plot()


if __name__ == '__main__':
    demos()
