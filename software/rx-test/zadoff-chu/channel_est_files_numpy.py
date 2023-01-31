import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate, correlation_lags
from os.path import join as pjoin
import os


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


zc_fft = generate()
zc_time = None


files = ["usrp_samples_31E2BD7_0.dat","usrp_samples_31E2BD7_1.dat","usrp_samples_31E2C39_0.dat","usrp_samples_31E2C39_1.dat"]
dirname = os.path.dirname(__file__)

IQ_matrix = []
for i in range(4):
    samples = np.fromfile(pjoin(dirname,"RX",files[i]), dtype=dt)
    IQ_matrix.append(samples['i']+1j*samples['q'])

IQ_matrix = np.asarray(IQ_matrix)
# given that the have the same index

iq_samples = IQ_matrix[0,:]
zc_time = np.zeros_like(iq_samples)
zc_time[:len(zc_fft)] = np.fft.ifft(zc_fft)
xcorr = correlate(iq_samples, np.fft.ifft(zc_fft))

xcorr_norm = np.abs(xcorr)/np.max(np.abs(xcorr))
peaks_idx = np.argwhere(xcorr_norm>0.8)
argmax = peaks_idx[0]
print(argmax)

last_peak = peaks_idx[-1]
num_peaks = len(peaks_idx)

# check if last peak is a full peak
if last_peak + 353 > IQ_matrix.shape[-1]:
    # remove last peak
    num_peaks -= 1
    peaks_idx = peaks_idx[:-1]

IQ_pruned = np.zeros((4, num_peaks, 353),dtype=IQ_matrix.dtype)
for i,p_idx in enumerate(peaks_idx):
    p_idx = int(p_idx)
    IQ_pruned[:,i,:] = IQ_matrix[:, p_idx:p_idx+353]

IQ_matrix_fft = np.fft.fft(IQ_pruned, 353, axis=-1)

H_matrix_fft = IQ_matrix_fft / zc_fft


from mpl_toolkits.mplot3d import axes3d

im = plt.imshow(10*np.log10(np.abs(H_matrix_fft[0,:,:])), cmap='hot', aspect='auto')
plt.colorbar(im)
plt.show()


im = plt.imshow(np.angle(H_matrix_fft[0,:,:]), cmap='hot', aspect='auto')
plt.colorbar(im)
plt.show()



fig, axs = plt.subplots(4, sharex=True)
for i in range(4):
    samples = np.fromfile(pjoin(dirname,"RX",files[i]), dtype=dt)
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

