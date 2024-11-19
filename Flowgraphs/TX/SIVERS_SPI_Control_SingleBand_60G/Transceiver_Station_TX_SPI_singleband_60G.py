#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Transceiver Station TX SPI Single Band 60G
# Author: Niklas Beckmann, Berk Acikgoez, Aleksandar Ichkov, Aron Schott
# Copyright: iNets - RWTH
# GNU Radio version: 3.10.6.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
import os
import sys
sys.path.append(os.environ.get('GRC_HIER_PATH', os.path.expanduser('~/.grc_gnuradio')))

from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import digital
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import iNETS_BeamManager
from gnuradio import iNETS_PHYHeader
from gnuradio import iNETS_PacketizedLink
from gnuradio import network
from phy_transceiver_tx_spi_singleband_60g import phy_transceiver_tx_spi_singleband_60g  # grc-generated hier_block
import Transceiver_Station_TX_SPI_singleband_60G_epy_block_0 as epy_block_0  # embedded python block
import gnuradio
import ieee802_11
import sip



class Transceiver_Station_TX_SPI_singleband_60G(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Transceiver Station TX SPI Single Band 60G", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Transceiver Station TX SPI Single Band 60G")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
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

        self.settings = Qt.QSettings("GNU Radio", "Transceiver_Station_TX_SPI_singleband_60G")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.usrp_tx_subdev_spec = usrp_tx_subdev_spec = "A:0"
        self.usrp_tx_address = usrp_tx_address = "addr=192.168.10.2"
        self.sweeping = sweeping = True
        self.sta_code = sta_code = 11
        self.sps = sps = 4
        self.scrambler_seed = scrambler_seed = 111
        self.samp_rate = samp_rate = 2000000
        self.rand_pad = rand_pad = 20
        self.partner_sta_code = partner_sta_code = 12
        self.max_mtu_size = max_mtu_size = 800
        self.init_tx_rf_gain = init_tx_rf_gain = 0x44
        self.init_tx_beam = init_tx_beam = 32
        self.init_rx_beam = init_rx_beam = 0
        self.header_format = header_format = iNETS_PHYHeader.phy_header().formatter()
        self.detector_threshold = detector_threshold = 60
        self.beam_id = beam_id = 11
        self.bb_freq_60 = bb_freq_60 = 100e6

        ##################################################
        # Blocks
        ##################################################

        # Create the options list
        self._sweeping_options = [False, True]
        # Create the labels list
        self._sweeping_labels = ['Fixed TX beam', 'Full TX beam sweep']
        # Create the combo box
        self._sweeping_tool_bar = Qt.QToolBar(self)
        self._sweeping_tool_bar.addWidget(Qt.QLabel("Choose Beam Sweeping Type" + ": "))
        self._sweeping_combo_box = Qt.QComboBox()
        self._sweeping_tool_bar.addWidget(self._sweeping_combo_box)
        for _label in self._sweeping_labels: self._sweeping_combo_box.addItem(_label)
        self._sweeping_callback = lambda i: Qt.QMetaObject.invokeMethod(self._sweeping_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._sweeping_options.index(i)))
        self._sweeping_callback(self.sweeping)
        self._sweeping_combo_box.currentIndexChanged.connect(
            lambda i: self.set_sweeping(self._sweeping_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._sweeping_tool_bar, 0, 0, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_time_sink_x_0 = qtgui.time_sink_c(
            1024, #size
            samp_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1.5, 1.5)

        self.qtgui_time_sink_x_0.set_y_label('Amplitude', "")

        self.qtgui_time_sink_x_0.enable_tags(True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_axis_labels(True)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        self.qtgui_time_sink_x_0.enable_stem_plot(False)


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


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qtgui_time_sink_x_0.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qtgui_time_sink_x_0.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_win, 4, 0, 2, 6)
        for r in range(4, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_number_sink_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_NONE,
            1,
            None # parent
        )
        self.qtgui_number_sink_0.set_update_time(0.10)
        self.qtgui_number_sink_0.set_title("TX codebook sweeping")

        labels = ["Beam ID", '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0.set_min(i, -1)
            self.qtgui_number_sink_0.set_max(i, 1)
            self.qtgui_number_sink_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0.set_label(i, labels[i])
            self.qtgui_number_sink_0.set_unit(i, units[i])
            self.qtgui_number_sink_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0.enable_autoscale(False)
        self._qtgui_number_sink_0_win = sip.wrapinstance(self.qtgui_number_sink_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_number_sink_0_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-1), 1)
        self.qtgui_const_sink_x_0.set_x_axis((-1.5), 1.5)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(True)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_const_sink_x_0_win, 0, 3, 4, 3)
        for r in range(0, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(3, 6):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.phy_transceiver_tx_spi_singleband_60g_0 = phy_transceiver_tx_spi_singleband_60g(
            baseband_derotation_volatility=0.8,
            bb_freq_60=bb_freq_60,
            detector_threshold=detector_threshold,
            init_beam=init_tx_beam,
            max_mtu_size=max_mtu_size,
            rand_pad=rand_pad,
            samp_rate=samp_rate,
            sps=sps,
            subdev_spec_TX=usrp_tx_subdev_spec,
            usrp_tx_address=usrp_tx_address,
        )
        self.network_socket_pdu_0 = network.socket_pdu('UDP_SERVER', 'localhost', '52001', 100, False)
        self.iNETS_PacketizedLink_stop_wait_arq_0 = iNETS_PacketizedLink.stop_wait_arq(False, 90e-3, 2, max_mtu_size, 0, scrambler_seed, init_tx_beam, init_rx_beam, init_tx_rf_gain, True, sta_code, partner_sta_code, '/home/inets/Workspace/GNURadio_logs/TX_USB/Stop_Wait_ARQ/')
        self.iNETS_BeamManager_beamsteering_protocol_0 = iNETS_BeamManager.beamsteering_protocol(2, "_iNETS", 0, sta_code, False, 15, True, 0.2, 0.2, 0.1, 0.28, 0.065, 0.1, 0.065, 1.5, 0.035, 0.2, 0.8, 1.2, '', '/home/inets/Workspace/GNURadio_logs/TX_USB/Beamsteering_Protocol_events_configs/', False, '/home/inets/Workspace/GNURadio_logs/TX_USB/Beamsteering_Protocol_persector/', 11, 1, 2.0, 1.0, 3.0, 1, init_tx_beam, 0.035, True)
        self.epy_block_0 = epy_block_0.blk()
        # Create the options list
        self._beam_id_options = [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13, 14, 14, 15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 20, 21, 21]
        # Create the labels list
        self._beam_id_labels = ['Omni Beam', 'Omni Beam', 'Beam 1', 'Beam 1', 'Beam 2', 'Beam 2', 'Beam 3', 'Beam 3', 'Beam 4', 'Beam 4', 'Beam 5', 'Beam 5', 'Beam 6', 'Beam 6', 'Beam 7', 'Beam 7', 'Beam 8', 'Beam 8', 'Beam 9', 'Beam 9', 'Beam 10', 'Beam 10', 'Beam 11', 'Beam 11', 'Beam 12', 'Beam 12', 'Beam 13', 'Beam 13', 'Beam 14', 'Beam 14', 'Beam 15', 'Beam 15', 'Beam 16', 'Beam 16', 'Beam 17', 'Beam 17', 'Beam 18', 'Beam 18', 'Beam 19', 'Beam 19', 'Beam 20', 'Beam 20', 'Beam 21', 'Beam 21']
        # Create the combo box
        self._beam_id_tool_bar = Qt.QToolBar(self)
        self._beam_id_tool_bar.addWidget(Qt.QLabel("Choose Fixed TX Beam" + ": "))
        self._beam_id_combo_box = Qt.QComboBox()
        self._beam_id_tool_bar.addWidget(self._beam_id_combo_box)
        for _label in self._beam_id_labels: self._beam_id_combo_box.addItem(_label)
        self._beam_id_callback = lambda i: Qt.QMetaObject.invokeMethod(self._beam_id_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._beam_id_options.index(i)))
        self._beam_id_callback(self.beam_id)
        self._beam_id_combo_box.currentIndexChanged.connect(
            lambda i: self.set_beam_id(self._beam_id_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._beam_id_tool_bar, 1, 0, 1, 2)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.iNETS_BeamManager_beamsteering_protocol_0, 'gui_out'), (self.epy_block_0, 'message_in'))
        self.msg_connect((self.iNETS_BeamManager_beamsteering_protocol_0, 'out'), (self.iNETS_PacketizedLink_stop_wait_arq_0, 'beamforming_protocol_in'))
        self.msg_connect((self.iNETS_PacketizedLink_stop_wait_arq_0, 'beamforming_protocol_out'), (self.iNETS_BeamManager_beamsteering_protocol_0, 'in'))
        self.msg_connect((self.iNETS_PacketizedLink_stop_wait_arq_0, 'udp_socket_out'), (self.network_socket_pdu_0, 'pdus'))
        self.msg_connect((self.iNETS_PacketizedLink_stop_wait_arq_0, 'phy_out'), (self.phy_transceiver_tx_spi_singleband_60g_0, 'TX PHY in'))
        self.msg_connect((self.network_socket_pdu_0, 'pdus'), (self.iNETS_PacketizedLink_stop_wait_arq_0, 'udp_socket_in'))
        self.connect((self.epy_block_0, 0), (self.qtgui_number_sink_0, 0))
        self.connect((self.phy_transceiver_tx_spi_singleband_60g_0, 1), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.phy_transceiver_tx_spi_singleband_60g_0, 0), (self.qtgui_time_sink_x_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "Transceiver_Station_TX_SPI_singleband_60G")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_usrp_tx_subdev_spec(self):
        return self.usrp_tx_subdev_spec

    def set_usrp_tx_subdev_spec(self, usrp_tx_subdev_spec):
        self.usrp_tx_subdev_spec = usrp_tx_subdev_spec
        self.phy_transceiver_tx_spi_singleband_60g_0.set_subdev_spec_TX(self.usrp_tx_subdev_spec)

    def get_usrp_tx_address(self):
        return self.usrp_tx_address

    def set_usrp_tx_address(self, usrp_tx_address):
        self.usrp_tx_address = usrp_tx_address
        self.phy_transceiver_tx_spi_singleband_60g_0.set_usrp_tx_address(self.usrp_tx_address)

    def get_sweeping(self):
        return self.sweeping

    def set_sweeping(self, sweeping):
        self.sweeping = sweeping
        self._sweeping_callback(self.sweeping)

    def get_sta_code(self):
        return self.sta_code

    def set_sta_code(self, sta_code):
        self.sta_code = sta_code

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.phy_transceiver_tx_spi_singleband_60g_0.set_sps(self.sps)

    def get_scrambler_seed(self):
        return self.scrambler_seed

    def set_scrambler_seed(self, scrambler_seed):
        self.scrambler_seed = scrambler_seed

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.phy_transceiver_tx_spi_singleband_60g_0.set_samp_rate(self.samp_rate)
        self.qtgui_time_sink_x_0.set_samp_rate(self.samp_rate)

    def get_rand_pad(self):
        return self.rand_pad

    def set_rand_pad(self, rand_pad):
        self.rand_pad = rand_pad
        self.phy_transceiver_tx_spi_singleband_60g_0.set_rand_pad(self.rand_pad)

    def get_partner_sta_code(self):
        return self.partner_sta_code

    def set_partner_sta_code(self, partner_sta_code):
        self.partner_sta_code = partner_sta_code

    def get_max_mtu_size(self):
        return self.max_mtu_size

    def set_max_mtu_size(self, max_mtu_size):
        self.max_mtu_size = max_mtu_size
        self.phy_transceiver_tx_spi_singleband_60g_0.set_max_mtu_size(self.max_mtu_size)

    def get_init_tx_rf_gain(self):
        return self.init_tx_rf_gain

    def set_init_tx_rf_gain(self, init_tx_rf_gain):
        self.init_tx_rf_gain = init_tx_rf_gain

    def get_init_tx_beam(self):
        return self.init_tx_beam

    def set_init_tx_beam(self, init_tx_beam):
        self.init_tx_beam = init_tx_beam
        self.phy_transceiver_tx_spi_singleband_60g_0.set_init_beam(self.init_tx_beam)

    def get_init_rx_beam(self):
        return self.init_rx_beam

    def set_init_rx_beam(self, init_rx_beam):
        self.init_rx_beam = init_rx_beam

    def get_header_format(self):
        return self.header_format

    def set_header_format(self, header_format):
        self.header_format = header_format

    def get_detector_threshold(self):
        return self.detector_threshold

    def set_detector_threshold(self, detector_threshold):
        self.detector_threshold = detector_threshold
        self.phy_transceiver_tx_spi_singleband_60g_0.set_detector_threshold(self.detector_threshold)

    def get_beam_id(self):
        return self.beam_id

    def set_beam_id(self, beam_id):
        self.beam_id = beam_id
        self._beam_id_callback(self.beam_id)

    def get_bb_freq_60(self):
        return self.bb_freq_60

    def set_bb_freq_60(self, bb_freq_60):
        self.bb_freq_60 = bb_freq_60
        self.phy_transceiver_tx_spi_singleband_60g_0.set_bb_freq_60(self.bb_freq_60)




def main(top_block_cls=Transceiver_Station_TX_SPI_singleband_60G, options=None):

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
