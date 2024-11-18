#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 iNETS RWTH - Florian Wischeler
# updated by Niklas Beckmann and Berk Acikgoez
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy
from datetime import datetime
from time import mktime
import pmt
from gnuradio import gr

#import sys
# replace the path in the next line with the location of EVK02001 Cruijff driver
#sys.path.append('/home/inets/Workspace/evk02001/cruijff_evk-Release_20211123_1800/cruijff_a')
            
#import cruijff
import memory
import register

class evk02001_set_beams_TX_USB(gr.basic_block):
    """
    docstring for block evk02001_set_beams_TX_USB
    """
    def __init__(self, evkplatform_type, length_tag_name, beam_tag_name, initial_beam_index):
        gr.basic_block.__init__(self,
            name="evk02001_set_beams_TX_USB",
            in_sig=[numpy.complex64],
            out_sig=[numpy.complex64])

        # Tag Propagation Policy
        self.set_tag_propagation_policy(gr.TPP_DONT) # Let no tags pass

        # Parameter initialization with input values
        self.evkplatform_type = evkplatform_type  # for cruijff
        self.length_tag_name = length_tag_name
        self.beam_tag_name = beam_tag_name
        self.packet_length = 0
        self.beam_id = initial_beam_index
        self.initial_beam_index = initial_beam_index
        self.TX_RF_gain = 0x11
        self.packet_arrived = False
        self.burst_transmission_complete = True
        self.number_of_samples_of_burst_left = 0
        self.all_consumed_items = 0

        # Instantiate cruijff object
        self.regs = register.Register(evkplatform_type)
        self.mems = memory.Memory(evkplatform_type)
        print('EVK platform type:' + evkplatform_type)

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]
        
        ninput_items = len(input_items[0])

        # Reset consumed_items back to zero every time the work function is called
        consumed_items = 0
        # Reset other variables
        self.beam_id = self.initial_beam_index
        self.TX_RF_gain = 0x11

        # Collect tags (Tags should be at the beginning of the packet. However, during the call of work only parts of a packet might be processed (ninput_items != packet_len).
        # Therefore, tags will not be detected in everay call of work())
        samp0_count = self.nitems_read(0)
        tags = self.get_tags_in_range(0, samp0_count, samp0_count + ninput_items)
        if len(tags) > 0:
            for tag in tags:
                #tx_time tag found
                if pmt.equal(tag.key, pmt.intern(self.length_tag_name)):
                    #print('[EVK02001 Set Beams TX USB] Length tag found')
                    if tag.offset != samp0_count: #Actually this can not happen, but to be sure we check here again that the tag is at the beginning of the burst
                        #print('[EVK02001 Set Beams TX USB] Error: length_tag not at the beginning of the burst!')
                        break
                    self.packet_length = pmt.to_long(tag.value)
                    #print("[EVK02001 Set Beams TX USB] Packet length:", self.packet_length)
                    if self.burst_transmission_complete == True:
                        self.number_of_samples_of_burst_left = self.packet_length
                        self.packet_arrived = True
                #beam tag found
                elif pmt.equal(tag.key, pmt.intern(self.beam_tag_name)):
                    #print('[EVK02001 Set Beams TX USB] Beam tag found')
                    if tag.offset != samp0_count: #Actually this can not happen, but to be sure we check here again that the tag is at the beginning of the burst
                        print('[EVK02001 Set Beams TX USB] Error: beam_id tag not at the beginning of the burst!')
                        break
                    self.beam_id = pmt.to_long(tag.value)
                    #print("[EVK02001 Set Beams TX USB] beam ID ", self.beam_id)
                    if self.beam_id > 63 or self.beam_id < 0:
                        print('[EVK02001 Set Beams TX USB] Error: Beam ID should be between 0 and 63. Setting beam ID to 0.')
                        self.beam_id = 0
                #RF gain tag found
                elif pmt.equal(tag.key, pmt.intern("tx_RF_gain")):
                    #print("[EVK02001 Set Beams TX USB] RF gain tag found")
                    if tag.offset != samp0_count: #Actually this can not happen, but to be sure we check here again that the tag is at the beginning of the burst
                        print('[EVK02001 Set Beams TX USB] Error: RF gain tag not at the beginning of the burst!')
                        break
                    self.TX_RF_gain = pmt.to_long(tag.value)
                    #print("[EVK02001 Set Beams TX USB] TX RF Gain ", self.TX_RF_gain)
                    if self.TX_RF_gain > 0xFF or self.TX_RF_gain < 0x00:
                        print('[EVK02001 Set Beams TX USB] Error: TX RF gain tag should be between 0x00 and 0xFF. Setting RF gain to 0x00.')
                        self.TX_RF_gain = 0x00
                #else: ignore other tags
        
        # Arrived packet can be processed since it is valid
        if self.number_of_samples_of_burst_left > 0 and self.packet_arrived == True:
            self.burst_transmission_complete = False
            # Packet is ready to be sent since indiciated tx_time has been reached
            # Also check whether antenna array is still transmitting
            print('[EVK02001 Set Beams TX USB] Current beam id = ' + str(self.beam_id))
            # Set main TX beam direction
            self.mems.awv.wr('bf_tx_awv_ptr', 0x80 | self.beam_id)
            # Set TX RF gain
            #self.regs.wr('tx_bfrf_gain', self.TX_RF_gain)
            print("TX_RF_gain: " + str(self.regs.rd('tx_bfrf_gain')))
            # Set / Update new tx_time tag
            # Send only once at the beginning when TX first was enabled
            updated_time = datetime.now()
            updated_time_full_seconds = mktime(updated_time.timetuple())
            updated_time_frac_seconds = float(updated_time.microsecond / 1000000.0)
            self.add_item_tag(0, self.nitems_written(0), pmt.intern("tx_time"), pmt.make_tuple(pmt.from_long(int(updated_time_full_seconds)), pmt.from_double(updated_time_frac_seconds + 0.027))) #0.015
            self.add_item_tag(0, self.nitems_written(0), pmt.intern(self.length_tag_name), pmt.from_long(self.packet_length))

            if self.number_of_samples_of_burst_left >= ninput_items:
                consumed_items = ninput_items
            else:
                consumed_items = self.number_of_samples_of_burst_left

            #Due to forecast manipulation and scheduler problems, ensure that consumed input items fit in output
            consumed_items = min(consumed_items, len(output_items[0]))
            self.number_of_samples_of_burst_left -= consumed_items
            if self.number_of_samples_of_burst_left < 0:
                print('[EVK02001 Set Beams TX USB] ERROR: Number of samples left negative!')
            # Output
            for i in range(consumed_items):
                out0[i] = in0[i]
            
        self.consume_each(consumed_items)
        self.all_consumed_items += consumed_items
        return consumed_items

