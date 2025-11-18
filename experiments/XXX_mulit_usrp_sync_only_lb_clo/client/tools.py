from scipy.signal import butter, sosfilt
from scipy import stats
import numpy as np


def circmean(arr, deg=True):

    arr = np.asarray(arr)
    if deg:
        arr = np.deg2rad(arr)

    _circmean = np.angle(np.sum(np.exp(1j * arr)))

    return np.rad2deg(_circmean) if deg else _circmean

from scipy.signal import butter, sosfilt
from scipy import stats
import numpy as np


def to_min_pi_plus_pi(angles, deg=True):

    angles = np.asarray(angles)

    thr = 180.0 if deg else np.pi / 2
    rotate = 360.0 if deg else 2 * np.pi

    # ensure positive
    idx = angles < 0.0
    angles[idx] = angles[idx] + rotate

    # ensure betwen -180 and 180 or -pi and pi
    idx = angles > thr
    angles[idx] = angles[idx] - rotate

    return angles


f0 = 1e3
cutoff = 100
fs = 250e3
lowcut = f0 - cutoff
highcut = f0 + cutoff


def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    sos = butter(order, [low, high], analog=False, btype="band", output="sos")
    return sos


def butter_bandpass_filter(data, lowcut, highcut, fs, order=5, sos=None):
    if sos is None:
        sos = butter_bandpass(lowcut, highcut, fs, order=order)
    y = sosfilt(sos, data)
    return y


def apply_bandpass(x: np.ndarray, fs=250e3):
    sos = butter_bandpass(lowcut, highcut, fs, order=9)

    y_re = butter_bandpass_filter(np.real(x), lowcut, highcut, fs, order=9, sos=sos)
    y_imag = butter_bandpass_filter(np.imag(x), lowcut, highcut, fs, order=9, sos=sos)

    return y_re + 1j * y_imag


def get_phases_and_apply_bandpass(x: np.ndarray, fs=250e3):
    sos = butter_bandpass(lowcut, highcut, fs, order=9)

    y_re = butter_bandpass_filter(np.real(x), lowcut, highcut, fs, order=9, sos=sos)
    y_imag = butter_bandpass_filter(np.imag(x), lowcut, highcut, fs, order=9, sos=sos)

    return np.angle(y_re + 1j * y_imag), 0  # legacy


def get_phases_and_remove_CFO(x, fs=250e3, remove_first_samples=True):

    sos = butter_bandpass(lowcut, highcut, fs, order=9)
    y_re = butter_bandpass_filter(np.real(x), lowcut, highcut, fs, order=9, sos=sos)
    y_imag = butter_bandpass_filter(np.imag(x), lowcut, highcut, fs, order=9, sos=sos)

    # return np.angle(y_re + 1j * y_imag)

    angle_unwrapped = np.unwrap(np.angle(y_re + 1j * y_imag))
    t = np.arange(0, len(y_re)) * (1 / fs)

    lin_regr = stats.linregress(t, angle_unwrapped)
    angles = angle_unwrapped - lin_regr.slope * t
    return angles[5000:] if remove_first_samples else angles
