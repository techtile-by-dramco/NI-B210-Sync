#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: xcorr files
# Author: techtile
# GNU Radio version: 3.10.1.1

from packaging.version import Version as StrictVersion

if __name__ == '__main__':
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print("Warning: failed to XInitThreads()")

import os
import sys
sys.path.append(os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio.filter import firdes
import sip
from gnuradio import blocks
import pmt
from gnuradio import gr
from gnuradio.fft import window
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from xcorr import xcorr  # grc-generated hier_block



from gnuradio import qtgui

class xcorr_files(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "xcorr files", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("xcorr files")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "xcorr_files")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except:
            pass

        ##################################################
        # Variables
        ##################################################
        self.seq_len = seq_len = 353
        self.samp_rate = samp_rate = 250e3
        self.fft_len = fft_len = seq_len*2

        ##################################################
        # Blocks
        ##################################################
        self.xcorr_0_1 = xcorr(
            fft_len=fft_len,
        )
        self.xcorr_0_0 = xcorr(
            fft_len=fft_len,
        )
        self.xcorr_0 = xcorr(
            fft_len=fft_len,
        )
        self.qtgui_time_sink_x_0_0_0_0_1 = qtgui.time_sink_f(
            seq_len, #size
            samp_rate, #samp_rate
            "USRP2", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0_0_0_1.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0_0_0_1.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0_0_0_0_1.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0_0_0_1.enable_tags(True)
        self.qtgui_time_sink_x_0_0_0_0_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0_0_0_0_1.enable_autoscale(True)
        self.qtgui_time_sink_x_0_0_0_0_1.enable_grid(False)
        self.qtgui_time_sink_x_0_0_0_0_1.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0_0_0_1.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0_0_0_1.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0_0_0_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0_0_0_1.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0_0_0_1.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0_0_0_1.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0_0_0_1.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0_0_0_1.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0_0_0_1.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_0_0_1_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0_0_0_1.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_0_0_0_1_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0_0_0_0_0 = qtgui.time_sink_f(
            seq_len, #size
            samp_rate, #samp_rate
            "USRP1 vs USRP2", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0_0_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0_0_0_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0_0_0_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0_0_0_0.enable_tags(True)
        self.qtgui_time_sink_x_0_0_0_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0_0_0_0_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0_0_0_0_0.enable_grid(False)
        self.qtgui_time_sink_x_0_0_0_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0_0_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0_0_0_0.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0_0_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0_0_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0_0_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0_0_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0_0_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0_0_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0_0_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_0_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0_0_0_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_0_0_0_0_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0_0_0_0 = qtgui.time_sink_f(
            seq_len, #size
            samp_rate, #samp_rate
            "USRP1", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0_0_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0_0_0.set_y_axis(-1, 1)

        self.qtgui_time_sink_x_0_0_0_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0_0_0_0.enable_tags(True)
        self.qtgui_time_sink_x_0_0_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0_0_0_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0_0_0_0.enable_grid(False)
        self.qtgui_time_sink_x_0_0_0_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0_0_0_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0_0_0_0.enable_stem_plot(False)


        labels = ['Signal 1', 'Signal 2', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_0_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0_0_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_0_0_0_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.blocks_file_source_0_0_0_0 = blocks.file_source(gr.sizeof_gr_complex*1, '/home/techtile/NI-B210-Sync/software/rx-test/rx-zc/usrp_samples_31E2C39_1.dat', False, 0, 0)
        self.blocks_file_source_0_0_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0_0 = blocks.file_source(gr.sizeof_gr_complex*1, '/home/techtile/NI-B210-Sync/software/rx-test/rx-zc/usrp_samples_31E2C39_0.dat', False, 0, 0)
        self.blocks_file_source_0_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0_0 = blocks.file_source(gr.sizeof_gr_complex*1, '/home/techtile/NI-B210-Sync/software/rx-test/rx-zc/usrp_samples_31E2BD7_1.dat', False, 0, 0)
        self.blocks_file_source_0_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, '/home/techtile/NI-B210-Sync/software/rx-test/rx-zc/usrp_samples_31E2BD7_0.dat', False, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_complex_to_mag_1_1 = blocks.complex_to_mag(1)
        self.blocks_complex_to_mag_1_0 = blocks.complex_to_mag(1)
        self.blocks_complex_to_mag_1 = blocks.complex_to_mag(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_1, 0), (self.qtgui_time_sink_x_0_0_0_0, 0))
        self.connect((self.blocks_complex_to_mag_1_0, 0), (self.qtgui_time_sink_x_0_0_0_0_0, 0))
        self.connect((self.blocks_complex_to_mag_1_1, 0), (self.qtgui_time_sink_x_0_0_0_0_1, 0))
        self.connect((self.blocks_file_source_0, 0), (self.xcorr_0, 0))
        self.connect((self.blocks_file_source_0_0, 0), (self.xcorr_0, 1))
        self.connect((self.blocks_file_source_0_0, 0), (self.xcorr_0_0, 1))
        self.connect((self.blocks_file_source_0_0_0, 0), (self.xcorr_0_0, 0))
        self.connect((self.blocks_file_source_0_0_0, 0), (self.xcorr_0_1, 0))
        self.connect((self.blocks_file_source_0_0_0_0, 0), (self.xcorr_0_1, 1))
        self.connect((self.xcorr_0, 0), (self.blocks_complex_to_mag_1, 0))
        self.connect((self.xcorr_0_0, 0), (self.blocks_complex_to_mag_1_0, 0))
        self.connect((self.xcorr_0_1, 0), (self.blocks_complex_to_mag_1_1, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "xcorr_files")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_seq_len(self):
        return self.seq_len

    def set_seq_len(self, seq_len):
        self.seq_len = seq_len
        self.set_fft_len(self.seq_len*2)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.qtgui_time_sink_x_0_0_0_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_0_0_0_0_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_0_0_0_0_1.set_samp_rate(self.samp_rate)

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.xcorr_0.set_fft_len(self.fft_len)
        self.xcorr_0_0.set_fft_len(self.fft_len)
        self.xcorr_0_1.set_fft_len(self.fft_len)




def main(top_block_cls=xcorr_files, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
