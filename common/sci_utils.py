import numpy as np
from collections import deque


def is_outlier(points, thresh=3.5):
    """
    Returns a boolean array with True if points are outliers and False
    otherwise.

    Parameters:
    -----------
        points : An numobservations by numdimensions array of observations
        thresh : The modified z-score to use as a threshold. Observations with
            a modified z-score (based on the median absolute deviation) greater
            than this value will be classified as outliers.

    Returns:
    --------
        mask : A numobservations-length boolean array.

    References:
    ----------
        Boris Iglewicz and David Hoaglin (1993), "Volume 16: How to Detect and
        Handle Outliers", The ASQC Basic References in Quality Control:
        Statistical Techniques, Edward F. Mykytka, Ph.D., Editor.
    """
    if len(points.shape) == 1:
        points = points[:, None]
    median = np.median(points, axis=0)
    diff = np.sum((points - median)**2, axis=-1)
    diff = np.sqrt(diff)
    med_abs_deviation = np.median(diff)
    modified_z_score = 0.6745 * diff / med_abs_deviation
    return modified_z_score > thresh


def demo_masked_deque():

    vals = deque(maxlen=100)

    x = np.random.random(100)
    x = np.r_[x, -3, -10, 100]
    x[11:22] = 22
    # masked array copy of x with outliers replaced by None (like NaN for plotting)
    mx = np.ma.array(x, mask=is_outlier(x))

    vals.extend(mx)
    print(vals)


def demo_outlier_rejection():

    import matplotlib.pyplot as plt

    # variable of interest is x
    x = np.random.random(100)

    # append some outliers
    x = np.r_[x, -3, -10, 100]
    x[11:22] = 22

    # masked array copy of x with outliers replaced by None (like NaN for plotting)
    mx = np.ma.array(x, mask=is_outlier(x))

    # plot results
    fig, (ax1, ax2) = plt.subplots(nrows=2)

    ax1.plot(x)
    ax1.set_title('Original')

    ax2.plot(mx)
    ax2.set_title('Without Outliers')

    plt.show()


if __name__ == '__main__':
    # demo_masked_deque()
    demo_outlier_rejection()
