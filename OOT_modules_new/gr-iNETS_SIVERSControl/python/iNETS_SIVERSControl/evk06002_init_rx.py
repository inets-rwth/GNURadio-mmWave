#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 iNETS, RWTH Aachen University.
# Author: Florian Wischeler, Berk Acikgoez.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
import pmt
from gnuradio import gr
import threading
import time
#import sys

# replace the path in the next line with the location of EVK06002 Eder driver
#sys.path.append("/home/inets/Workspace/evk06002_sw_release_20220406_1715/eder_evk-Release_20220406_1715/Eder_B")

import eder
#import ref
#import register
#import memory
#import rx

class evk06002_init_rx(gr.basic_block):
    """
    Set sleep amount to 0 if SPI is not being used.
    """
    def __init__(self, trx_frequency, initial_rx_beam_index, initial_TX_RF_gain, initial_RX_RF_gain, initial_RX_vga_1_2_gain, unit_name, sleep_amount, evkplatform_type="MB1", do_lo_leakage_cal=False, custom_beambook_suffix="", rfm_type='BFM06009'):
        gr.basic_block.__init__(self,
            name="evk06002_init_rx",
            in_sig=None,
            out_sig=None)
            
        # Parameter initialization with input values
        self.unit_name = unit_name
        self.evkplatform_type = evkplatform_type
        self.trx_freq = trx_frequency
        self.custom_beambook_suffix = custom_beambook_suffix
        self.initial_rx_beam_index = initial_rx_beam_index
        self.initial_TX_RF_gain = initial_TX_RF_gain
        self.initial_RX_RF_gain = initial_RX_RF_gain
        self.initial_RX_vga_1_2_gain = initial_RX_vga_1_2_gain
        self.sleep_amount = sleep_amount
        self.thread_lock = threading.Lock()
        self.rfm_type = rfm_type
        # Message port register
        self.message_port_register_in(pmt.intern('MAC_control_message_in'))
        # Set incoming message callback function
        self.set_msg_handler(pmt.intern('MAC_control_message_in'), self.handle_mac_message)
        
        # Instantiate eder object
        #self.regs = register.Register(evkplatform_type)
        #self.mems = memory.Memory(evkplatform_type)

        # Instantiate eder object to control the antenna array transceiver
        self.EDER = eder.Eder(unit_name=self.unit_name, evkplatform_type=self.evkplatform_type, rfm_type=self.rfm_type)

        # TRX now in SX mode
        if hasattr(self.EDER, 'regs') and self.TRX_accessible(): #check whether regs are already initialized and if self.EDER.chip_present_status == True
            print('[EVK06002 Init RX]: Starting initialization now!!!')

            # TRX Setup with freq and beambook
            #print("[EVK06002 Init RX]: TX setup with custom beambook suffix: " + self.custom_beambook_suffix)
            # Reset antenna array
            self.EDER.reset()
            # TX LO leakage calibration (RX DC offset calibration already executed in setup)
            if do_lo_leakage_cal:
                self.EDER.run_tx_lo_leakage_cal(custom_beambook_suffix=self.custom_beambook_suffix)
            # TRX enable in toggle mode (RX normally enabled), mode is officially 'None'
	        
            self.EDER.rx.init()	
            self.EDER.run_rx(trx_frequency)
            #self.EDER.rx.dco.run() # added because eder does not run DCO calibration automatically
            #print('current state', self.EDER.state())
            self.EDER.regs.wrrd('rx_gain_ctrl_bfrf', self.initial_RX_RF_gain)
            self.EDER.regs.wrrd('rx_gain_ctrl_bb1', 0x77)
            self.EDER.regs.wrrd('rx_gain_ctrl_bb2', 0x11)
            self.EDER.regs.wrrd('rx_gain_ctrl_bb3', 0x77)
            self.EDER.regs.wrrd('trx_rx_on', 0x1fffff)
            #self.EDER.regs.wr('agc_int_ctrl', 0x0)
            #self.EDER.regs.wr('agc_int_en_ctrl', 0x0)
            #self.EDER.regs.wr('agc_ext_ctrl', 0x5)
            #self.EDER.rx.set_beam(self.initial_rx_beam_index)
            # Set default TX and RX Gains
            #self.set_tx_default_gain()
            #self.set_rx_default_gain()
            print('AGC control: '), self.EDER.regs.rd('agc_int_en_ctrl')
            print('[EVK06002 Init RX]: Initialization of antenna array evaluation kit completed.')
            # Send message to MAC Protocol to indicate TXRX antenna array completion
            #self.message_port_pub(pmt.intern('init_msg_out'), pmt.intern('antenna_array_init_complete'))
            
            if sleep_amount > 0:
                print("[EVK06002 Init RX]: You can now connect the SPI connector and use direct SPI control.")
                print("You have {} seconds to switch the (four upper-most) SW3 inputs.".format(sleep_amount))
                self.EDER.evkplatform.drv.spioff()
                time.sleep(sleep_amount)
                print("[EVK06002 Init RX]: Control over SPI enabled.")
            
        else:
            print('[EVK06002 Init RX]: ERROR: Init failed (Chip not present)')

    def handle_mac_message(self, msg_pmt):
        with self.thread_lock:
          #MAC control message handler
          #Currently only RX_beam_ID message to set RX_beam
            meta = pmt.to_python(pmt.car(msg_pmt))
            if pmt.is_dict(meta) == False:
                print("[EVK06002 Init RX]: ERROR: Recevied MAC message meta is not a PMT dictionary!")
            if pmt.dict_has_key(meta, pmt.string_to_symbol("rx_beam_id")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("rx_beam_id"), pmt.PMT_NIL)
                rx_beam = pmt.to_uint64(r)
            if not(rx_beam < 64 and rx_beam >= 0):
                print('[EVK06002 Init RX]: ERROR: Received RX beam ID is out of range!')
                rx_beam = self.current_RX_beam
          
            if current_RX_beam != rx_beam:
                self.current_RX_beam = rx_beam
                self.EDER.rx.set_beam(self.current_RX_beam)
    
    # Check if TRX is available/connected
    def TRX_accessible(self):
        if self.EDER is not None and hasattr(self.EDER, 'chip_present_status'):
            return True
        else:
            return False

    # Set default TX gain using register. Set both I and Q path
    def set_tx_default_gain(self):
        if self.EDER.chip_is_present():
            self.EDER.regs.wr('tx_bfrf_gain', self.initial_TX_RF_gain) #old: 0x3
            self.EDER.regs.wr('tx_bb_gain', 0x0) #old: 0x0
            self.EDER.regs.wr('tx_bb_iq_gain', self.initial_TX_BF_gain) #old0x00
            print("[EVK06002 Init RX]: TX default gains set")
        else:
            print("[EVK06002 Init RX]: ERROR: Cannot set TX default measurement gains, chip not present or mode not TX!")

    # Set default RX gain using register. Set both I and Q path
    def set_rx_default_gain(self):
        if self.EDER.chip_is_present():
            self.EDER.regs.wrrd('rx_bf_rf_gain', self.initial_RX_RF_gain) #0xee
            self.EDER.regs.wr('rx_bb_i_vga_1_2', self.initial_RX_vga_1_2_gain) #0x73
            self.EDER.regs.wr('rx_bb_q_vga_1_2', self.initial_RX_vga_1_2_gain)
            self.EDER.regs.wr('rx_bb_i_vga_1db', 0xe)
            self.EDER.regs.wr('rx_bb_q_vga_1db', 0xe)
            #self.EDER.regs.set('rx_bb_en',0x40)
            self.EDER.regs.wr('agc_en',0x00)
            print("[EVK06002 Init RX]: RX default gains set")
        else:
            print("[EVK06002 Init RX]: ERROR: Cannot set RX default measurement gains, chip not present or mode not TX!")
