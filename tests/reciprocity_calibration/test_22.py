import zmq
import numpy as np
import sys
from io import BytesIO



context = zmq.Context()
socket = context.socket(zmq.PULL)
#socket.RCVTIMEO = 20*1000  # in milliseconds
socket.connect("tcp://127.0.0.1:5555")

rct_default = socket.RCVTIMEO


phase_socket = context.socket(zmq.REP)
phase_socket.bind("tcp://*:5000")

arr_in = []
arr_out = []

first=True
i = 0

while True:
    try:
        i+=1
        buff = BytesIO()
        print(f"[{i}] ----------------------------------")
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

        # remove 1 sample at the beginning and end
        #b = b[sample_rate//100:-sample_rate//100]

        phase_rad = np.angle(np.mean(b))

        if first:
            arr_in.append(phase_rad)
        else:
            arr_out.append(phase_rad)

        first = not first

        # angles = np.angle(b)
        # phase_rad = np.mod(angles + 2 * np.pi, 2*np.pi)
        phase = np.rad2deg(phase_rad)

        # std = np.std(phase)
        # avg = np.mean(phase)

        # print(f"std: {std:0.2f}°")
        print(f"mean: {phase:0.2f}°")

        print("Listening for incoming messages.")
        msg = phase_socket.recv()
        sys.stdout.flush()
        phase_socket.send_string(str(phase_rad))
        print("----------------------------------")
        print("")
        print("")
        print("")
        print("")
    except KeyboardInterrupt:
        if len(arr_in) != len(arr_out):
            if len(arr_in) > len(arr_out):
                arr_in = arr_in[:-1]
            else:
                arr_out = arr_out[-1]
        x = np.zeros((2, len(arr_in)))
        x[0,:] = arr_in
        x[1,:] = arr_out
        np.save("out-phases.npy", x)
        sys.exit()

