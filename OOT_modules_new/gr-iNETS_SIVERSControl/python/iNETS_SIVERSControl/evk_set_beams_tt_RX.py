#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 iNETS RWTH
# updated by Niklas Beckmann, Berk Acikgoez
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr
import threading
import pmt

# libraries from EVK drivers
import memory
import register

class evk_set_beams_tt_RX(gr.basic_block):
    """
    This block performs the following operations:
    - For each beam index in beam_indices, pass samples for a duration of time_per_angle. 
    Then, switch to the next beam_index
    
    Make sure to place a stream_to_tagged_stream block immediately after this block to get back 
    the packet_length tags that we do not handle in this block
    
    As long as either one of cruijff or eder has been imported at the evk_init block, 
    there is no need to import them here as well.
    Therefore, this block can be used for either cruijff or eder without any modifications.
    The instances of register and memory will automatically be imported 
    from whichever of cruijff or eder is used for that runtime 
    (i.e. which one is before the other in the PYTHONPATH).
    Furthermore, this block can also be used for controlling the EVK over SPI 
    in combination with the EVK Standalone SPI Manager block.
    For control over SPI, choose Use SPI as Yes from the block diagram 
    and connect the ports to the aforementioned SPI Manager block.
    """
    def __init__(self, evkplatform_type, time_per_angle, beam_indices, sps, use_spi):
        gr.basic_block.__init__(self,
            name="evk_set_beams_tt_RX",
            in_sig=[numpy.complex64],
            out_sig=[numpy.complex64])
               
        # Set message port registers
        self.message_port_register_in(pmt.intern("time_per_angle_message"))
        self.message_port_register_in(pmt.intern("beam_indices_message"))

        # Set incoming message callback function
        self.set_msg_handler(pmt.intern('time_per_angle_message'), self.handle_time_per_angle_message)
        self.set_msg_handler(pmt.intern('beam_indices_message'), self.handle_beam_indices_message)

        self.valid_samples = True
        self.timer = 0

        self.evkplatform_type = evkplatform_type  # for cruijff

        self.time_per_angle = time_per_angle
        self.beam_indices = beam_indices.split(',')
        self.beam_indices = [int(i) for i in self.beam_indices]
        self.beamID = 100
        self.cur_beam_idx = 0
        self.cur_beam_idx_changed = True  # used to trigger a tag each time the angle is changed
        self.rx_bfrf_gain = 0x11
        self.sps = sps  # samples per symbol
        self.run_no = 0

        self.beam_id_key = "rx_beam_id"
        
        self.use_spi = use_spi
        self.spi_readback_curr_beam = 0
        if self.use_spi:
            self.message_port_register_in(pmt.intern("spi_manager_in"))
            self.message_port_register_out(pmt.intern("spi_manager_out"))
            self.set_msg_handler(pmt.intern("spi_manager_in"), self.handle_spi_manager_in)
        else:
            # Instantiate cruijff/eder object
            self.regs = register.Register(self.evkplatform_type)
            self.mems = memory.Memory(self.evkplatform_type)
            print(evkplatform_type)

    def general_work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]

        ninput_items = len(input_items[0])

        # Reset consumed_items back to zero every time the work function is called
        consumed_items = 0
        counter = 0

        if self.valid_samples:
            consumed_items = min(len(in0), len(out0))
            for i in range(0, consumed_items):
                out0[i] = in0[i]
                if self.cur_beam_idx_changed:
                    for s in range(1,self.sps):
                        try:
                            self.add_item_tag(0, self.nitems_written(0) + i + s, pmt.intern(self.beam_id_key),
                                                pmt.from_long(self.beam_indices[self.cur_beam_idx]))
                        except:
                            pass
                    self.cur_beam_idx_changed = False

        else:
            consumed_items = min(len(in0), len(out0))
            for i in range(0, consumed_items):
                out0[i] = 0

        if self.timer == 0:
            self.timer = threading.Timer(1.0, self.set_beam_angle)
            self.timer.start()
        
        self.consume_each(consumed_items)
        return consumed_items  # number of output items

    def handle_time_per_angle_message(self, msg):
        time_per_angle = pmt.to_float(msg)
        self.time_per_angle = time_per_angle
        #print('Time Per Angle UPDATE: ', self.time_per_angle)

    def handle_beam_indices_message(self, msg):
        beamID = pmt.to_float(msg)
        self.beamID = beamID
        #print('BEAM ID UPDATE: ', self.beamID)
        
    def handle_spi_manager_in(self, msg):
        spi_rb_curr_beam = pmt.to_long(msg)
        self.spi_readback_curr_beam = spi_rb_curr_beam

    def set_beam_angle(self):
        """
        Iterate through all beams and wait time_per_angle between iteration steps.
        """
        if self.beamID == 100:
            # increase idx (make it wrap around to 0 if all the indices have already been iterated over)
            self.cur_beam_idx = (self.cur_beam_idx + 1) % len(self.beam_indices)
            self.cur_beam_idx_changed = True
            # set beam angle
            print('[EVK Set Beams and TT RX] Set beamsteering index to ' + str(self.beam_indices[self.cur_beam_idx]))
            if self.use_spi:
                print('[EVK Set Beams and TT RX] Sending message to SPI manager')
                self.message_port_pub(pmt.intern("spi_manager_out"), pmt.from_long(self.beam_indices[self.cur_beam_idx]))
            else:
                self.mems.awv.wr('bf_rx_awv_ptr', 0x80 | self.beam_indices[self.cur_beam_idx])
            
            if self.cur_beam_idx == len(self.beam_indices)-1:
                # we reached the end of the beam angles that we want to measure
                # increment run_no to indicate that a new run is being started
                self.run_no += 1
            
            # wait time_per_angle before continuing
            self.timer = threading.Timer(self.time_per_angle, self.set_beam_angle)
            self.timer.start()
            return
        else:
            # fixed idx
            self.cur_beam_idx = int(self.beamID)
            self.cur_beam_idx_changed = True
            # set beam angle
            print('[EVK Set Beams and TT RX] Set beamsteering index to ' + str(self.beam_indices[self.cur_beam_idx]))
            if self.use_spi:
                print('[EVK Set Beams and TT RX] Sending message to SPI manager')
                self.message_port_pub(pmt.intern("spi_manager_out"), pmt.from_long(self.beam_indices[self.cur_beam_idx]))
            else:
                self.mems.awv.wr('bf_rx_awv_ptr', 0x80 | self.beam_indices[self.cur_beam_idx])
                
            # wait time_per_angle before continuing
            self.timer = threading.Timer(self.time_per_angle, self.set_beam_angle)
            self.timer.start()
            return

    def get_list_from_string(self, input):
        #l = input.replace(" ", "")
        #l = l.replace("[", "")
        #l = l.replace("]", "")
        l = input.split(',')
        l = [float(i) for i in l]
        l.sort()
        return l

