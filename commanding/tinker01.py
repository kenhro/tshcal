import numpy as np
import matplotlib.pyplot as plt
from fractions import Fraction
from operator import lt, le, eq, gt, ge


def zero_gt49p9(x):
    """return zero if x > 49.9; otherwise, return x"""
    if x > 49.9:
        return 0.0
    else:
        return x


def clamp(x, thresh=49.9, oper=gt, newval=0.0):
    """return newval if 'x is cmp thresh'; otherwise, return x """
    # need_newval = oper(x, thresh)
    # if need_newval:
    #     return newval
    # else:
    #     return x
    need_newval = oper(x, thresh)
    return newval if need_newval else x


def vectorize_zero_gt49p9(x):
    """return vectorized function [not fast, convenient; it's a for loop]"""
    return np.vectorize(zero_gt49p9)(x)


def my_filter(v, predicate=zero_gt49p9):
    """return list of filtered values (e.g. values > 49.9 become zero)"""
    return [predicate(x) for x in v]


def my_round(x, base=5):
    """return x rounded to nearest multiple of base"""
    # https://stackoverflow.com/questions/2272149/round-to-5-or-other-number-in-python
    return base * round(x/base)


def clamp_array(x, thresh=49.9, oper=gt, newval=0.0):
    return np.where(oper(x, thresh), newval, x)


# raise SystemExit
#
#
# old_values = [1.0, 2.0, 49.8, 49.9, 50.0, 50.1, 33, 34, 34.7, 34.8, 34.9, 35, 35.1, 36]
# for x in old_values:
#     print(x, end=" ")
#     print(clamp(x, oper=ge, thresh=49.9, newval=0.0))
# raise SystemExit
#
#
# olds = np.array(old_values)
# olds[olds > 49.9] = 0.0
# print(olds)
#
# print(my_filter(old_values))
# print(my_filter(olds))
#
# print([my_round(x, base=10) for x in old_values])
#
# nums = [1, 2, 3]
# dens = [4, 5, 6]
# zipped = zip(nums, dens)
# fracs = [Fraction(n, d) for n, d in zip(nums, dens)]
# print(fracs)
#

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
