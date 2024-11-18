#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 iNETS, RWTH Aachen University.
# Author: Florian Wischeler
# Modified by Berk Acikgoez, 2024.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
import pmt
from gnuradio import gr

import time
import threading
#import sys

# replace the path in the next line with the location of EVK02001 Cruijff driver
#sys.path.append('/home/inets/Workspace/evk02001/cruijff_evk-Release_20211123_1800/cruijff_a')

import cruijff

class evk02001_init_rx(gr.basic_block):
    """
    Set sleep amount to 0 if SPI is not being used.
    """
    def __init__(self, trx_frequency, initial_tx_beam_index, initial_rx_beam_index, initial_TX_RF_gain, initial_TX_BF_gain, initial_RX_RF_gain, initial_RX_vga_1_2_gain, unit_name, sleep_amount, evkplatform_type="MB1", version_num="20211123_1800", custom_beambook_suffix="", do_lo_leakage_cal=False, ref_freq = 122.88e6, ref_is_diff=True, rfm_type='BFM02003'):
        gr.basic_block.__init__(self,
            name="evk02001_init_rx",
            in_sig=None,
            out_sig=None)
                     
        # Parameter initialization with input values
        self.unit_name = unit_name
        self.evkplatform_type = evkplatform_type
        self.version_num = version_num
        self.trx_freq = trx_frequency
        self.custom_beambook_suffix = custom_beambook_suffix
        self.initial_tx_beam_index = initial_tx_beam_index
        self.initial_TX_RF_gain = initial_TX_RF_gain
        self.initial_TX_BF_gain = initial_TX_BF_gain
        self.initial_RX_RF_gain = initial_RX_RF_gain
        self.initial_RX_vga_1_2_gain = initial_RX_vga_1_2_gain
        self.current_RX_beam = initial_rx_beam_index
        self.thread_lock = threading.Lock()
        self.ref_freq = ref_freq
        self.ref_is_diff = ref_is_diff
        self.rfm_type = rfm_type
        # Message port register
        self.message_port_register_in(pmt.intern('MAC_control_message_in'))
        # Set incoming message callback function
        self.set_msg_handler(pmt.intern('MAC_control_message_in'), self.handle_mac_message)

        # Instantiate eder/cruijff object to control the antenna array transceiver
        self.CRUIJFF = cruijff.Cruijff(unit_name=self.unit_name, evkplatform_type=self.evkplatform_type, ref_cfg={'freq':self.ref_freq,'is_diff':self.ref_is_diff}, rfm_type=self.rfm_type)

        # TRX now in SX mode
        if hasattr(self.CRUIJFF, 'regs') and self.TRX_accessible(): #check whether regs are already initialized and if self.EDER.chip_present_status == True
            print('[EVK02001 Init RX]: Starting initialization now!!!')

            # TRX Setup with freq and beambook
            #print("[EVK02001 Init RX]: TX setup with custom beambook suffix: " + self.custom_beambook_suffix)
            # Reset antenna array
            self.CRUIJFF.reset()
            # TX LO leakage calibration (RX DC offset calibration already executed in setup)
            if do_lo_leakage_cal:
                self.CRUIJFF.run_tx_lo_leakage_cal(custom_beambook_suffix=self.custom_beambook_suffix)
            # TRX enable in toggle mode (RX normally enabled), mode is officially 'None'
            
            self.CRUIJFF.rx.init()	
            self.CRUIJFF.runRx(trx_frequency)
            print('current state'), self.CRUIJFF.state()
            #self.CRUIJFF.tx.bf.awv.bpp.set_selected_beambook(0)
            self.CRUIJFF.regs.wr('rx_gain_ctrl_bfrf', self.initial_RX_RF_gain)
            self.CRUIJFF.regs.wr('rx_gain_ctrl_bb1', 0x77)
            self.CRUIJFF.regs.wr('rx_gain_ctrl_bb2', 0x33)
            self.CRUIJFF.regs.wr('rx_gain_ctrl_bb3', 0xff)
            self.CRUIJFF.regs.wr('trx_rx_on', 0x1fffff)
            self.CRUIJFF.regs.wr('agc_int_ctrl', 0x0)
            self.CRUIJFF.regs.wr('agc_int_en_ctrl', 0x0)
            self.CRUIJFF.regs.wr('agc_ext_ctrl', 0x5)
            # Set initial beam according to customized beambook
            #self.CRUIJFF.tx.set_beam(self.initial_tx_beam_index)
            #self.CRUIJFF.rx.set_beam(self.current_RX_beam)
            # Set default TX and RX Gains
            #self.set_tx_default_gain()
            #self.set_rx_default_gain()
            print('AGC control: '), self.CRUIJFF.regs.rd('agc_int_en_ctrl')
            print('[EVK02001 Init RX]: Initialization of antenna array evaluation kit completed.')
            # Send message to MAC Protocol to indicate TXRX antenna array completion
            #self.message_port_pub(pmt.intern('init_msg_out'), pmt.intern('antenna_array_init_complete'))
            
            if sleep_amount > 0:           
                print("[EVK02001 Init RX]: You can now connect the SPI connector and use direct SPI control.")
                print("You have {} seconds to switch the (four upper-most) SW3 inputs.".format(sleep_amount))           
                self.CRUIJFF.evkplatform.drv.spioff()             
                time.sleep(sleep_amount)
                print("[EVK02001 Init RX]: Control over SPI enabled.")
            
        else:
            print('[EVK02001 Init RX]: ERROR: Init failed (Chip not present)')

    def handle_mac_message(self, msg_pmt):
        with self.thread_lock:
          # MAC control message handler
          # Currently only RX_beam_ID message to set RX_beam
            meta = pmt.to_python(pmt.car(msg_pmt))
            if pmt.is_dict(meta) == False:
                print("[EVK02001 Init RX]: ERROR: Recevied MAC message meta is not a PMT dictionary!")
            if pmt.dict_has_key(meta, pmt.string_to_symbol("rx_beam_id")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("rx_beam_id"), pmt.PMT_NIL)
                rx_beam = pmt.to_uint64(r)
            if not(rx_beam < 64 and rx_beam >= 0):
                print('[EVK02001 Init RX]: ERROR: Received RX beam ID is out of range!')
                rx_beam = self.current_RX_beam
          
            if current_RX_beam != rx_beam:
                self.current_RX_beam = rx_beam
                self.CRUIJFF.rx.set_beam(self.current_RX_beam)
    
    # Check if TRX is available/connected
    def TRX_accessible(self):
        if self.CRUIJFF is not None and hasattr(self.CRUIJFF, 'chip_present_status'):
            return True
        else:
            return False

    # Set default TX gain using register. Set both I and Q path
    def set_tx_default_gain(self):
        if self.CRUIJFF.chip_is_present():
            self.CRUIJFF.regs.wr('tx_bfrf_gain', self.initial_TX_RF_gain) # old: 0x3
            self.CRUIJFF.regs.wr('tx_bb_gain', 0x0) # old: 0x0
            self.CRUIJFF.regs.wr('tx_bb_iq_gain', self.initial_TX_BF_gain) # old: 0x00
            print("[EVK02001 Init RX]: TX default gains set")
        else:
            print("[EVK02001 Init RX]: ERROR: Cannot set TX default measurement gains, chip not present or mode not TX!")

    # Set default RX gain using register. Set both I and Q path
    def set_rx_default_gain(self):
        if self.CRUIJFF.chip_is_present():
            self.CRUIJFF.regs.wrrd('rx_bf_rf_gain', self.initial_RX_RF_gain) #0xee
            self.CRUIJFF.regs.wr('rx_bb_i_vga_1_2', self.initial_RX_vga_1_2_gain) #0x73
            self.CRUIJFF.regs.wr('rx_bb_q_vga_1_2', self.initial_RX_vga_1_2_gain)
            self.CRUIJFF.regs.wr('rx_bb_i_vga_1db', 0xe)
            self.CRUIJFF.regs.wr('rx_bb_q_vga_1db', 0xe)
            self.CRUIJFF.regs.wr('agc_en',0x00)
            print("[EVK02001 Init RX]: RX default gains set")
        else:
            print("[EVK02001 Init RX]: ERROR: Cannot set RX default measurement gains, chip not present or mode not TX!")
