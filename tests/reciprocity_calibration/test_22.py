import zmq
import numpy as np
import sys
from io import BytesIO

import xarray as xr
import xrft


context = zmq.Context()
socket = context.socket(zmq.PULL)
#socket.RCVTIMEO = 20*1000  # in milliseconds
socket.connect("tcp://127.0.0.1:5555")

rct_default = socket.RCVTIMEO


phase_socket = context.socket(zmq.REP)
phase_socket.bind("tcp://*:5000")

while True:
    buff = BytesIO()
    print("Listening for IQ samples")
    socket.RCVTIMEO = rct_default
    while True:
        try:
            message = socket.recv()
        except zmq.error.Again as _e:
                break
        buff.write(message)
        print(".", end=" ")
        sys.stdout.flush()
        socket.RCVTIMEO = 1000

    print("Done RX'en")

    dt = np.dtype([('re', np.int16), ('im', np.int16)])

    buff.seek(0)
    a = np.frombuffer(buff.read(), dtype=dt)

    b = np.zeros(len(a), dtype=np.complex64)
    b[:].real = a['re']/(2**15)
    b[:].imag = a['im']/(2**15)

    sample_rate = int(250e3)
    dt = 1/sample_rate

    print(f"{len(b)/sample_rate:0.2f}s recorded")


    bins = 1024*2

    # remove 1 sample at the beginning and end
    b = b[sample_rate:-sample_rate]

    N = len(b)//bins



    time = np.arange(N*bins)*dt
    b = b[-N*bins:]

    da = xr.DataArray(b, dims=["samples"], coords={"time":("samples",time)})
    da = da.chunk(bins)

    da_fft = xrft.fft(da, dim='samples', shift=True, chunks_to_segments=True)

    mag_fft = np.abs(da_fft)

    bins = mag_fft.argmax(dim="freq_samples").to_numpy()

    x= np.angle(da_fft, deg=True)

    std = np.std(x[:, bins])
    avg = np.mean(x[:, bins])

    print(f"std: {std:0.2f}°")
    print(f"mean: {avg:0.2f}°")

    print("Listening for incoming messages.")
    msg = phase_socket.recv()
    print(f"returning {avg}° in radians")
    sys.stdout.flush()
    phase_socket.send_string(str(np.deg2rad(avg)))
