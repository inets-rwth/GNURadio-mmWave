#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 iNETS RWTH - Florian Wischeler
# updated by Niklas Beckmann, Berk Acikgoez
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy
from gnuradio import gr
import string
import time
import datetime
import csv
import queue
import pmt
import threading
import os

# /////////////////////////////////////////////////////////////////////////////
#                   Simple MAC w/ ARQ
# /////////////////////////////////////////////////////////////////////////////

class stop_wait_arq(gr.basic_block):
    """
    docstring for block stop_wait_arq
    """
    # State identifiers
    STATE_WAIT_FOR_ACK = 0
    STATE_IDLE = 1
    
    # Packet type identifiers
    PACKET_TYPE_DATA = 0
    PACKET_TYPE_ACK = 1
    PACKET_TYPE_BEAMSTEERING_MESSAGE = 2

    # Message type identifiers
    MAC_SET_MESSAGE = 0 # Message to set parameters inside MAC protocol
    BEAMSTEERING_PROTOCOL_MESSAGE = 1 # Message to transmit via PHY to responder station
    
    def __init__(self, use_ack, ack_timeout, max_retries, max_mtu_size, tx_mcs, tx_scrambler_seed, initial_tx_beam_index, initial_rx_beam_index, initial_TX_RF_gain, send_only_when_trained, station_code, partner_station_code, conf_parent_dir):
        gr.basic_block.__init__(self,
            name="stop_wait_arq",
            in_sig=[], #numpy.complex64
            out_sig=[])
    
        # Set message port registers
        self.message_port_register_in(pmt.intern('udp_socket_in'))
        self.message_port_register_in(pmt.intern('beamforming_protocol_in'))
        self.message_port_register_in(pmt.intern('phy_in'))
        self.message_port_register_in(pmt.intern('snr_in'))
        self.message_port_register_out(pmt.intern('udp_socket_out'))
        self.message_port_register_out(pmt.intern('phy_out'))
        self.message_port_register_out(pmt.intern('beamforming_protocol_out'))
        self.message_port_register_out(pmt.intern('antenna_array_control_out'))
        self.message_port_register_out(pmt.intern('rx_phy_logger_out'))

        # Set incoming message callback functions
        self.set_msg_handler(pmt.intern('phy_in'), self.handle_phy_message)
        self.set_msg_handler(pmt.intern('udp_socket_in'), self.handle_udp_message)
        self.set_msg_handler(pmt.intern('beamforming_protocol_in'), self.handle_beamforming_protocol_message)
        self.set_msg_handler(pmt.intern('snr_in'), self.handle_snr_message)

        # Initialize variables
        self.udp_queue = queue.Queue()
        self.beamsteering_protocol_queue = queue.Queue()
        self.state = self.STATE_IDLE
        self.last_tx_time = 0
        self.last_tx_packet = 0
        self.ack_timeout = ack_timeout
        self.retries = 0
        self.max_retries = max_retries
        self.max_mtu_size = max_mtu_size
        self.use_ack = use_ack
        self.wait_for_frag = False
        self.packet_buffer = []
        self.last_frag_index = 0
        self.tx_seq_num = 0
        self.tx_seq_num_2 = 0
        self.tx_curr_packet_seq_num = -1
        self.rx_last_seq_num = -1
        self.thread_lock = threading.RLock()
        self.last_snr = 0
        self.send_only_when_trained = send_only_when_trained
        self.rx_array_trained = False
        self.tx_array_trained = False
        self.tx_beam_ID = initial_tx_beam_index
        self.tx_RF_gain = initial_TX_RF_gain
        self.rx_beam_ID = initial_rx_beam_index
        self.tx_mcs = tx_mcs
        self.tx_scrambler_seed = tx_scrambler_seed
        self.tx_pckt_type = 0
        self.tx_trn_len = 0
        self.tx_beam_track_req = 0
        self.tx_last_rssi = 0
        self.no_call = 0
        self.decimation = 5
        self.current_snr = -50.0
        self.timer = 0
        self.station_code = station_code
        self.partner_station_code = partner_station_code

        #Logging Configuration
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        if conf_parent_dir[-1] != '/':
            conf_parent_dir = conf_parent_dir + '/'
                       
        if not os.path.exists(conf_parent_dir):
            try:
                os.makedirs(conf_parent_dir)
            except:
                print("[Stop & Wait ARQ MAC]: Exception; could not create parent directory for configuration logging.")
                exit()
        
        self.configuration_file_name = conf_parent_dir + 'MAC_Configuration_Station_' + str(station_code) + '_' + str(timestamp) + '.csv'
        self.configuration_csv_fields = ['Use ACK', 'ACK Timeout', 'Max retries', 'Max MTU size', 'MCS', 'Init TX Beam Index', 'Init RX Beam Index', 'TX RF Gain', 'Send Only When Trained']
        with open(self.configuration_file_name,'w') as config_file:
            csv_writer = csv.DictWriter(config_file, fieldnames=self.configuration_csv_fields)
            csv_writer.writeheader()
            csv_writer.writerow({'Use ACK':use_ack, 'ACK Timeout':ack_timeout, 'Max retries':max_retries, 'Max MTU size':max_mtu_size, 'MCS':tx_mcs, 'Init TX Beam Index':initial_tx_beam_index, 'Init RX Beam Index':initial_rx_beam_index, 'TX RF Gain':initial_TX_RF_gain, 'Send Only When Trained':send_only_when_trained})

    ## FINITE STATE MACHINE ##
    def run_fsm(self):
        with self.thread_lock:
          if self.state == self.STATE_IDLE: #State IDLE
            if self.beamsteering_protocol_queue.empty() == False: #Prioritize Beamsteering protocol packet queue over UDP packet queue
              self.last_tx_packet = self.beamsteering_protocol_queue.get() #Get last TX packet out of queue

              msg_str = "".join([chr(x) for x in pmt.u8vector_elements(pmt.cdr(self.last_tx_packet))])
              curr_packet_len = len(msg_str[3:])
              self.tx_curr_packet_seq_num = ord(msg_str[0])

              #self.last_tx_time = time.time() #Set current time to last tx time
              #print('[Stop & Wait ARQ MAC]: Sending beamsteering packet with payload length: '+ str(curr_packet_len) +'. Queue fill level = ', self.beamsteering_protocol_queue.qsize())

              self.message_port_pub(pmt.intern('phy_out'), self.last_tx_packet) #Publish message at phy_out port
              #print('MAC has sent message form beamsteering')
            #if self.use_ack: #If ACK mode is activated then we have to wait for the ACK
            #self.state = self.STATE_WAIT_FOR_ACK
              
            elif self.udp_queue.empty() == False: #UDP Queue is not empty
              if self.send_only_when_trained == False or (self.send_only_when_trained == True and self.tx_array_trained == True):
                self.last_tx_packet = self.udp_queue.get() #Get last TX packet out of queue

                msg_str = "".join([chr(x) for x in pmt.u8vector_elements(pmt.cdr(self.last_tx_packet))])
                curr_packet_len = len(msg_str[3:])
                self.tx_curr_packet_seq_num = ord(msg_str[0])

                meta = pmt.car(self.last_tx_packet)
                payload = pmt.cdr(self.last_tx_packet)
                meta = pmt.dict_add(meta, pmt.string_to_symbol("last_rssi"), pmt.from_long(self.tx_last_rssi))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(self.tx_beam_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.from_long(self.tx_RF_gain))
                self.last_tx_packet = pmt.cons(meta, payload)

                #self.last_tx_time = time.time() #Set current time to last tx time
                #print('[Stop & Wait ARQ MAC]: Sending packet with payload length: '+ str(curr_packet_len) +'. Queue fill level = ', self.udp_queue.qsize())
                self.message_port_pub(pmt.intern('phy_out'), self.last_tx_packet) #Publish message at phy_out port
                if self.use_ack: #If ACK mode is activated then we have to wait for the ACK #Don't send ACKs for beamsteering protocol packets
                    self.state = self.STATE_WAIT_FOR_ACK
                    if self.timer != 0:
                      self.timer.cancel()
                    self.timer = threading.Timer(self.ack_timeout, self.resend_packet)
                    self.timer.start()
              #else:
                #print('[Stop & Wait ARQ MAC]: WARNING: UDP packets are not transmitted: Waiting for TX antenna array training!')
            #else:
              #print('[Stop & Wait ARQ MAC]: INFO: No packet in buffers to transmit!')
          
          elif self.state == self.STATE_WAIT_FOR_ACK: #State wait for ACK
            #ACK is not received in ACK timeout interval -> retransmission of the packet
            # current_time = time.time()
            # if (current_time - self.last_tx_time) > self.ack_timeout:
            #   self.retries += 1
            #   if self.retries > self.max_retries:
            #     print('[Stop & Wait ARQ MAC]: INFO: Maximum number of packet retransmissions reached. Dropping packet')
            #     self.state = self.STATE_IDLE
            #     self.retries = 0
            #   else:
            #     print('[Stop & Wait ARQ MAC]: ACK timeout. Retransmitting')
            #     self.last_tx_time = current_time
            #     self.message_port_pub(pmt.intern('phy_out'), self.last_tx_packet)
              return
          else:
            print('[Stop & Wait ARQ MAC]: ERROR: Undefined State!')

    def resend_packet(self):
          # ACK is not received in ACK timeout interval -> retransmission of the packet
          self.retries += 1
          if self.retries > self.max_retries:
            print('[Stop & Wait ARQ MAC]: INFO: Maximum number of packet retransmissions reached. Dropping packet')
            self.state = self.STATE_IDLE
            self.retries = 0
          else:
            print('[Stop & Wait ARQ MAC]: ACK timeout. Retransmitting')
            self.message_port_pub(pmt.intern('phy_out'), self.last_tx_packet)
            self.timer = threading.Timer(self.ack_timeout, self.resend_packet)
            self.timer.start()

    ## HANDLE UDP MESSAGES ##
    def handle_udp_message(self, msg_pmt):
        with self.thread_lock:
          #External UDP packets might not always fulfill the maximum MTU size limitation. Therefore, we fragment them.
          packets_str = self.fragment_packet(msg_pmt)
          for packet_str in packets_str:
            # Increase sequence number and add to packet
            if self.tx_seq_num < 255:
              self.tx_seq_num = self.tx_seq_num + 1
            else:
              self.tx_seq_num = 0
            packet_seq_num_str = chr(self.tx_seq_num)
            # Assemble packet
            packet_str_total = packet_seq_num_str + chr(self.station_code) + chr(self.PACKET_TYPE_DATA) + packet_str
            # Prepare string for sending as pmt
            send_pmt = pmt.make_u8vector(len(packet_str_total), ord(' '))
            for i in range(len(packet_str_total)):
              pmt.u8vector_set(send_pmt, i, ord(packet_str_total[i]))

            #Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("mcs"), pmt.from_long(self.tx_mcs))
            meta = pmt.dict_add(meta, pmt.string_to_symbol("scrambler_seed"), pmt.from_long(self.tx_scrambler_seed))
            meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_type"), pmt.from_long(self.tx_pckt_type))
            meta = pmt.dict_add(meta, pmt.string_to_symbol("trn_len"), pmt.from_long(self.tx_trn_len))
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"), pmt.from_long(0))
            
            pdu = pmt.cons(meta, send_pmt)
            #Append packet to queue
            self.udp_queue.put(pdu)
        self.run_fsm() # Trigger FSM handle function

    ## HANDLE BEAMSTEERING PROTOCOL MESSAGES ##
    def handle_beamforming_protocol_message(self, msg_pmt):
        with self.thread_lock:
          tx_beam_ID_found = False
          rx_beam_ID_found = False
          tx_array_trained_found = False
          rx_array_trained_found = False

          #distinguish between messages intended to transmit to another responder station and messages setting flags inside this MAC protocol
          meta = pmt.car(msg_pmt)
          if pmt.is_dict(meta) == False:
            print("[Stop & Wait ARQ MAC]: ERROR: Recevied beamsteering meta is not a PMT dictionary!")
          if pmt.dict_has_key(meta, pmt.string_to_symbol("msg_type")):
            r = pmt.dict_ref(meta, pmt.string_to_symbol("msg_type"), pmt.PMT_NIL)
            msg_type = pmt.to_long(r)
          else:
            msg_type = "ERROR"

          #For setting flags
          if msg_type == self.MAC_SET_MESSAGE:
            #print('[Stop & Wait ARQ MAC]: MAC SET MESSAGE received')
            #Read from metadata
            if pmt.dict_has_key(meta, pmt.string_to_symbol("tx_beam_id")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("tx_beam_id"), pmt.PMT_NIL)
              self.tx_beam_ID = pmt.to_uint64(r)
              tx_beam_ID_found = True
            if pmt.dict_has_key(meta, pmt.string_to_symbol("tx_RF_gain")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.PMT_NIL)
              self.tx_RF_gain = pmt.to_uint64(r)
              tx_RF_gain_found = True
            if pmt.dict_has_key(meta, pmt.string_to_symbol("rx_beam_id")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("rx_beam_id"), pmt.PMT_NIL)
              self.rx_beam_ID = pmt.to_uint64(r)
              rx_beam_ID_found = True
            if pmt.dict_has_key(meta, pmt.string_to_symbol("tx_array_trained")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("tx_array_trained"), pmt.PMT_NIL)
              self.tx_array_trained = pmt.to_bool(r)
              tx_array_trained_found = True
            if pmt.dict_has_key(meta, pmt.string_to_symbol("rx_array_trained")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("rx_array_trained"), pmt.PMT_NIL)
              self.rx_array_trained = pmt.to_bool(r)
              rx_array_trained_found = True

            if tx_beam_ID_found == False and rx_beam_ID_found == False and tx_array_trained_found == False and rx_array_trained_found == False and tx_RF_gain_found == False:
              print("[Stop & Wait ARQ MAC]: ERROR: No meta data contained in MAC set message from beamsteering protocol")

            if rx_beam_ID_found == True:
              meta = pmt.make_dict()
              meta = pmt.dict_add(meta, pmt.string_to_symbol("rx_beam_id"), self.rx_beam_ID)
              self.message_port_pub(pmt.intern('antenna_array_control_out'), pmt.cons(meta, pmt.PMT_NIL)) 
              
          #For transmission
          elif msg_type == self.BEAMSTEERING_PROTOCOL_MESSAGE:
            tx_beam_ID = self.tx_beam_ID
            tx_RF_gain = self.tx_RF_gain
            tx_beam_track_req = self.tx_beam_track_req
            #Update tags / meta values
            if pmt.dict_has_key(meta, pmt.string_to_symbol("tx_beam_id")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("tx_beam_id"), pmt.PMT_NIL)
              tx_beam_ID = pmt.to_uint64(r)
            if pmt.dict_has_key(meta, pmt.string_to_symbol("tx_RF_gain")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.PMT_NIL)
              tx_RF_gain = pmt.to_uint64(r)
            if pmt.dict_has_key(meta, pmt.string_to_symbol("beam_track_req")):
              r = pmt.dict_ref(meta, pmt.string_to_symbol("beam_track_req"), pmt.PMT_NIL)
              tx_beam_track_req = pmt.to_uint64(r)
            packets_str = self.fragment_packet(msg_pmt) #To be on the save side -> fragment also the beamsteering protocol related packets
            for packet_str in packets_str:
              # Increase sequence number and add to packet
              if self.tx_seq_num_2 < 255:
                self.tx_seq_num_2 = self.tx_seq_num_2 + 1
              else:
                self.tx_seq_num_2 = 0
              packet_seq_num_str = chr(self.tx_seq_num_2)
              # Assemble packet
              packet_str_total = packet_seq_num_str + chr(self.station_code) + chr(self.PACKET_TYPE_BEAMSTEERING_MESSAGE) + packet_str
              # Prepare string for sending as pmt
              send_pmt = pmt.make_u8vector(len(packet_str_total), ord(' '))
              for i in range(len(packet_str_total)):
                pmt.u8vector_set(send_pmt, i, ord(packet_str_total[i]))

              #Add tags/meta
              meta = pmt.make_dict()
              meta = pmt.dict_add(meta, pmt.string_to_symbol("mcs"), pmt.from_long(self.tx_mcs))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("scrambler_seed"), pmt.from_long(self.tx_scrambler_seed))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_type"), pmt.from_long(self.tx_pckt_type))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("trn_len"), pmt.from_long(self.tx_trn_len))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"), pmt.from_long(tx_beam_track_req))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("last_rssi"), pmt.from_long(self.tx_last_rssi))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(tx_beam_ID))
              meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.from_long(tx_RF_gain))

              send_pmt = pmt.cons(meta, send_pmt)
              #Append packet to prioritzed queue
              self.beamsteering_protocol_queue.put(send_pmt)
          else:
            print('[Stop & Wait ARQ MAC]: ERROR: Undefined beamsteering protocol message received!')
        #print 'MAC has handled message form beamsteering'
        self.run_fsm() # Trigger FSM handle function
    
    ## HANDLE SNR MESSAGES ##
    def handle_snr_message(self, msg_pmt):
      with self.thread_lock:
        snr_pmt = pmt.to_python(msg_pmt)
        self.current_snr = float(snr_pmt)

    ## HANDLE PHY MESSAGES ##
    def handle_phy_message(self, msg_pmt):
        with self.thread_lock:
            # Convert received message to string
            msg = pmt.cdr(msg_pmt)
            packet_str_orig = "".join([chr(x) for x in pmt.u8vector_elements(msg)])
            if len(packet_str_orig) > 3:
                #Get relevant parameters of message
                packet_rx_seq_number_byte = ord(packet_str_orig[0]) #sequence number
                station_code_byte = ord(packet_str_orig[1]) #station code
                packet_type_byte = ord(packet_str_orig[2]) #packet type
                packet_str = packet_str_orig[3:] #payload

                # This is cheating... This should not be fixed in this block but earlier in phase correction
                if station_code_byte > 127:
                    #print('[Stop & Wait ARQ]: Warning: Station code > 127. Maybe bits are just inverted... Trying to fix that.')
                    # # Apparently all the bits are negated... This might work for BPSK but not sure what happens for
                    # # higher modulation orders
                    packet_str_orig = "".join([chr(255-x) for x in pmt.u8vector_elements(msg)])
                    packet_rx_seq_number_byte = ord(packet_str_orig[0])  # sequence number
                    station_code_byte = ord(packet_str_orig[1])  # station code
                    packet_type_byte = ord(packet_str_orig[2])  # packet type
                    packet_str = packet_str_orig[3:]  # payload


                #print('[Stop & Wait ARQ MAC]: Packet received with sequence number ', packet_rx_seq_number_byte, ', type: ', packet_type_byte)
                dropped = False

                if station_code_byte == self.partner_station_code: #Ignore own packets received due to self-interference (weak isolation between TX and RX) and only accept partner station packets
                    meta = pmt.car(msg_pmt)
                    if pmt.dict_has_key(meta, pmt.string_to_symbol("evm")):
                        r = pmt.dict_ref(meta, pmt.string_to_symbol("evm"), pmt.PMT_NIL)
                        self.tx_last_rssi = int(-1 * round(pmt.to_double(r))) #RSSI is choosen to be the complement of the EVM
                    else:
                        print('[Stop & Wait ARQ MAC]: WARNING: No EVM tag contained in message.')

                    # Handle received packets according to their types
                    if packet_type_byte == self.PACKET_TYPE_DATA:
                        #print('[Stop & Wait ARQ MAC]: Data packet received.')
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_num"), pmt.from_long(packet_rx_seq_number_byte))
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_type_MAC"), pmt.from_long(packet_type_byte))
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("snr"), pmt.from_double(self.current_snr))

                        #Check sequence number (Received sequence number has to be the previous sequence number + 1)
                        if self.rx_last_seq_num == packet_rx_seq_number_byte: # Duplicate Packet
                            print('[Stop & Wait ARQ MAC]: WARNING: Duplicate data packet is ignored.')
                            drop = True
                        elif (self.rx_last_seq_num + 1) != packet_rx_seq_number_byte: #Wrong order of sequence number
                            print('[Stop & Wait ARQ MAC]: WARNING: Received data packet has a bad sequence number: ', packet_rx_seq_number_byte)
                        self.rx_last_seq_num = packet_rx_seq_number_byte #Update last sequence number
                        if self.use_ack:
                            #send ACK packet
                            #print '[Stop & Wait ARQ MAC]: Sending ACK'
                            ack_pdu = self.generate_ack_packet_pdu(packet_rx_seq_number_byte)
                            self.message_port_pub(pmt.intern('phy_out'), ack_pdu)
                        if not dropped:
                            #process fragment
                            send_pmt = self.process_fragment(packet_str)
                            if send_pmt != 0:
                                self.message_port_pub(pmt.intern('udp_socket_out'), pmt.cons(pmt.PMT_NIL, send_pmt))
                                self.message_port_pub(pmt.intern('beamforming_protocol_out'), pmt.cons(meta, pmt.PMT_NIL)) #empty payload, for preamble_RSSI transmission
                                self.message_port_pub(pmt.intern('rx_phy_logger_out'), pmt.cons(meta, send_pmt))
                    elif packet_type_byte == self.PACKET_TYPE_BEAMSTEERING_MESSAGE:
                        #print('[Stop & Wait ARQ MAC]: Beamsteering packet received.')
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_num"), pmt.from_long(packet_rx_seq_number_byte))
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_type_MAC"), pmt.from_long(packet_type_byte))
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("snr"), pmt.from_double(self.current_snr))
                        if (self.rx_last_seq_num == packet_rx_seq_number_byte and packet_type_byte): # Duplicate Packet
                            print('[Stop & Wait ARQ MAC]: WARNING: Duplicate beamsteering packet is ignored.')
                            drop = True
                        #elif (self.rx_last_seq_num + 1) != packet_rx_seq_number_byte: #Wrong order of sequence number
                        #print('[Stop & Wait ARQ MAC]: WARNING: Received beamsteering packet has a bad sequence number: ', packet_rx_seq_number_byte)
                        #self.rx_last_seq_num = packet_rx_seq_number_byte #Update last sequence number
                        #if self.use_ack: #Do not send ACKs for beamsteering protocol messages
                        #send ACK packet
                        #print('[Stop & Wait ARQ MAC]: Sending ACK for beamsteering packet')
                        #ack_pdu = self.generate_ack_packet_pdu(packet_rx_seq_number_byte)
                        #self.message_port_pub(pmt.intern('phy_out'), ack_pdu)
                        if not dropped:
                            send_pmt = self.process_fragment(packet_str)
                            if send_pmt != 0:
                                self.message_port_pub(pmt.intern('beamforming_protocol_out'), pmt.cons(meta, send_pmt))
                                self.message_port_pub(pmt.intern('rx_phy_logger_out'), pmt.cons(meta, send_pmt))
                    elif packet_type_byte == self.PACKET_TYPE_ACK:
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_num"), pmt.from_long(packet_rx_seq_number_byte))
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_type_MAC"), pmt.from_long(packet_type_byte))
                        meta = pmt.dict_add(meta, pmt.string_to_symbol("snr"), pmt.from_double(self.current_snr))
                        self.message_port_pub(pmt.intern('rx_phy_logger_out'), pmt.cons(meta, msg))
                        self.message_port_pub(pmt.intern('beamforming_protocol_out'), pmt.cons(meta, pmt.PMT_NIL)) #empty payload, for preamble_RSSI transmission
                        #Check sequence number (Received sequence number of ACK has to be the same number of the previously transmitted packet)
                        if self.tx_curr_packet_seq_num == packet_rx_seq_number_byte:
                            #Packet correctly transmitted -> Set State back to IDLE since we are no longer waiting for an ACK
                            #print('[Stop & Wait ARQ MAC]: Correct ACK received')
                            if self.timer != 0:
                                self.timer.cancel()
                            self.state = self.STATE_IDLE
                            self.retries = 0
                            self.run_fsm()
                        elif (self.tx_curr_packet_seq_num - 1) == packet_rx_seq_number_byte:
                            print('[Stop & Wait ARQ MAC]: WARNING: Duplicate ACK is ignored.')
                        else:
                            print('[Stop & Wait ARQ MAC]: WARNING: ACK with wrong sequence number.')
                    else:
                        print('[Stop & Wait ARQ MAC]: ERROR: Undefined packet received! ', packet_type_byte)
                else:
                    print('[Stop & Wait ARQ MAC]: Packet has wrong station code ' + str(station_code_byte))
            else:
                print('[Stop & Wait ARQ MAC]: Packet length < 3.')

    ## OTHER FUNCTIONS ##
    def generate_ack_packet_pdu(self, seq_num):
        packet_str = chr(seq_num) + chr(self.station_code) + chr(self.PACKET_TYPE_ACK) + 'ack'
        send_pmt = pmt.make_u8vector(len(packet_str), ord(' '))
        for i in range(len(packet_str)):
          pmt.u8vector_set(send_pmt, i, ord(packet_str[i]))
        #Add tags/meta
        meta = pmt.make_dict()
        meta = pmt.dict_add(meta, pmt.string_to_symbol("mcs"), pmt.from_long(self.tx_mcs)) #Send with BPSK modulation
        meta = pmt.dict_add(meta, pmt.string_to_symbol("scrambler_seed"), pmt.from_long(self.tx_scrambler_seed))
        meta = pmt.dict_add(meta, pmt.string_to_symbol("packet_type"), pmt.from_long(self.tx_pckt_type))
        meta = pmt.dict_add(meta, pmt.string_to_symbol("trn_len"), pmt.from_long(0))
        meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"), pmt.from_long(0))
        meta = pmt.dict_add(meta, pmt.string_to_symbol("last_rssi"), pmt.from_long(self.tx_last_rssi))
        meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(self.tx_beam_ID))
        meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.from_long(self.tx_RF_gain))
        return pmt.cons(meta, send_pmt)

    def process_fragment(self, packet_str):
        frag_byte = ord(packet_str[0])
        #process fragment header
        frag_index = frag_byte >> 2
        if frag_byte & 0x01 == 1: #Packet is a fragment
          self.last_frag_index = frag_index
          if frag_byte & 0x02 == 0: #Packet is not the last fragment -> Store in buffer to re-asssemble the fragements
            self.wait_for_frag = True
            self.packet_buffer += packet_str[1:]
          else: #Packet is the last fragment -> Don't wait for further fragments
            self.wait_for_frag = False
            self.packet_buffer += packet_str[1:]
            packet_str = self.packet_buffer #get all the assembled packet fragements
            self.packet_buffer = ''
        else: #Packet is no fragment
          packet_str = packet_str[1:]
          self.wait_for_frag = False
        if not self.wait_for_frag: #don't wait for further fragments -> Send packets to UDP port
          send_pmt = pmt.make_u8vector(len(packet_str), ord(' '))
          for i in range(len(packet_str)):
            pmt.u8vector_set(send_pmt, i, ord(packet_str[i]))
          return send_pmt
        else:
          return 0

    def fragment_packet(self, msg_pmt): # fragment incoming udp packet to smaller packets which fulfill the maximum MTU size
        meta = pmt.to_python(pmt.car(msg_pmt))
        msg = pmt.cdr(msg_pmt)
        if not pmt.is_u8vector(msg):
            print("[Stop & Wait ARQ MAC]: ERROR: Wrong pmt format!")
            return
        msg_str = "".join([chr(x) for x in pmt.u8vector_elements(msg)])
        num_mtus = (len(msg_str) // self.max_mtu_size) #calculate number of full fragmented packets / MTUs
        if len(msg_str) % self.max_mtu_size != 0: #check whether there is further packet which is shorter than the max MTU size
          num_mtus = num_mtus + 1
        mtu_index_start = 0
        mtu_index_end = 0
        last = False
        frag_required = False
        frag_index = 0
        packet_list = []
        if num_mtus > 1:
          frag_required = True
        for i in range(num_mtus): #Start actual fragmentation
          if (len(msg_str) - mtu_index_start) > self.max_mtu_size: #Calculate start and end index
            mtu_index_end = mtu_index_start + self.max_mtu_size
          else:
            mtu_index_end = len(msg_str)
            last = True

          fragment_str = msg_str[mtu_index_start:mtu_index_end] #Get fragment with calculated indices
          packet = self.add_frag_hdr(fragment_str, frag_required, last, i)  #Add fragment header
          mtu_index_start += self.max_mtu_size #Increment start index for next fragment
          packet_list.append(packet) #Send/Append the message
        return packet_list

    def add_frag_hdr(self, payload_str, frag_required, last_frag, frag_index):
        hdr_str = ''
        if not frag_required:
          hdr_str = '\x00'
        else:
          frag_byte = 0
          if not last_frag:
            frag_byte = 1 | frag_index << 2
          else:
            frag_byte = 3 | frag_index << 2
          hdr_str = chr(frag_byte)

        packet_str = hdr_str + payload_str
        return packet_str

    ## GENERAL WORK FUNCTION ##
    # Call is not absolutely necessary but should be done to ensure proper timeout handling
    def general_work(self, input_items, output_items):
        #called to ensure early timeout detection
        print('general_work_called')
        return 0
    
    def forecast(self, noutput_items, ninput_items_required):
        #required to frequently call the general_work function
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items # 0 #Setting this to zero means that scheduler always calls this function

