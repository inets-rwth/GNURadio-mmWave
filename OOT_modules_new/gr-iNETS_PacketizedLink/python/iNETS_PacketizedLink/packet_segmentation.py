#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 iNETS RWTH - Florian Wischeler
# updated by Niklas Beckmann
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
import string
import pmt
from gnuradio import gr
from gnuradio import digital

class packet_segmentation(gr.basic_block):
    """
    docstring for block packet_segmentation
    """
    def __init__(self, max_mtu_size):
        gr.basic_block.__init__(self,
            name="packet_segmentation",
            in_sig=[],
            out_sig=[])
        self.message_port_register_in(pmt.intern('in'))
        self.message_port_register_out(pmt.intern('out'))
        self.set_msg_handler(pmt.intern('in'), self.message_handler) #Trigger callback function when new packet arrives
        #Max MTU size in bytes the PHY is able to handle
        self.max_mtu_size = max_mtu_size
        
    def message_handler(self, msg_pmt): #callback function definition
        meta = pmt.to_python(pmt.car(msg_pmt))
        msg = pmt.cdr(msg_pmt)
        if not pmt.is_u8vector(msg): #Check if incoming data is a packet (byte vector)
            print("ERROR wrong pmt format")
            return

        msg_str = "".join([chr(x) for x in pmt.u8vector_elements(msg)]) #convert byte vector into string

        num_mtus = (len(msg_str) // self.max_mtu_size) #Calculate in how many segments (MTUs) of size max_mtu_size the arrived packet has to be split
        if len(msg_str) % self.max_mtu_size != 0: #Incoming data does not fit in full MTUs. We have to add another MTU which is not filled completely.
            num_mtus = num_mtus + 1
        
        # Segementation variables
        mtu_index_start = 0
        mtu_index_end = 0
        last = False
        seg = False
        seg_index = 0
    
        if num_mtus > 1: #Check whether data has to be segmented
            seg = True;
      
        for i in range(num_mtus):
            #Calculate indices of segments
            if (len(msg_str) - mtu_index_start) > self.max_mtu_size:
                mtu_index_end = mtu_index_start + self.max_mtu_size
            else: #last segment
                mtu_index_end = len(msg_str)
                last = True

        segment_str = msg_str[mtu_index_start:mtu_index_end] #Create string for segment
    
        packet = self.build_packet(segment_str, seg, last, i) #Create packet out of segement
      
        mtu_index_start += self.max_mtu_size

        # Create an empty PMT u8 vector (contains only spaces):
        send_pmt = pmt.make_u8vector(len(packet), ord(' '))
        # Copy packet to the u8vector
        for i in range(len(packet)):
            pmt.u8vector_set(send_pmt, i, ord(packet[i]))

        # Send message
        self.message_port_pub(pmt.intern('out'),
        pmt.cons(pmt.PMT_NIL, send_pmt))

    def build_packet(self, payload_str, seg, last_seg, seg_index): 
        hdr_str = ''
        #create segmentation identifier and put it in a header
        if not seg: # no segmentation required
            hdr_str = '\x00'
        else:
            seg_id = 0
        
        if not last_seg: #normal segmentation
            seg_id = 1 | seg_index << 2 
        else: #last segement
            seg_id = 3 | seg_index << 2
        hdr_str = chr(seg_id)
        #print('Generating seg ID: ', ord(hdr_str))
        packet_str = hdr_str + payload_str
        packet_str = digital.crc.gen_and_append_crc32(packet_str)
        packet_str = digital.packet_utils.whiten(packet_str, 0)
        #print('Building segment: hdr ID = %d payload len = %d total len = %d' % (ord(hdr_str), len(payload_str) , len(packet_str)))
        return packet_str

