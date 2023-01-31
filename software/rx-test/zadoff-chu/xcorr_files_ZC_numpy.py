import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate


def generate(u=7, seq_length=353, q=0):

    """
    Generate a Zadoff-Chu (ZC) sequence.
    Parameters
    ----------
    u : int
        Root index of the the ZC sequence: u>0.
    seq_length : int
        Length of the sequence to be generated. Usually a prime number:
        u<seq_length, greatest-common-denominator(u,seq_length)=1.
    q : int
        Cyclic shift of the sequence (default 0).
    Returns
    -------
    zcseq : 1D ndarray of complex floats
        ZC sequence generated.
        
   To still put DC to 0, 
   we interleave the ZC sequence with zeros.
 
    """
    
    for el in [u,seq_length,q]:
        if not float(el).is_integer():
            raise ValueError('{} is not an integer'.format(el))
    if u<=0:
        raise ValueError('u is not stricly positive')
    if u>=seq_length:
        raise ValueError('u is not stricly smaller than seq_length')
        
    if np.gcd(u,seq_length)!=1:
        raise ValueError('the greatest common denominator of u and seq_length is not 1')
        

    cf = seq_length%2
    n = np.arange(seq_length)
    zcseq = np.exp( -1j * np.pi * u * n * (n+cf+2.0*q) / seq_length)
    
    return zcseq

dt = np.dtype([('i',np.float32), ('q',np.float32)])

fig, axs = plt.subplots(4, sharex=True)
zc_fft = generate()
zc_time = None


files = ["usrp_samples_31E2BD7_0.dat","usrp_samples_31E2BD7_1.dat","usrp_samples_31E2C39_0.dat","usrp_samples_31E2C39_1.dat"]

for i in range(4):


    samples = np.fromfile(files[i], dtype=dt)
    iq_samples = samples['i']+1j*samples['q']

    if zc_time is None:
        zc_time = np.zeros_like(iq_samples)
        zc_time[:len(zc_fft)] = np.fft.ifft(zc_fft)
    xcorr = correlate(iq_samples, zc_time)

    xcorr_norm = np.abs(xcorr)/np.max(np.abs(xcorr))


    axs[i].plot(xcorr_norm)
    argmax = np.argwhere(xcorr_norm>0.8)[0]
    print(argmax)
    print(xcorr_norm[argmax-1])
    print(xcorr_norm[argmax+1])
    axs[i].set_title(files[i])

plt.show()
