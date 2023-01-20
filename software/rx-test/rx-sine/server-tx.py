#!/usr/bin/python3

# simple_pub.py
import zmq
import time
from datetime import datetime, timezone
from gnuradio import uhd #"serial=31DEAD2"
from gnuradio import analog
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import uhd
import time
import traceback



class test_1_to_2(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate_rx = samp_rate_rx = 100e3
        self.samp_rate = samp_rate = 1e3
        self.gain_rx = gain_rx = 0.7
        self.fc = fc = 400e6
        self.f_tx = f_tx = 1e3

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_sink_0_0 = uhd.usrp_sink(
            ",".join(("serial=31DEAD2", '')),
            uhd.stream_args(
                cpu_format="fc32",
                args='',
                channels=list(range(0,1)),
            ),
            "",
        )
        self.uhd_usrp_sink_0_0.set_clock_source('external', 0)
        self.uhd_usrp_sink_0_0.set_time_source('external', 0)
        self.uhd_usrp_sink_0_0.set_samp_rate(samp_rate)
        self.uhd_usrp_sink_0_0.set_time_now(uhd.time_spec(time.time()), uhd.ALL_MBOARDS)

        self.uhd_usrp_sink_0_0.set_center_freq(fc+f_tx, 0)
        self.uhd_usrp_sink_0_0.set_antenna("TX/RX", 0)
        self.uhd_usrp_sink_0_0.set_normalized_gain(0.5, 0)
        self.analog_const_source_x_0 = analog.sig_source_c(0, analog.GR_CONST_WAVE, 0, 0, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_const_source_x_0, 0), (self.uhd_usrp_sink_0_0, 0))


    def get_samp_rate_rx(self):
        return self.samp_rate_rx

    def set_samp_rate_rx(self, samp_rate_rx):
        self.samp_rate_rx = samp_rate_rx

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_sink_0_0.set_samp_rate(self.samp_rate)

    def get_gain_rx(self):
        return self.gain_rx

    def set_gain_rx(self, gain_rx):
        self.gain_rx = gain_rx

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        self.fc = fc
        self.uhd_usrp_sink_0_0.set_center_freq(self.fc+self.f_tx, 0)

    def get_f_tx(self):
        return self.f_tx

    def set_f_tx(self, f_tx):
        self.f_tx = f_tx
        self.uhd_usrp_sink_0_0.set_center_freq(self.fc+self.f_tx, 0)





host = "*"
port = "5557"

# Creates a socket instance
context = zmq.Context()


start_socket = context.socket(zmq.PUB)
# Binds the socket to a predefined port on localhost
start_socket.bind("tcp://{}:{}".format(host, port))


hello_socket = context.socket(zmq.REP)
hello_socket.bind("tcp://*:5555")


def main(top_block_cls=test_1_to_2, options=None):
    tb = top_block_cls()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.start()

    while(True):
        message = hello_socket.recv()
        print(f"Node #{message.decode()} is ready")
        hello_socket.send_string("OK")

        message = hello_socket.recv()
        print(f"Node #{message.decode()} is ready")
        hello_socket.send_string("OK")


        # start_ms = datetime.now(timezone.utc).timestamp()
        # print(f"Waiting 30 seconds before starting the SYNC")

        # while(start_ms + 5*1000 > datetime.now(timezone.utc).timestamp()):
        #     try:
        #         message = hello_socket.recv(flags=zmq.NOBLOCK)
        #         print(f"Node #{message.decode()} is ready")
        #         hello_socket.send_string("OK")
        #     except zmq.ZMQError as e:
        #         if e.errno == zmq.EAGAIN:
        #             pass # no message was ready (yet!)
        #         else:
        #             traceback.print_exc()

        time.sleep(2)


        # Sends a string message
        start_socket.send_string("SYNC")
        print("SYNC")

    try:
        input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()


if __name__ == '__main__':
    main()