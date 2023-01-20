# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Cross-correlator
# GNU Radio version: 3.10.1.1

from gnuradio import blocks
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal







class xcorr(gr.hier_block2):
    def __init__(self, fft_len=1024):
        gr.hier_block2.__init__(
            self, "Cross-correlator",
                gr.io_signature.makev(2, 2, [gr.sizeof_gr_complex*1, gr.sizeof_gr_complex*1]),
                gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
        )

        ##################################################
        # Parameters
        ##################################################
        self.fft_len = fft_len

        ##################################################
        # Blocks
        ##################################################
        self.fft_vxx_0_1 = fft.fft_vcc(fft_len, False, (), True, 1)
        self.fft_vxx_0_0_0 = fft.fft_vcc(fft_len, True, (), True, 1)
        self.fft_vxx_0_0 = fft.fft_vcc(fft_len, True, (), True, 1)
        self.blocks_vector_to_stream_0_0 = blocks.vector_to_stream(gr.sizeof_gr_complex*1, fft_len)
        self.blocks_stream_to_vector_0_0_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_len)
        self.blocks_stream_to_vector_0_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_len)
        self.blocks_multiply_const_xx_0 = blocks.multiply_const_cc(1.0/fft_len, 1)
        self.blocks_multiply_conjugate_cc_0 = blocks.multiply_conjugate_cc(fft_len)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_multiply_conjugate_cc_0, 0), (self.fft_vxx_0_1, 0))
        self.connect((self.blocks_multiply_const_xx_0, 0), (self, 0))
        self.connect((self.blocks_stream_to_vector_0_0, 0), (self.fft_vxx_0_0, 0))
        self.connect((self.blocks_stream_to_vector_0_0_0, 0), (self.fft_vxx_0_0_0, 0))
        self.connect((self.blocks_vector_to_stream_0_0, 0), (self.blocks_multiply_const_xx_0, 0))
        self.connect((self.fft_vxx_0_0, 0), (self.blocks_multiply_conjugate_cc_0, 0))
        self.connect((self.fft_vxx_0_0_0, 0), (self.blocks_multiply_conjugate_cc_0, 1))
        self.connect((self.fft_vxx_0_1, 0), (self.blocks_vector_to_stream_0_0, 0))
        self.connect((self, 0), (self.blocks_stream_to_vector_0_0, 0))
        self.connect((self, 1), (self.blocks_stream_to_vector_0_0_0, 0))


    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.blocks_multiply_const_xx_0.set_k(1.0/self.fft_len)

