import numpy as np

num_samples = 1024

dt = np.dtype([('re', np.int16), ('im', np.int16)])

time_samples_int16 = np.ones(num_samples, dtype=dt)
time_samples_int16['re'] = 0.85*(2**15)
time_samples_int16['im'] = 0




time_samples_int16.tofile('sine.dat')
