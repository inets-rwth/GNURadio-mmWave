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
from gnuradio import digital
import pmt
import string
import csv
import datetime
import threading
import shutil
import os

class RX_PHY_logger(gr.basic_block):
    """
    docstring for block RX_PHY_logger
    """    
    # Packet type identifiers
    PACKET_TYPE_DATA = 0
    PACKET_TYPE_ACK = 1
    PACKET_TYPE_BEAMSTEERING_MESSAGE = 2
    
    def __init__(self, station_code, mode, log_file_parent_dir, log_per_sector, log_per_sector_parent_dir, simulation=False):
        gr.basic_block.__init__(self,
            name="RX_PHY_logger",
            in_sig=[],
            out_sig=[])
            
        self.message_port_register_in(pmt.intern('rx_logger_in'))
        self.set_msg_handler(pmt.intern('rx_logger_in'), self.handle_rx_phy_message)

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        self.csv_fields = ['Timestamp', 'SNR', 'EVM', 'Preamble RSS (before AGC)', 'Preamble RMS', 'Packet Number',
                           'Packet Type', 'Packet Length', 'MCS', 'Byte Errors', 'Bit Errors', 'Preamble RSS (before AGC)',
                           'RX Beam ID', 'TT Az angle', 'TT El angle']
        if log_file_parent_dir[-1] != '/':
            log_file_parent_dir = log_file_parent_dir + '/'
                       
        if not os.path.exists(log_file_parent_dir):
            try:
                os.makedirs(log_file_parent_dir)
            except:
                print("[RX PHY Logger]: Exception; could not create parent directory for event logging.")
                exit()
        
        self.log_file_name = log_file_parent_dir + 'ReceivedPackets_Station_' + str(station_code) + '_' + str(timestamp) + '.csv'

        with open(self.log_file_name, 'w') as log_file:
            csv_writer = csv.DictWriter(log_file, fieldnames=self.csv_fields)
            csv_writer.writeheader()
            
        self.station_code = station_code
        self.simulation_mode = simulation
        self.valid = False
        self.log = False
        self.curr_snr = 0
        self.num_rec_packets = 0
        self.sum_snr = 0
        self.avg_snr = 0
        self.per = 0
        self.num_packet_errors = 0
        # self.num_bit_errors = 0
        self.skip_header_bytes_start = 0  # 5 #1 byte type, 1 byte node_id, 4 byte crc
        self.skip_header_bytes_end = 0  # 4 #1 byte type, 1 byte node_id, 4 byte crc
        self.check_payload = mode
        print("[RX PHY Logger] Testing received packets against " + self.check_payload + " test sequence")
        numpy.random.seed(0)
        self.payload_random = numpy.random.randint(0, 256, 1000)  # 1000 byte random payload
        self.payload_defined = numpy.tile(numpy.arange(0, 256, 1), 4)  # defined payload (see defined payload generator)
        
        # to enable logging per sector
        self.log_per_sector = log_per_sector
        self.init_timestamp = timestamp
        if self.log_per_sector:
            self.log_per_sector_fnames = []
            # add backslash to the end of path if not there
            if log_per_sector_parent_dir[-1] != '/':
                log_per_sector_parent_dir = log_per_sector_parent_dir + '/'
                       
            if not os.path.exists(log_per_sector_parent_dir):
                try:
                    os.makedirs(log_per_sector_parent_dir)
                except:
                    print("[RX PHY Logger]: Exception; could not create parent directory for per sector logging.")
                    exit()
            self.log_per_sector_save_dir = log_per_sector_parent_dir
            self.log_per_sector_temp_dir = log_per_sector_parent_dir + 'temp/'
            
            if not os.path.exists(self.log_per_sector_temp_dir):
                try:
                    os.makedirs(self.log_per_sector_temp_dir)
                except:
                    print("[RX PHY Logger]: Exception; could not create temp directory for per sector logging.")
                    exit()
        
        self.tt_inv_timer = 0
        self.curr_sector_fname = ""
        self.curr_sector_fname_final_dest = ""
        self.last_tt_az_angle_received = 0.0
        self.last_tt_el_angle_received = 0.0
        self.tt_run_no = 0 # starts from 1
            
        # Set message port registers
        self.message_port_register_in(pmt.intern('tt_msg'))

        # Set incoming message callback functions
        self.set_msg_handler(pmt.intern('tt_msg'), self.handle_tt_message)

    def handle_rx_phy_message(self, msg_pmt):
        meta = pmt.to_python(pmt.car(msg_pmt))
        packet_num = meta["packet_num"]
        if self.simulation_mode:
            packet_rx_time = 0
            packet_rx_time_full_sec = 0
            packet_rx_time_frac_sec = 0
        else:
            packet_rx_time = meta["rx_time"]
            packet_rx_time_full_sec = packet_rx_time[0]
            packet_rx_time_frac_sec = packet_rx_time[1]
        packet_type = meta["packet_type_MAC"]
        snr = meta["snr"]
        rx_beam_id = -1
        tt_az_angle = -500
        tt_el_angle = -500
        preamble_rss = -500
        try:
            rx_beam_id = meta["rx_beam_id"]
            tt_az_angle = meta["tt_az_angle"]
            tt_el_angle = meta["tt_el_angle"]
            preamble_rss = meta["preamble_rss"]
        except:
            print('[RX PHY Logger] Warning. Could not find all tags.')
        preamble_rms = meta["preamble_rms"]
        preamble_snr = meta["preamble_snr"]
        evm = meta["evm"]
        mcs = meta["mcs"]
        msg = pmt.cdr(msg_pmt)
        if pmt.length(msg) < 0:
            print("[RX PHY Logger] Packet Error (Negative Payload length)")
            return
        msg_data = pmt.u8vector_elements(msg)
        packet_len = len(msg_data)

        if packet_len > 0:  # check if packet has payload
            self.num_rec_packets += 1
            timestamp = packet_rx_time_full_sec + packet_rx_time_frac_sec
            # print('[RX PHY Logger] Packet received with sequence number ' + str(packet_num) + ' and type ' + str(packet_type) + '. Total #Packets = ' + str(self.num_rec_packets))
            user_data = list(msg_data)
            # print("Received packet:")
            # print str(msg_data)
            if packet_type == self.PACKET_TYPE_DATA:
                if self.check_payload == 'random':
                    byte_errors, bit_errors = self.compare_lists(user_data, self.payload_random)
                    if byte_errors > 0:
                        print(str(user_data))
                        self.num_packet_errors += 1
                        print('[RX PHY Logger] Packet error. Total Errors = ' + str(self.num_packet_errors) + '. Total #Packets = ' + str(self.num_rec_packets))
                    self.log_packet(timestamp, snr, evm, preamble_snr, preamble_rms, packet_num, packet_type,
                                    packet_len, mcs, byte_errors, bit_errors, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle)
                elif self.check_payload == 'defined':
                    byte_errors, bit_errors = self.compare_lists(user_data, self.payload_defined)
                    if byte_errors > 0:
                        print(str(user_data))
                        self.num_packet_errors += 1
                        print('[RX PHY Logger] Packet error. Total Errors = ' + str(
                            self.num_packet_errors) + '. Total #Packets = ' + str(self.num_rec_packets))
                    self.log_packet(timestamp, snr, evm, preamble_snr, preamble_rms, packet_num, packet_type,
                                    packet_len, mcs, byte_errors, bit_errors, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle)
                else:
                    self.log_packet(timestamp, snr, evm, preamble_snr, preamble_rms, packet_num, packet_type,
                                    packet_len, mcs, -1, -1, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle)
            else:
                self.log_packet(timestamp, snr, evm, preamble_snr, preamble_rms, packet_num, packet_type, packet_len,
                                mcs, -1, -1, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle)

    def handle_tt_message(self, msg):
        if self.log_per_sector:
            msg_str = pmt.symbol_to_string(msg)
            l = msg_str.split(';')
            self.last_tt_az_angle_received = float(l[0])
            self.last_tt_el_angle_received = float(l[1])
            tt_inv_time = float(l[2])
            
            # set timer so that the program switches to the new csv file only as the invalid time is about to end
            self.tt_inv_timer = threading.Timer(tt_inv_time - 0.15, self.csv_switch_sector)
            self.tt_inv_timer.start()
            
    def csv_switch_sector(self):
        if self.curr_sector_fname != "": # if file already created and sector ended, move it to the final destination for syncronization
            shutil.copyfile(self.curr_sector_fname, self.curr_sector_fname_final_dest)            
        
        self.curr_sector_fname = self.log_per_sector_temp_dir + 'Station_' + str(self.station_code) + '_Az_' + str(self.last_tt_az_angle_received) + '_El_' + str(self.last_tt_el_angle_received) + '_Run_' + str(self.tt_run_no) + '.csv'
        self.curr_sector_fname_final_dest = self.log_per_sector_save_dir + 'Station_' + str(self.station_code) + '_Az_' + str(self.last_tt_az_angle_received) + '_El_' + str(self.last_tt_el_angle_received) + '_Run_' + str(self.tt_run_no) + '.csv'
            
        if self.curr_sector_fname not in self.log_per_sector_fnames:
            # if data from azimuth/elevation pair is received for the first time, first create the file and the header
            with open(self.curr_sector_fname, 'w') as sector_log_file:
                csv_writer = csv.DictWriter(sector_log_file, fieldnames=self.csv_fields)
                csv_writer.writeheader()
            self.log_per_sector_fnames.append(self.curr_sector_fname) # add to the list of created files
    
    def log_packet(self, timestamp, snr, evm, preamble_snr, preamble_rms, packet_num, packet_type, packet_len, mcs,
                   byte_errors, bit_errors, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle):
        with open(self.log_file_name, 'a') as log_file:
            csv_writer = csv.DictWriter(log_file, fieldnames=self.csv_fields)
            csv_writer.writerow(
                {'Timestamp': timestamp, 'SNR': snr, 'EVM': evm, 'Preamble RSS (before AGC)': preamble_snr,
                 'Preamble RMS': preamble_rms, 'Packet Number': packet_num, 'Packet Type': packet_type,
                 'Packet Length': packet_len, 'MCS': mcs, 'Byte Errors': byte_errors, 'Bit Errors': bit_errors,
                 'Preamble RSS (before AGC)': preamble_rss,
                 'RX Beam ID': rx_beam_id, 'TT Az angle': tt_az_angle, 'TT El angle': tt_el_angle
                 })
                 
        # per sector logging                       
        if self.log_per_sector:
            with open(self.curr_sector_fname, 'a') as sector_log_file:
                csv_writer = csv.DictWriter(sector_log_file, fieldnames=self.csv_fields)
                csv_writer.writerow(
                        {'Timestamp': timestamp, 'SNR': snr, 'EVM': evm, 'Preamble RSS (before AGC)': preamble_snr,
                        'Preamble RMS': preamble_rms, 'Packet Number': packet_num, 'Packet Type': packet_type,
                        'Packet Length': packet_len, 'MCS': mcs, 'Byte Errors': byte_errors, 'Bit Errors': bit_errors,
                        'Preamble RSS (before AGC)': preamble_rss,
                        'RX Beam ID': rx_beam_id, 'TT Az angle': tt_az_angle, 'TT El angle': tt_el_angle
                        })
            

    def compare_lists(self, list1, list2):
        byte_errors = 0
        bit_errors = 0
        for x, y in zip(list1, list2):
            if x != y:
                byte_errors += 1
                for i in range(0, 8):
                    if ((x >> i) & 0x01) != ((y >> i) & 0x01):
                        # self.num_bit_errors += 1
                        bit_errors += 1

        return byte_errors, bit_errors
