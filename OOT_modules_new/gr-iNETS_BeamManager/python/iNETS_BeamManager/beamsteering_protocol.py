#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 iNETS RWTH - Florian Wischeler
# updated by Niklas Beckmann and Berk Acikgoez
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
import pmt
from gnuradio import gr
import time
import threading
import random
import queue
import string
import csv
import datetime
import random
import os
import shutil

class beamsteering_protocol(gr.basic_block):
    """
    docstring for block beamsteering_protocol
    """
    # Packet type identifiers
    PACKET_TYPE_DATA = 0
    PACKET_TYPE_ACK = 1
    PACKET_TYPE_BEAMSTEERING_MESSAGE = 2

    # Beamsteering Algorithm Identifiers
    PLS_TX = 0  # TX Pencil Level Sweep
    PLS_TX_RX = 1  # TX and RX Pencil Level Sweep
    PLS_TIMER_BASED = 2  # TX PLS based on one-sided quasi-omni links
    SLS_TX = 3  # TX SLS, based on two-sided quasi-omni links
    SLS_TX_RX = 4  # TX and RX SLS, based on two-sided quasi-omni links
    SLS_TIMER_BASED = 5  # TX SLS based on one-sided quasi-omni link
    ITERATIVE_TX = 6
    ITERATIVE_TX_RX = 7
    ITERATIVE_TIMER_BASED = 8
    HISTORY_SEARCH = 9  # Based on A. Patra et al.: Smart mm-Wave Beam Steering Algorithm for Fast Link Re-Establishment under Node Mobility in 60 GHz Indoor WLANs
    EXHAUSTIVE_SEARCH = 10
    FIXED_BEAM_BACKUP_LINK = 11 # Fixed beam with backup link (mirror)

    # Beambook related variables
    QUASIOMNI_iNETS = 0
    SECTOR_iNETS = numpy.arange(45, 58, 1)
    MULITARMED_iNETS = [58, 59, 60]
    PENCIL_iNETS = numpy.arange(1, 22, 1) # use 45 for the 44 IDs for the EVK06002 (60 GHz)
    SECTOR_TO_PENCIL_MAPPING = [[1, 2, 3, 4], [3, 4, 5, 6], [6, 7, 8, 9], [9, 10, 11, 12, 13, 14], [15, 16, 17, 18, 19],
                                [19, 20, 21, 22], [21, 22, 23, 24, 25], [26, 27, 28, 29], [29, 30, 31, 32],
                                [32, 33, 34, 35], [35, 36, 37, 38], [39, 40, 41, 42],
                                [42, 43, 44]]  # nested list of pencil beams per sector beam list entry

    # RF Gain Identifiers
    PENCIL_RF_GAIN = 0x05
    QUASI_OMNI_RF_GAIN = 0x06
    SECTOR_RF_GAIN = 0x06
    MULTI_ARMED_RF_GAIN = 0x06

    # Message Type Identifiers
    MAC_SET_MESSAGE = 0  # Message to set parameters inside MAC protocol
    BEAMSTEERING_PROTOCOL_MESSAGE = 1  # Message to transmit via PHY to responder station

    # Logging Identifiers
    EVENT_TX = 0
    EVENT_RX = 1
    EVENT_RX_PACKET_DATA = 2

    # SSW related Identifiers
    # TRN_REQUEST = 0
    # TRN_REQUEST_ACK = 1
    TRN_SECTOR_SWEEP = 1
    TRN_PENCIL_SWEEP = 2
    TRN_PENCIL_SWEEP_FINISHED = 3
    TRN_SECTOR_SWEEP_FINISHED = 4
    TRN_SECTOR_SSW_FEEDBACK = 5
    TRN_PENCIL_SSW_FEEDBACK = 6
    TRN_SECTOR_SSW_FEEDBACK_ACK = 7
    TRN_PENCIL_SSW_FEEDBACK_ACK = 8
    INITIATOR = 0
    RESPONDER = 1
    
    TRN_FIXED_BEAM_BACKUP_LINK_SWITCH_DEFAULT = 9
    TRN_FIXED_BEAM_BACKUP_LINK_SWITCH_BACKUP = 10
    TRN_FIXED_BEAM_BACKUP_LINK_DATA_BURST = 11

    # OTHER
    TX_TRAINED = 0
    RX_TRAINED = 1
    BOTH_TRAINED = 2

    # Exhaustive search States
    EXHAUSTIVE_SEARCH_IDLE = 0
    EXHAUSTIVE_SEARCH_SEND_TRN_REQUEST = 1
    EXHAUSTIVE_SEARCH_TRN_REQUEST_RECEIVED = 2
    EXHAUSTIVE_SEARCH_TRN_REQUEST_ACK_RECEIVED = 3
    EXHAUSTIVE_SEARCH_SWEEP = 4
    EXHAUSTIVE_SEARCH_RECEIVE_SSW_FRAMES = 5
    EXHAUSTIVE_SEARCH_SEND_FEEDBACK = 6
    EXHAUSTIVE_SEARCH_FEEDBACK_RECEIVED = 7
    EXHAUSTIVE_SEARCH_FEEDBACK_ACK_RECEIVED = 8
    EXHAUSTIVE_SEARCH_UNDEFINED = 9
    EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE = 10

    # PLS States
    PLS_IDLE = 0
    PLS_SWEEP = 1
    PLS_RECEIVE_SSW_FRAMES = 2
    PLS_SEND_FEEDBACK = 3
    PLS_FEEDBACK_RECEIVED = 4
    PLS_FEEDBACK_ACK_RECEIVED = 5
    PLS_LAST_SSW_FRAME_RECEIVED = 6
    PLS_UNDEFINED = 7

    # SLS States
    SLS_IDLE = 0
    SLS_SEND_TRN_REQUEST = 1
    SLS_TRN_REQUEST_RECEIVED = 2
    SLS_TRN_REQUEST_ACK_RECEIVED = 3
    SLS_SWEEP = 4
    SLS_SWEEP_COMPLETE = 5
    SLS_RECEIVE_SSW_FRAMES = 6
    SLS_SEND_FEEDBACK = 7
    SLS_FEEDBACK_RECEIVED = 8
    SLS_FEEDBACK_ACK_RECEIVED = 9
    SLS_LAST_SSW_FRAME_RECEIVED = 10
    SLS_UNDEFINED = 11

    # ITERATIVE States
    ITERATIVE_IDLE = 1
    ITERATIVE_SECTOR_SWEEP = 2
    ITERATIVE_SECTOR_SWEEP_COMPLETE = 3
    ITERATIVE_PENCIL_SWEEP = 4
    ITERATIVE_PENCIL_SWEEP_COMPLETE = 5
    ITERATIVE_RECEIVE_SECTOR_SSW_FRAMES = 6
    ITERATIVE_RECEIVE_PENCIL_SSW_FRAMES = 7
    ITERATIVE_SEND_SECTOR_FEEDBACK = 8
    ITERATIVE_SEND_PENCIL_FEEDBACK = 9
    ITERATIVE_SECTOR_FEEDBACK_RECEIVED = 10
    ITERATIVE_PENCIL_FEEDBACK_RECEIVED = 11
    ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED = 12
    ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED = 13
    ITERATIVE_LAST_SECTOR_SSW_FRAME_RECEIVED = 14
    ITERATIVE_LAST_PENCIL_SSW_FRAME_RECEIVED = 15
    ITERATIVE_UNDEFINED = 16
    
    # Fixed Beam with Backup Link states and variables
    FIXED_BEAM_BACKUP_LINK_STATE_DATA_TRX = 0
    FIXED_BEAM_BACKUP_LINK_STATE_REPORT = 1
    FIXED_BEAM_BACKUP_LINK_SPI_SWITCH_RX = -1
    FIXED_BEAM_BACKUP_LINK_SPI_SWITCH_TX = -2

    def __init__(self, beamsteering_algorithm, custom_beambook_suffix, station_type, station_code,
                 single_training_for_TX_and_RX, retrain_RSSI_threshold, start_training, timeout_SLS,
                 timeout_SLS_timer_based, timeout_SLS_timer_based_receive_SSW_frames, timeout_PLS,
                 timeout_PLS_timer_based, timeout_PLS_timer_based_receive_SSW_frames, timeout_iterative,
                 timeout_iterative_timer_based, timeout_iterative_search_timer_based_receive_SSW_frames,
                 timeout_history_search, timeout_history_search_receive_SSW_frames, timeout_RSSI_value_interval,
                 experimental_setup_comment, log_config_parent_dir, log_per_sector, log_per_sector_parent_dir, 
                 fixed_beam_backup_link_default_beam_id, fixed_beam_backup_link_backup_beam_id,
                 fixed_beam_backup_link_data_state_duration, fixed_beam_backup_link_report_state_duration, 
                 fixed_beam_backup_link_distance, fixed_beam_backup_link_beam_switch_message_retrans_no,
                 fixed_beam, beam_interval, sweeping = False):
        gr.basic_block.__init__(self,
                                name="beamsteering_protocol",
                                in_sig=None,
                                out_sig=None)

        # Set message port registers
        self.message_port_register_in(pmt.intern('in'))
        self.message_port_register_out(pmt.intern('out'))
        self.message_port_register_out(pmt.intern('gui_out'))
        self.message_port_register_in(pmt.intern('beam_id_message'))
        self.message_port_register_in(pmt.intern('sweeping_message'))
        self.message_port_register_in(pmt.intern('tt_msg'))
        self.message_port_register_in(pmt.intern('lidar_message'))
        self.message_port_register_out(pmt.intern('spi_manager_out'))

        # Set incoming message callback functions
        self.set_msg_handler(pmt.intern('in'), self.handle_phy_message)
        self.set_msg_handler(pmt.intern('beam_id_message'), self.handle_beam_id_message)
        self.set_msg_handler(pmt.intern('sweeping_message'), self.handle_sweeping_message)
        self.set_msg_handler(pmt.intern('tt_msg'), self.handle_tt_message)
        self.set_msg_handler(pmt.intern('lidar_message'), self.handle_lidar_message)

        # Initialize variables
        self.beamsteering_algorithm = beamsteering_algorithm
        self.custom_beambook_suffix = custom_beambook_suffix
        self.station_code = station_code
        self.rx_array_trained = False
        self.tx_array_trained = False
        self.tx_beam_ID = 0
        self.rx_beam_ID = 0
        self.last_rssi_received = 0
        self.last_preamble_rms = 0
        self.last_beam_ID_received = -1
        self.single_training_for_TX_and_RX = True
        self.retrain_RSSI_threshold = retrain_RSSI_threshold
        self.best_beam = -1
        self.best_beam_gain = 0x00
        self.last_tx_time = 0
        self.last_state = -1
        self.thread_lock = threading.RLock()
        self.ready = threading.Event()
        self.packet_queue = queue.Queue()
        self.retransmit_counter = 0
        self.fixed_beam = fixed_beam
        self.last_preamble_snr = 0
        self.sweeping = sweeping

        if self.custom_beambook_suffix == '':  # Check if suffix is empty (Sivers IMA default)
            print('####### not yet implemented!')
        elif self.custom_beambook_suffix == '_iNETS':
            self.sector_IDs = self.SECTOR_iNETS
            self.multiarmed_IDs = self.MULITARMED_iNETS
            self.quasiomni_ID = self.QUASIOMNI_iNETS
            self.pencil_IDs = self.PENCIL_iNETS
            self.number_of_sectors = len(self.SECTOR_iNETS)
            self.number_of_pencils = len(self.PENCIL_iNETS)
        else:
            print('[Beamsteering Protocol]: ERROR: Beambook with given suffix unknown!')

        # General Beamsteering variables
        self.cdown = 0
        self.direction = -1
        self.list_of_beam_and_rssi = []
        self.best_initiator_sector_beam = 70
        self.best_responder_sector_beam = 70
        self.best_initiator_pencil_beam = 70
        self.best_responder_pencil_beam = 70
        self.my_station_type = station_type  # Am I the initiator or the responder?
        self.timer_RSSI_value_interval = 0
        self.timeout_RSSI_value_interval = timeout_RSSI_value_interval

        # Exhaustive search variables
        self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_IDLE
        self.exhaustive_pencil_iter = 0
        self.exhaustive_search_request_ACK_received = False
        
        # Time between consecutive beams (in seconds)
        self.beam_interval = beam_interval

        # PLS variables
        self.PLS_state = self.PLS_IDLE
        self.timer_PLS = 0
        self.timeout_PLS = timeout_PLS

        # Timer-based PLS variables
        self.PLS_timer_based_state = self.PLS_IDLE
        self.timer_PLS_timer_based = 0
        self.timeout_PLS_timer_based = timeout_PLS_timer_based
        self.PLS_timer_receive_SSW_frames = 0
        self.timeout_PLS_timer_based_receive_SSW_frames = timeout_PLS_timer_based_receive_SSW_frames

        # SLS variables
        self.SLS_state = self.SLS_IDLE
        self.timer_SLS = 0
        self.timeout_SLS = timeout_SLS

        # Timer Based SLS variables
        self.SLS_timer_based_state = self.SLS_IDLE
        self.timer_SLS_timer_based = 0
        self.timeout_SLS_timer_based = timeout_SLS_timer_based
        self.SLS_timer_receive_SSW_frames = 0
        self.timeout_SLS_timer_based_receive_SSW_frames = timeout_SLS_timer_based_receive_SSW_frames

        # Iterative Search variables
        self.iterative_search_state = self.ITERATIVE_IDLE
        self.timer_iterative_search = 0
        self.timeout_iterative_search = timeout_iterative

        # Iterative Search Timer Based variables
        self.iterative_search_timer_based_state = self.ITERATIVE_IDLE
        self.timer_iterative_search_timer_based = 0
        self.timeout_iterative_search_timer_based = timeout_iterative_timer_based
        self.iterative_search_timer_receive_SSW_frames = 0
        self.timeout_iterative_search_timer_based_receive_SSW_frames = timeout_iterative_search_timer_based_receive_SSW_frames

        # History Search variables
        self.history_search_state = self.SLS_IDLE
        self.timer_history_search = 0
        self.timeout_history_search = timeout_history_search
        self.history_search_timer_receive_SSW_frames = 0
        self.timeout_history_search_receive_SSW_frames = timeout_history_search_receive_SSW_frames
        self.history_of_good_sectors = []
        
        # Fixed Beam with Backup Link variables
        self.fixed_beam_backup_link_state = -1                                                              # only for the initial run
        self.fixed_beam_backup_link_default_beam_id = fixed_beam_backup_link_default_beam_id
        self.fixed_beam_backup_link_backup_beam_id = fixed_beam_backup_link_backup_beam_id
        self.fixed_beam_backup_link_data_state_duration = fixed_beam_backup_link_data_state_duration        # in seconds, validate/optimize this value
        self.fixed_beam_backup_link_report_state_duration = fixed_beam_backup_link_report_state_duration    # in seconds, validate/optimize this value
        self.fixed_beam_backup_link_distance = fixed_beam_backup_link_distance                              # distance between TX and RX in meters
        self.timer_fixed_beam_backup_link_next_state = 0
        self.fixed_beam_backup_link_lidar_obstacle_msg = False
        self.fixed_beam_backup_link_beam_switch_message_retrans_no = fixed_beam_backup_link_beam_switch_message_retrans_no # how many times will the beam switch message be retransmitted so that we are sure the initiator received it?
        self.fixed_beam_backup_link_checked_lidar = False                                                   # set as True once the lidar info is checked and the required messages have been sent
        # self.fixed_beam_backup_link_data_burst_packet_no = 20                                               # number of consecutive packets to be sent by the initiator during the data_trx state
        self.fixed_beam_backup_link_data_burst_packet_no = int((self.fixed_beam_backup_link_data_state_duration * 0.8) / self.beam_interval)
        # self.timer_fixed_beam_backup_link_wait_for_next_burst = 0                                           # timer to interleave data bursts
        # self.fixed_beam_backup_link_next_burst_delay = self.beam_interval * self.fixed_beam_backup_link_data_burst_packet_no # wait for the approx. duration of one burst. validate/optimize this value.
        self.fixed_beam_backup_link_wait_tx_rx_switch = 0.05                                                # in seconds, validate/optimize this value

        # Logging
        self.algorithm_string = ''
        if self.beamsteering_algorithm == self.PLS_TX:
            self.algorithm_string = 'PLS_TX'
        elif self.beamsteering_algorithm == self.PLS_TX_RX:
            self.algorithm_string = 'PLS_TX_RX'
        elif self.beamsteering_algorithm == self.PLS_TIMER_BASED:
            self.algorithm_string = 'PLS_TX_TIMER_BASED'
        elif self.beamsteering_algorithm == self.SLS_TX:
            self.algorithm_string = 'SLS_TX'
        elif self.beamsteering_algorithm == self.SLS_TX_RX:
            self.algorithm_string = 'SLS_TX_RX'
        elif self.beamsteering_algorithm == self.SLS_TIMER_BASED:
            self.algorithm_string = 'SLS_TX_Timer_Based'
        elif self.beamsteering_algorithm == self.ITERATIVE_TX:
            self.algorithm_string = 'Iterative_TX'
        elif self.beamsteering_algorithm == self.ITERATIVE_TX_RX:
            self.algorithm_string = 'Iterative_TX_RX'
        elif self.beamsteering_algorithm == self.ITERATIVE_TIMER_BASED:
            self.algorithm_string = 'Iterative_TX_Timer_Based'
        elif self.beamsteering_algorithm == self.HISTORY_SEARCH:
            self.algorithm_string = 'History_Search'
        elif self.beamsteering_algorithm == self.EXHAUSTIVE_SEARCH:
            self.algorithm_string = 'Exhaustive_Search'
        elif self.beamsteering_algorithm == self.FIXED_BEAM_BACKUP_LINK:
            self.algorithm_string = 'Fixed_Beam_with_Backup_Link'
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')
        # add backslash to the end of path if not there
        if log_config_parent_dir[-1] != '/':
            log_config_parent_dir = log_config_parent_dir + '/'
        # try to create the directory if it does not exist
        if not os.path.exists(log_config_parent_dir):
            try:
                os.makedirs(log_config_parent_dir)
            except:
                print("[Beamsteering Protocol]: Exception; could not create parent directory for logging/configuration.")
                exit()
        self.log_file_name = log_config_parent_dir + 'Beamsteering_Protocol_Events_' + self.algorithm_string + '_Station_' + str(
            station_code) + '_' + str(timestamp) + '.csv'
        self.csv_fields = ['Timestamp', 'Event', 'Packet Type', 'Direction', 'CDOWN', 'Used TX Beam', 'Beam Feedback',
                           'EVM', 'RSSI', 'Preamble RMS', 'RSS (before AGC)', 'RX Beam ID',
                           'TT Az angle', 'TT El angle']
        with open(self.log_file_name, 'w') as log_file:
            csv_writer = csv.DictWriter(log_file, fieldnames=self.csv_fields)
            csv_writer.writeheader()
        self.configuration_file_name = log_config_parent_dir + 'Beamsteering_Protocol_Configuration_' + self.algorithm_string + '_' + str(
            station_code) + '_' + str(timestamp) + '.csv'
        self.configuration_csv_fields = ['Algorithm', 'Experimental Setup', 'Station Type',
                                         'Single Training for TX and RX', 'Retrain RSSI Threshold',
                                         'Timeout RSSI Value Interval', 'Start Training', 'Timeout SLS', 'Timeout PLS',
                                         'Timeout Iterative', 'Timeout SLS Timer Based',
                                         'timeout_SLS_timer_based_receive_SSW_frames', 'timeout_PLS_timer_based',
                                         'timeout_PLS_timer_based_receive_SSW_frames', 'timeout_iterative_timer_based',
                                         'timeout_iterative_search_timer_based_receive_SSW_frames',
                                         'timeout_history_search', 'timeout_history_search_receive_SSW_frames',
                                         'Fixed_Beam_Backup_Link_Default_Beam_ID', 'Fixed_Beam_Backup_Link_Backup_Beam_ID']
        with open(self.configuration_file_name, 'w') as config_file:
            csv_writer = csv.DictWriter(config_file, fieldnames=self.configuration_csv_fields)
            csv_writer.writeheader()
            csv_writer.writerow({'Algorithm': self.algorithm_string, 'Experimental Setup': experimental_setup_comment,
                                 'Station Type': self.my_station_type,
                                 'Single Training for TX and RX': single_training_for_TX_and_RX,
                                 'Retrain RSSI Threshold': retrain_RSSI_threshold,
                                 'Timeout RSSI Value Interval': timeout_RSSI_value_interval,
                                 'Start Training': start_training, 'Timeout SLS': timeout_SLS,
                                 'Timeout PLS': timeout_PLS, 'Timeout Iterative': timeout_iterative,
                                 'Timeout SLS Timer Based': timeout_SLS_timer_based,
                                 'timeout_SLS_timer_based_receive_SSW_frames': timeout_SLS_timer_based_receive_SSW_frames,
                                 'timeout_PLS_timer_based': timeout_PLS_timer_based,
                                 'timeout_PLS_timer_based_receive_SSW_frames': timeout_PLS_timer_based_receive_SSW_frames,
                                 'timeout_iterative_timer_based': timeout_iterative_timer_based,
                                 'timeout_iterative_search_timer_based_receive_SSW_frames': timeout_iterative_search_timer_based_receive_SSW_frames,
                                 'timeout_history_search': timeout_history_search,
                                 'timeout_history_search_receive_SSW_frames': timeout_history_search_receive_SSW_frames,
                                 'Fixed_Beam_Backup_Link_Default_Beam_ID': fixed_beam_backup_link_default_beam_id,
                                 'Fixed_Beam_Backup_Link_Backup_Beam_ID': fixed_beam_backup_link_backup_beam_id})
        
        # to enable logging per turntable position/sector
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
                    print("[Beamsteering Protocol]: Exception; could not create parent directory for per sector logging.")
                    exit()
            
            self.log_per_sector_save_dir = log_per_sector_parent_dir
            self.log_per_sector_temp_dir = log_per_sector_parent_dir + "temp/"
            
            if not os.path.exists(self.log_per_sector_temp_dir):
                try:
                    os.makedirs(self.log_per_sector_temp_dir)
                except:
                    print("[Beamsteering Protocol]: Exception; could not create temp directory for per sector logging.")
                    exit()
            
        self.curr_sector_fname = ""
        self.curr_sector_fname_final_dest = ""
        self.last_tt_az_angle_received = 0.0
        self.last_tt_el_angle_received = 0.0
        self.tt_inv_timer = 0
        self.tt_run_no = 0 # starts from 1
        
        # Initial FSM call
        # Start timer to initially call the FSM to trigger the training process after random time
        random_frac_seconds = random.uniform(18.001, 19.010)
        if start_training == True:
            if self.beamsteering_algorithm == self.PLS_TX:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.PLS)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.SLS_TX:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.SLS)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.ITERATIVE_TX:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.iterative_search)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.SLS_TIMER_BASED:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.SLS_timer_based)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.PLS_TIMER_BASED:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.PLS_timer_based)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.ITERATIVE_TIMER_BASED:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.iterative_search_timer_based)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.HISTORY_SEARCH:
                self.trigger_timer = threading.Timer(random_frac_seconds, self.history_search)
                self.trigger_timer.start()
            elif self.beamsteering_algorithm == self.FIXED_BEAM_BACKUP_LINK:
                # do not wait for random amount of time. Make both initiator and responder start at the same instant.
                current_time = datetime.datetime.now()
                hour = current_time.hour
                minute = current_time.minute
                second = current_time.second
                start_hour = (hour + ((minute + 2) // 60)) % 24
                start_minute = (minute + 2) % 60
                print('Current time is: ', '{:02d}'.format(hour), ':', '{:02d}'.format(minute), ':', '{:02d}'.format(second))
                print('Starting time is: ', '{:02d}'.format(start_hour), ':', '{:02d}'.format(start_minute), ':', '00')
                while True:
                    current_time = datetime.datetime.now()
                    if current_time.hour == start_hour and current_time.minute == start_minute:
                        print('Time to start the communication!')
                        break
                    time.sleep(0.001)
                self.trigger_timer = threading.Timer(1.0, self.fixed_beam_backup_link_set_next_state)
                self.trigger_timer.start()

    def handle_phy_message(self, msg):
        # print 'Beamsteering Message received'
        with self.thread_lock:
            retrain = False
            # Process parameters in meta
            meta = pmt.car(msg)
            if pmt.is_dict(meta) == False:
                print("[Beamsteering Protocol]: ERROR: Received beamsteering meta is not a PMT dictionary!")
            if pmt.dict_has_key(meta, pmt.string_to_symbol("packet_type_MAC")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("packet_type_MAC"), pmt.PMT_NIL)
                packet_type_MAC = pmt.to_long(r)
            else:
                print("[Beamsteering Protocol]: ERROR: No Packet Type Tag received!")

            if pmt.dict_has_key(meta, pmt.string_to_symbol("evm")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("evm"), pmt.PMT_NIL)
                evm = pmt.to_double(r)
                self.last_rssi_received = int(
                    -1 * round(pmt.to_double(r)))  # RSSi is choosen to be the complement of the EVM
                # RSSI value received. If no RSSI value is received for a longer timer we assume that we have to retrain!
                # Start timer for this. Stop timer when RSSI value was received in time
                if self.my_station_type == self.INITIATOR and self.beamsteering_algorithm != self.FIXED_BEAM_BACKUP_LINK:
                    # do not do this if the algorithm is Fixed Beam with Backup Link
                    if self.timer_RSSI_value_interval != 0:
                        self.timer_RSSI_value_interval.cancel()
                        # print 'RSSI timer cancelled'
                    self.timer_RSSI_value_interval = threading.Timer(self.timeout_RSSI_value_interval,
                                                                     self.RSSI_timeout)
                    self.timer_RSSI_value_interval.start()

                if self.last_rssi_received < self.retrain_RSSI_threshold and packet_type_MAC == self.PACKET_TYPE_DATA:
                    # Start Retraining
                    print('[Beamsteering Protocol]: Retraining required')
                    retrain = True
                    self.rx_array_trained = False
                    self.tx_array_trained = False
                    # Send Mac parameter message to MAC
                    self.send_TX_antenna_array_requires_training_message()
                # else:
                # print('[Beamsteering Protocol]: Retraining not required')
            else:
                print("[Beamsteering Protocol]: ERROR: No EVM Tag received!")

            if pmt.dict_has_key(meta, pmt.string_to_symbol("preamble_rms")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("preamble_rms"), pmt.PMT_NIL)
                self.last_preamble_rms = pmt.to_double(r)
            if pmt.dict_has_key(meta, pmt.string_to_symbol("preamble_snr")):
                snr = pmt.dict_ref(meta, pmt.string_to_symbol("preamble_snr"), pmt.PMT_NIL)
                self.last_preamble_snr = pmt.to_double(snr)

            if pmt.dict_has_key(meta, pmt.string_to_symbol("preamble_rss")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("preamble_rss"), pmt.PMT_NIL)
                preamble_rss = pmt.to_double(r)

            if pmt.dict_has_key(meta, pmt.string_to_symbol("rx_beam_id")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("rx_beam_id"), pmt.PMT_NIL)
                rx_beam_id = pmt.to_double(r)

            if pmt.dict_has_key(meta, pmt.string_to_symbol("tt_az_angle")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("tt_az_angle"), pmt.PMT_NIL)
                tt_az_angle = pmt.to_double(r)
                #self.last_tt_az_angle_received = tt_az_angle

            if pmt.dict_has_key(meta, pmt.string_to_symbol("tt_el_angle")):
                r = pmt.dict_ref(meta, pmt.string_to_symbol("tt_el_angle"), pmt.PMT_NIL)
                tt_el_angle = pmt.to_double(r)
                #self.last_tt_el_angle_received = tt_el_angle

            payload = pmt.cdr(msg)
            if packet_type_MAC == self.PACKET_TYPE_BEAMSTEERING_MESSAGE and pmt.is_u8vector(payload) and len(
                    pmt.u8vector_elements(payload)) == 28:
                packet_type, direction, cdown, self.last_beam_ID_received, best_beam_feedback = self.decode_SSW_frame(
                    payload)  # last_beam_ID_received is the beam with which the received packet was transmitted from the partner station
                self.log_events(self.EVENT_RX, packet_type, direction, cdown, self.last_beam_ID_received,
                                best_beam_feedback, evm, self.last_rssi_received, self.last_preamble_rms,
                                self.last_preamble_snr, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle)
                self.forward_info_to_gui(self.last_beam_ID_received, rx_beam_id, self.best_initiator_pencil_beam, self.last_rssi_received, self.last_preamble_snr, preamble_rss)

                ######## PLS TX ##### PLS TX ####################################
                if self.beamsteering_algorithm == self.PLS_TX:
                    # Set states of PLS state machine according to the received packet type or restart training if RSSI is too low
                    print('PLS TX')
                    if retrain == True:
                        print('[Beamsteering Protocol]: Re-Training')
                        self.PLS_stop_wait_timer()
                        self.PLS_state = self.PLS_IDLE
                        self.PLS()  # Call PLS in IDLE mode which starts the training process since self.tx_array_trained = False
                    elif packet_type == self.TRN_PENCIL_SWEEP:
                        if direction != self.my_station_type and cdown >= 0:
                            self.PLS_state = self.PLS_RECEIVE_SSW_FRAMES
                            self.PLS()
                        else:
                            print('[Beamsteering Protocol]: ERROR: PLS SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SWEEP_FINISHED:
                        if direction != self.my_station_type:
                            self.PLS_stop_wait_timer()
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Pencil Beam', self.best_initiator_pencil_beam)
                            self.PLS_state = self.PLS_LAST_SSW_FRAME_RECEIVED
                            self.PLS()
                        else:
                            print('[Beamsteering Protocol]: ERROR: PLS Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.PLS_state = self.PLS_FEEDBACK_RECEIVED
                                self.best_responder_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Pencil Beam', self.best_responder_pencil_beam)
                                self.PLS()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: PLS SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: PLS Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.PLS_stop_wait_timer()
                                self.PLS_state = self.PLS_FEEDBACK_ACK_RECEIVED
                                self.PLS()
                            else:
                                print('[Beamsteering Protocol]: Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: PLS SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined PLS Packet Type! Setting PLS state to undefined. Packet Type: ', packet_type)
                        self.PLS_state = self.PLS_UNDEFINED
                        self.PLS()  # call PLS FSM
                ######## PLS TX_RX ##### PLS TX_RX ####################################
                elif self.beamsteering_algorithm == self.PLS_TX_RX:
                    print('PLS TX_RX')
                    return
                ######## PLS TX TIMER BASED ##### PLS TX TIMER BASED ####################################
                elif self.beamsteering_algorithm == self.PLS_TIMER_BASED:
                    # Set states of PLS state machine according to the received packet type or restart training if RSSI is too low
                    if retrain == True:
                        self.PLS_timer_based_stop_wait_timer()
                        self.PLS_timer_based_state = self.PLS_IDLE
                        self.PLS_timer_based()  # Call PLS in IDLE mode which starts the training process since self.tx_array_trained = False
                    elif packet_type == self.TRN_PENCIL_SWEEP:
                        if direction != self.my_station_type:
                            if cdown > 0:
                                self.PLS_timer_based_state = self.PLS_RECEIVE_SSW_FRAMES
                                self.PLS_timer_based()
                                if self.PLS_timer_receive_SSW_frames != 0:
                                    self.PLS_timer_receive_SSW_frames.cancel()
                                self.PLS_timer_receive_SSW_frames = threading.Timer(
                                    self.timeout_PLS_timer_based_receive_SSW_frames * cdown, self.PLS_timer_based)
                                self.PLS_timer_based_state = self.PLS_LAST_SSW_FRAME_RECEIVED
                                self.PLS_timer_receive_SSW_frames.start()
                            elif cdown == 0:
                                self.PLS_timer_based_state = self.PLS_RECEIVE_SSW_FRAMES
                                self.PLS_timer_based()
                                if self.PLS_timer_receive_SSW_frames != 0:
                                    self.PLS_timer_receive_SSW_frames.cancel()
                                self.PLS_timer_based_state = self.PLS_LAST_SSW_FRAME_RECEIVED
                                self.PLS_timer_based()
                            else:
                                print('[Beamsteering Protocol]: ERROR: SLS SSW Frame has wrong cdown value!')
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Pencil Beam', self.best_initiator_pencil_beam)
                        else:
                            print('[Beamsteering Protocol]: ERROR: PLS SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.PLS_timer_based_state = self.PLS_FEEDBACK_RECEIVED
                                self.best_responder_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Pencil Beam', self.best_responder_pencil_beam)
                                self.PLS_timer_based()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: PLS SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: PLS Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.PLS_timer_based_stop_wait_timer()
                                self.PLS_timer_based_state = self.PLS_FEEDBACK_ACK_RECEIVED
                                self.PLS_timer_based()
                            else:
                                print('[Beamsteering Protocol]: Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: PLS SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined PLS Packet Type! Setting PLS state to undefined. Packet Type: ', packet_type)
                        self.PLS_timer_based_state = self.PLS_UNDEFINED
                        self.PLS_timer_based()  # call PLS FSM
                ######## ITERATIVE_SEARCH TX ##### ITERATIVE_SEARCH TX ####################################
                elif self.beamsteering_algorithm == self.ITERATIVE_TX:
                    # Set states of SLS state machine according to the received packet type or restart training if RSSI is too low
                    print('ITERATIVE_SEARCH TX')
                    if retrain == True:
                        print('[Beamsteering Protocol]: Re-Training')
                        self.iterative_search_stop_wait_timer()
                        self.iterative_search_state = self.ITERATIVE_IDLE
                    elif packet_type == self.TRN_SECTOR_SWEEP:
                        if direction != self.my_station_type and cdown >= 0:
                            self.iterative_search_state = self.ITERATIVE_RECEIVE_SECTOR_SSW_FRAMES
                            self.iterative_search()
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Sector SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SWEEP:
                        if direction != self.my_station_type and cdown >= 0:
                            self.iterative_search_state = self.ITERATIVE_RECEIVE_PENCIL_SSW_FRAMES
                            self.iterative_search()
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Pencil SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SWEEP_FINISHED:
                        if direction != self.my_station_type:
                            self.iterative_search_stop_wait_timer()
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Sector Beam', self.best_initiator_sector_beam)
                            self.iterative_search_state = self.ITERATIVE_LAST_SECTOR_SSW_FRAME_RECEIVED
                            self.iterative_search()
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iiterative Search Sector Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SWEEP_FINISHED:
                        if direction != self.my_station_type:
                            self.iterative_search_stop_wait_timer()
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Pencil Beam', self.best_initiator_pencil_beam)
                            self.iterative_search_state = self.ITERATIVE_LAST_PENCIL_SSW_FRAME_RECEIVED
                            self.iterative_search()
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iiterative Search Sector Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.iterative_search_state = self.ITERATIVE_SECTOR_FEEDBACK_RECEIVED
                                self.best_responder_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Beam', self.best_responder_sector_beam)
                                self.iterative_search()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: Iterative Search Sector SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: Iterative Search Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.iterative_search_state = self.ITERATIVE_PENCIL_FEEDBACK_RECEIVED
                                self.best_responder_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Beam', self.best_responder_pencil_beam)
                                self.iterative_search()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: Iterative Search Pencil SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: Iterative Search Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.iterative_search_stop_wait_timer()
                                self.iterative_search_state = self.ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED
                                self.iterative_search()
                            else:
                                print('Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Sector SSW Feedback Frame has wrong direction or cdown value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.iterative_search_stop_wait_timer()
                                self.iterative_search_state = self.ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED
                                self.iterative_search()
                            else:
                                print('Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Pencil SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined Iterative Search Packet Type! Setting Iterative state to undefined. Packet Type: ', packet_type)
                        self.iterative_search_state = self.ITERATIVE_UNDEFINED
                        self.iterative_search()  # call iterative_search FSM
                ######## ITERATIVE_SEARCH Timer Based ##### ITERATIVE_SEARCH Timer Based ####################################
                elif self.beamsteering_algorithm == self.ITERATIVE_TIMER_BASED:
                    print('ITERATIVE_SEARCH Timer Based')
                    # Set states of SLS state machine according to the received packet type or restart training if RSSI is too low
                    if retrain == True:
                        print('[Beamsteering Protocol]: Re-Training')
                        self.iterative_search_timer_based_stop_wait_timer()
                        self.iterative_search_timer_based_state = self.ITERATIVE_IDLE
                    elif packet_type == self.TRN_SECTOR_SWEEP:
                        if direction != self.my_station_type:
                            if cdown > 0:
                                self.iterative_search_timer_based_state = self.ITERATIVE_RECEIVE_SECTOR_SSW_FRAMES
                                self.iterative_search_timer_based()
                                if self.iterative_search_timer_receive_SSW_frames != 0:
                                    self.iterative_search_timer_receive_SSW_frames.cancel()
                                self.iterative_search_timer_receive_SSW_frames = threading.Timer(
                                    self.timeout_iterative_search_timer_based_receive_SSW_frames * cdown,
                                    self.iterative_search_timer_based)
                                self.iterative_search_timer_based_state = self.ITERATIVE_LAST_SECTOR_SSW_FRAME_RECEIVED
                                self.iterative_search_timer_receive_SSW_frames.start()
                            elif cdown == 0:
                                self.iterative_search_timer_based_state = self.ITERATIVE_RECEIVE_SECTOR_SSW_FRAMES
                                self.iterative_search_timer_based()
                                if self.iterative_search_timer_receive_SSW_frames != 0:
                                    self.iterative_search_timer_receive_SSW_frames.cancel()
                                self.iterative_search_timer_based_state = self.ITERATIVE_LAST_SECTOR_SSW_FRAME_RECEIVED
                                self.iterative_search_timer_based()
                            else:
                                print('[Beamsteering Protocol]: ERROR: SLS SSW Frame has wrong cdown value!')
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Sector Beam', self.best_initiator_sector_beam)
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Sector SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SWEEP:
                        if direction != self.my_station_type:
                            if cdown > 0:
                                self.iterative_search_timer_based_state = self.ITERATIVE_RECEIVE_PENCIL_SSW_FRAMES
                                self.iterative_search_timer_based()
                                if self.iterative_search_timer_receive_SSW_frames != 0:
                                    self.iterative_search_timer_receive_SSW_frames.cancel()
                                self.iterative_search_timer_receive_SSW_frames = threading.Timer(
                                    self.timeout_iterative_search_timer_based_receive_SSW_frames * cdown,
                                    self.iterative_search_timer_based)
                                self.iterative_search_timer_based_state = self.ITERATIVE_LAST_PENCIL_SSW_FRAME_RECEIVED
                                self.iterative_search_timer_receive_SSW_frames.start()
                            elif cdown == 0:
                                self.iterative_search_timer_based_state = self.ITERATIVE_RECEIVE_PENCIL_SSW_FRAMES
                                self.iterative_search_timer_based()
                                if self.iterative_search_timer_receive_SSW_frames != 0:
                                    self.iterative_search_timer_receive_SSW_frames.cancel()
                                self.iterative_search_timer_based_state = self.ITERATIVE_LAST_PENCIL_SSW_FRAME_RECEIVED
                                self.iterative_search_timer_based()
                            else:
                                print('[Beamsteering Protocol]: ERROR: SLS SSW Frame has wrong cdown value!')
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Pencil Beam', self.best_initiator_pencil_beam)
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Pencil SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.iterative_search_timer_based_state = self.ITERATIVE_SECTOR_FEEDBACK_RECEIVED
                                self.best_responder_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Sector Beam', self.best_responder_sector_beam)
                                self.iterative_search_timer_based()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: Iterative Search Sector SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: Iterative Search Frame has wrong direction value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.iterative_search_timer_based_state = self.ITERATIVE_PENCIL_FEEDBACK_RECEIVED
                                self.best_responder_pencil_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Pencil Beam', self.best_responder_pencil_beam)
                                self.iterative_search_timer_based()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: Iterative Search Pencil SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: Iterative Search Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.iterative_search_timer_based_stop_wait_timer()
                                self.iterative_search_timer_based_state = self.ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED
                                self.iterative_search_timer_based()
                            else:
                                print('Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Sector SSW Feedback Frame has wrong direction or cdown value!')
                    elif packet_type == self.TRN_PENCIL_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.iterative_search_timer_based_stop_wait_timer()
                                self.iterative_search_timer_based_state = self.ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED
                                self.iterative_search_timer_based()
                            else:
                                print('Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: Iterative Search Pencil SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined Iterative Search Packet Type! Setting Iterative state to undefined. Packet Type: ', packet_type)
                        self.iterative_search_state = self.ITERATIVE_UNDEFINED
                        self.iterative_search()  # call iterative_search FSM
                ######## ITERATIVE_SEARCH TX_RX ##### ITERATIVE_SEARCH TX_RX ####################################
                elif self.beamsteering_algorithm == self.ITERATIVE_TX_RX:
                    print('ITERATIVE_SEARCH TX_RX')
                    return
                ######## EXHAUSTIVE_SEARCH ##### EXHAUSTIVE_SEARCH ####################################
                elif self.beamsteering_algorithm == self.EXHAUSTIVE_SEARCH:
                    print('EXHAUSTIVE_SEARCH')
                    # Set states of exhaustive search state machine according to the received packet type or restart training if RSSI is too low
                    if retrain == True:
                        self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_SEND_TRN_REQUEST
                    elif packet_type == self.TRN_REQUEST:
                        self.exhaustive_search = self.EXHAUSTIVE_SEARCH_TRN_REQUEST_RECEIVED
                    elif packet_type == self.TRN_REQUEST_ACK:
                        if direction == self.SSWtype and cdown == self.number_of_sectors:
                            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_TRN_REQUEST_ACK_RECEIVED
                        else:
                            print('[Beamsteering Protocol]: ERROR: EXHAUSTIVE_SEARCH TRN Request ACK wrong!')
                    elif packet_type == self.TRN_SECTOR_SWEEP:
                        if direction == self.SSWtype and cdown >= 0:
                            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_RECEIVE_SSW_FRAMES
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: EXHAUSTIVE_SEARCH SSW Frame has wrong direction or cdown value!')
                    elif packet_type == self.TRN_SECTOR_SWEEP_FINISHED:
                        if direction == self.SSWtype and cdown == 0:
                            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_SEND_FEEDBACK
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: EXHAUSTIVE_SEARCH SSW Finished Frame has wrong direction or cdown value!')
                    elif packet_type == self.TRN_SSW_FEEDBACK:
                        if direction == self.SSWtype and cdown == 0:
                            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_FEEDBACK_RECEIVED
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: EXHAUSTIVE_SEARCH SSW Feedback Frame has wrong direction or cdown value!')
                    elif packet_type == self.TRN_SSW_FEEDBACK_ACK:
                        if direction == self.SSWtype and cdown == 0 and self.last_beam_ID_received == self.best_beam:
                            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_FEEDBACK_ACK_RECEIVED
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: EXHAUSTIVE_SEARCH SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print(
                            '[Beamsteering Protocol]: ERROR: Undefined EXHAUSTIVE_SEARCH Packet Type! Setting EXHAUSTIVE_SEARCH state to Undefined (=waiting)')
                        self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_UNDEFINED
                    self.exhaustive_search()  # call FSM
                ######## SLS TX ##### SLS TX ####################################
                elif self.beamsteering_algorithm == self.SLS_TX:
                    print('SLS TX')
                    # Set states of SLS state machine according to the received packet type or restart training if RSSI is too low
                    if retrain == True:
                        print('[Beamsteering Protocol]: Re-Training')
                        self.SLS_stop_wait_timer()
                        self.SLS_state = self.SLS_IDLE
                        self.SLS()  # Call SLS in IDLE mode which starts the training process since self.tx_array_trained = False
                    # elif packet_type == self.TRN_REQUEST:
                    #     #if direction == self.INITIATOR and self.my_station_type == self.INITIATOR:
                    #         #self.my_station_type = self.RESPONDER
                    #     if direction != self.my_station_type:
                    #         self.SLS_state = self.SLS_TRN_REQUEST_RECEIVED
                    #         self.SLS()
                    #     else:
                    #         print('[Beamsteering Protocol]: ERROR: SLS TRN REQUEST Frame has wrong direction value!')
                    # elif packet_type == self.TRN_REQUEST_ACK:
                    #     if direction != self.my_station_type:
                    #         self.SLS_stop_wait_timer()
                    #         self.SLS_state = self.SLS_TRN_REQUEST_ACK_RECEIVED
                    #         self.SLS()
                    #     else:
                    #         print('[Beamsteering Protocol]: ERROR: SLS TRN REQUEST ACK Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SWEEP:
                        if direction != self.my_station_type and cdown >= 0:
                            self.SLS_state = self.SLS_RECEIVE_SSW_FRAMES
                            self.SLS()
                        else:
                            print('[Beamsteering Protocol]: ERROR: SLS SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SWEEP_FINISHED:
                        if direction != self.my_station_type:
                            self.SLS_stop_wait_timer()
                            if self.my_station_type == self.INITIATOR:
                                self.best_initiator_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Sector Beam', self.best_initiator_sector_beam)
                            self.SLS_state = self.SLS_LAST_SSW_FRAME_RECEIVED
                            self.SLS()
                        else:
                            print('[Beamsteering Protocol]: ERROR: SLS Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.SLS_state = self.SLS_FEEDBACK_RECEIVED
                                self.best_responder_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Sector Beam', self.best_responder_sector_beam)
                                self.SLS()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: SLS SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: SLS Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.SLS_stop_wait_timer()
                                self.SLS_state = self.SLS_FEEDBACK_ACK_RECEIVED
                                self.SLS()
                            else:
                                print('Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: SLS SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined SLS Packet Type! Setting SLS state to undefined. Packet Type: ', packet_type)
                        self.SLS_state = self.SLS_UNDEFINED
                        self.SLS()  # call SLS FSM
                ######## SLS Timer Based ##### SLS Timer Based ####################################
                elif self.beamsteering_algorithm == self.SLS_TIMER_BASED:
                    print('SLS Timer Based')
                    # Set states of SLS state machine according to the received packet type or restart training if RSSI is too low
                    if retrain == True:
                        self.SLS_timer_based_stop_wait_timer()
                        self.SLS_timer_based_state = self.SLS_IDLE
                        print('[Beamsteering Protocol]: Re-Training')
                        self.SLS_timer_based()  # Call SLS in IDLE mode which starts the training process since self.tx_array_trained = False
                    elif packet_type == self.TRN_SECTOR_SWEEP:
                        if direction != self.my_station_type:
                            if cdown > 0:
                                self.SLS_timer_based_state = self.SLS_RECEIVE_SSW_FRAMES
                                self.SLS_timer_based()
                                if self.SLS_timer_receive_SSW_frames != 0:
                                    self.SLS_timer_receive_SSW_frames.cancel()
                                self.SLS_timer_receive_SSW_frames = threading.Timer(
                                    self.timeout_SLS_timer_based_receive_SSW_frames * cdown, self.SLS_timer_based)
                                self.SLS_timer_based_state = self.SLS_LAST_SSW_FRAME_RECEIVED
                                self.SLS_timer_receive_SSW_frames.start()
                            elif cdown == 0:
                                self.SLS_timer_based_state = self.SLS_RECEIVE_SSW_FRAMES
                                self.SLS_timer_based()
                                if self.SLS_timer_receive_SSW_frames != 0:
                                    self.SLS_timer_receive_SSW_frames.cancel()
                                self.SLS_timer_based_state = self.SLS_LAST_SSW_FRAME_RECEIVED
                                self.SLS_timer_based()
                            else:
                                print('[Beamsteering Protocol]: ERROR: SLS SSW Frame has wrong cdown value!')
                            if self.my_station_type == self.INITIATOR:
                                self.SLS_timer_based_stop_wait_timer()
                                self.best_initiator_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Initiator Sector Beam', self.best_initiator_sector_beam)
                        else:
                            print('[Beamsteering Protocol]: ERROR: SLS SSW Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK:
                        if direction != self.my_station_type:
                            if direction == self.INITIATOR and cdown == 0:
                                self.SLS_timer_based_state = self.SLS_FEEDBACK_RECEIVED
                                self.best_responder_sector_beam = best_beam_feedback
                                print('[Beamsteering Protocol]: Best Responder Sector Beam', self.best_responder_sector_beam)
                                self.SLS_timer_based()
                            elif direction == self.RESPONDER and cdown == 0:
                                print('[Beamsteering Protocol]: ERROR: Wrong state!')
                            else:
                                print(
                                    '[Beamsteering Protocol]: ERROR: SLS SSW Feedback Frame has wrong direction or cdown value!')
                        else:
                            print('[Beamsteering Protocol]: ERROR: SLS Frame has wrong direction value!')
                    elif packet_type == self.TRN_SECTOR_SSW_FEEDBACK_ACK:
                        if direction != self.my_station_type and cdown == 0:
                            if direction == self.RESPONDER:
                                self.SLS_timer_based_stop_wait_timer()
                                self.SLS_timer_based_state = self.SLS_FEEDBACK_ACK_RECEIVED
                                self.SLS_timer_based()
                            else:
                                print('[Beamsteering Protocol]: Logical Error')
                        else:
                            print(
                                '[Beamsteering Protocol]: ERROR: SLS SSW Feedback Frame has wrong direction or cdown value!')
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined SLS Timer Based Packet Type! Setting SLS state to undefined. Packet Type: ', packet_type)
                        self.SLS_timer_based_state = self.SLS_UNDEFINED
                        self.SLS_timer_based()  # call SLS FSM
                ######## History Search Timer Based ##### HISTORY Search Timer Based ####################################
                elif self.beamsteering_algorithm == self.HISTORY_SEARCH:
                    print('History Search: Not finally implemented')
                    return
                ######## Fixed Beam with Backup Link ##### Fixed Beam with Backup Link ###################################
                elif self.beamsteering_algorithm == self.FIXED_BEAM_BACKUP_LINK:
                    if packet_type == self.TRN_FIXED_BEAM_BACKUP_LINK_SWITCH_BACKUP:
                        print('Fixed Beam with Backup Link: Message received: switch to backup link')
                        if direction != self.my_station_type: # should have come from the responder
                            if direction == self.RESPONDER:
                                # if not already in the backup beam, send message to SPI manager to switch
                                if self.tx_beam_ID != self.fixed_beam_backup_link_backup_beam_id:
                                    pmt_to_send = pmt.from_long(self.fixed_beam_backup_link_backup_beam_id)
                                    self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
                                    self.tx_beam_ID = self.fixed_beam_backup_link_backup_beam_id
                                    self.rx_beam_ID = self.fixed_beam_backup_link_backup_beam_id
                                # else: # no further action needed
                                self.fixed_beam_backup_link() # go back to the state machine
                            else: # INITIATOR
                                print('[Beamsteering Protocol]: ERROR: Initiator does not send link switch messages (in this implementation).')
                        else:
                            print('[Beamsteering Protocol]: ERROR: Link Switch Frame has wrong direction value!')
                    elif packet_type == self.TRN_FIXED_BEAM_BACKUP_LINK_SWITCH_DEFAULT:
                        print('Fixed Beam with Backup Link: Message received: switch to default link')
                        if direction != self.my_station_type: # most probably came from the responder
                            if direction == self.RESPONDER:
                                # if not already in the default beam, send message to SPI manager to switch
                                if self.tx_beam_ID != self.fixed_beam_backup_link_default_beam_id:
                                    pmt_to_send = pmt.from_long(self.fixed_beam_backup_link_default_beam_id)
                                    self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
                                    self.tx_beam_ID = self.fixed_beam_backup_link_default_beam_id
                                    self.rx_beam_ID = self.fixed_beam_backup_link_default_beam_id
                                # else: # no further action needed
                                self.fixed_beam_backup_link() # go back to the state machine
                            else: # INITIATOR
                                print('[Beamsteering Protocol]: ERROR: Initiator does not send link switch messages (in this implementation).')
                        else:
                            print('[Beamsteering Protocol]: ERROR: Link Switch Frame has wrong direction value!')
                    elif packet_type == self.TRN_FIXED_BEAM_BACKUP_LINK_DATA_BURST:
                        if direction != self.my_station_type: # should have come from the initiator
                            if direction == self.INITIATOR:
                                # just process the packet and pass it to the other blocks
                                pass     
                    else:
                        print('[Beamsteering Protocol]: ERROR: Undefined Link Switch Packet Type! Discarding packet.')   
                
                else:
                    print('[Beamsteering Protocol]: Algorithm/Protocol not defined')
            # else: Data Packets for RSSI / EVM value evaluation not further evaluated
            # print('[Beamsteering Protocol]: PHY message not readable')

    def RSSI_timeout(self):
        with self.thread_lock:
            print('[Beamsteering Protocol]: RSSI timeout')
            self.log_events('RSSI_timeout', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-')
            self.rx_array_trained = False
            self.tx_array_trained = False
            if self.timer_SLS_timer_based != 0:
                self.timer_SLS_timer_based.cancel()
            if self.SLS_timer_receive_SSW_frames != 0:
                self.SLS_timer_receive_SSW_frames.cancel()
            # Send Mac parameter message to MAC
            self.send_TX_antenna_array_requires_training_message()
            if self.my_station_type == self.INITIATOR:
                if self.beamsteering_algorithm == self.PLS_TX:
                    self.PLS_state = self.PLS_IDLE
                    self.PLS()
                elif self.beamsteering_algorithm == self.PLS_TIMER_BASED:
                    self.PLS_timer_based_state = self.PLS_IDLE
                    self.PLS_timer_based()
                elif self.beamsteering_algorithm == self.SLS_TIMER_BASED:
                    self.SLS_timer_based_state = self.SLS_IDLE
                    self.SLS_timer_based()
                elif self.beamsteering_algorithm == self.SLS_TX:
                    self.SLS_state = self.SLS_IDLE
                    self.SLS()
                elif self.beamsteering_algorithm == self.ITERATIVE_TX:
                    self.iterative_search_state = self.ITERATIVE_IDLE
                    self.iterative_search()
                elif self.beamsteering_algorithm == self.ITERATIVE_TIMER_BASED:
                    self.iterative_search_timer_based_state = self.ITERATIVE_IDLE
                    self.iterative_search_timer_based()
                else:
                    print('[Beamsteering Protocol]: Algorithm/Protocol not defined')

    def get_bit(self, byte, index):
        if byte & (1 << index):
            return 1
        else:
            return 0

    def get_byte(self, bits, last_index):
        byte = 0
        for i in range(last_index):
            byte |= (bits[i] & 1) << i
        return byte

    def generate_SSW_frame(self, packet_type, direction, cdown, beam_ID, best_beam_feedback):
        # Sector Sweep (SSW) field according to IEEE 802.11ad:
        # 24 Bits
        # Bit 0: Direction: The Direction field is set to 0 to indicate that the frame is transmitted by the beamforming initiator and set to 1 to indicate that the frame is transmitted by the beamforming responder.
        # Bit 1-9: CDOWN: The CDOWN field is a down-counter indicating the number of remaining SSW frame transmissions to the end of the TXSS/RXSS. This field is set to 0 in the SSW frame transmission.
        # Bit 10-15: Beam ID: The Beam ID field is set to indicate the beam number through which the frame containing this SSW field is transmitted.
        # Bit 16-17: DMG Antenna ID: Not used here
        # Bit 18-23: RXSS Length: Not used here
        # Customization: 4 Bits for packet type added here at the front
        # + 6 bits at the end for best beam eedback during responder SSW and initiator feedback
        ssw_frame = []
        ssw_frame.append(self.get_bit(packet_type, 0))
        ssw_frame.append(self.get_bit(packet_type, 1))
        ssw_frame.append(self.get_bit(packet_type, 2))
        ssw_frame.append(self.get_bit(packet_type, 3))
        ssw_frame.append(self.get_bit(direction, 0))
        ssw_frame.append(self.get_bit(cdown, 0))
        ssw_frame.append(self.get_bit(cdown, 1))
        ssw_frame.append(self.get_bit(cdown, 2))
        ssw_frame.append(self.get_bit(cdown, 3))
        ssw_frame.append(self.get_bit(cdown, 4))
        ssw_frame.append(self.get_bit(cdown, 5))
        ssw_frame.append(self.get_bit(cdown, 6))
        ssw_frame.append(self.get_bit(cdown, 7))
        ssw_frame.append(self.get_bit(cdown, 8))
        ssw_frame.append(self.get_bit(beam_ID, 0))
        ssw_frame.append(self.get_bit(beam_ID, 1))
        ssw_frame.append(self.get_bit(beam_ID, 2))
        ssw_frame.append(self.get_bit(beam_ID, 3))
        ssw_frame.append(self.get_bit(beam_ID, 4))
        ssw_frame.append(self.get_bit(beam_ID, 5))
        ssw_frame.append(self.get_bit(beam_ID, 6))
        ssw_frame.append(self.get_bit(best_beam_feedback, 0))
        ssw_frame.append(self.get_bit(best_beam_feedback, 1))
        ssw_frame.append(self.get_bit(best_beam_feedback, 2))
        ssw_frame.append(self.get_bit(best_beam_feedback, 3))
        ssw_frame.append(self.get_bit(best_beam_feedback, 4))
        ssw_frame.append(self.get_bit(best_beam_feedback, 5))
        ssw_frame.append(self.get_bit(best_beam_feedback, 6))
        ssw_frame_pmt = pmt.make_u8vector(len(ssw_frame), 0)
        for i in range(len(ssw_frame)):
            pmt.u8vector_set(ssw_frame_pmt, i, ssw_frame[i])
        return ssw_frame_pmt

    def decode_SSW_frame(self, payload_pmt):
        payload = pmt.u8vector_elements(payload_pmt)
        packet_type = self.get_byte(payload[0:5], 4)
        direction = payload[4]
        cdown = self.get_byte(payload[5:14], 8)
        beam_ID = self.get_byte(payload[14:21], 6)
        best_beam_feedback = self.get_byte(payload[21:28], 6)
        return packet_type, direction, cdown, beam_ID, best_beam_feedback

    def send_from_queue(self):
        with self.thread_lock:
            while self.packet_queue.empty() == False:
                pmt_to_send = self.packet_queue.get()
                payload = pmt.cdr(pmt_to_send)
                if pmt.is_u8vector(payload) and len(pmt.u8vector_elements(payload)) == 28:
                    packet_type, direction, cdown, TX_beam_used, best_beam_feedback = self.decode_SSW_frame(payload)
                    self.log_events(self.EVENT_TX, packet_type, direction, cdown, TX_beam_used, best_beam_feedback, '-',
                                    '-', '-', '-', '-', '-', '-', '-')
                self.message_port_pub(pmt.intern('out'), pmt_to_send)
                self.forward_info_to_gui(TX_beam_used)
        self.ready.set()
        # if self.my_station_type == self.INITIATOR:
        # if self.timer_RSSI_value_interval != 0:
        #   self.timer_RSSI_value_interval.cancel()
        # print 'RSSI timer started'
        # print 'message sent to MAC'

    def exhaustive_search(self):
        # FSM for Exhaustive Search
        # For exhaustive search we assume that a station uses the same beam for TX and RX

        ### General States
        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined exhaustive search state!')
            return 0

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE:
            # Waiting for next beamsteering protocol message
            # If nothing is received within a timeout repeat last state
            # start timer
            current_time = time.time()
            if (current_time - self.last_tx_time) > self.timeout:
                self.exhaustive_search_state = self.last_state
                print('[Beamsteering Protocol]: WARNING: Timeout - Repeating last state.')

        ### Initiator Station States
        # Currently both stations will start with sending a TRN Request
        # First come, first serve!
        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_IDLE:
            self.last_state = self.EXHAUSTIVE_SEARCH_IDLE
            if self.tx_array_trained == False:
                self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_SEND_TRN_REQUEST
                self.exhaustive_pencil_iter = 0
                self.exhasutive_search_request_ACK_received = False
            else:
                return

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_SEND_TRN_REQUEST:  # Include the beam which the responder should use for ACK
            self.last_state = self.EXHAUSTIVE_SEARCH_SEND_TRN_REQUEST
            # Start with TRN Request from Initiator to Responder Station
            trn_request_payload = self.generate_SSW_frame(self.TRN_REQUEST, self.SSWtype, self.number_of_pencils,
                                                          self.pencil_IDs(
                                                              self.exhaustive_pencil_iter))  # use last field (beam ID) to tell the responder which beam to use for the TRN_Request_ACK
            if self.exhaustive_pencil_iter < self.number_of_pencils:
                self.exhaustive_pencil_iter += 1  # Increase iterator
            elif self.exhaustive_pencil_iter == self.number_of_pencils and self.exhaustive_search_request_ACK_received == True:
                # At least one ACK has been received so we can jump to feedback state
                self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_SEND_FEEDBACK
            else:
                # All possible responder beams tested and no ACK received -> start again with training
                self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_SEND_TRN_REQUEST
            # Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(1))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_request = pmt.cons(meta, trn_request_payload)
            self.message_port_pub(pmt.intern('out'), TRN_request)
            self.last_tx_time = time.time()
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Set next state
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_TRN_REQUEST_ACK_RECEIVED:
            self.last_state = self.EXHAUSTIVE_SEARCH_TRN_REQUEST_ACK_RECEIVED
            # Correct SLS_TRN_REQUEST is received -> Sector sweep can start
            self.exhaustive_search_request_ACK_received = True
            self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_SWEEP

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_SWEEP:
            self.last_state = self.EXHAUSTIVE_SEARCH_SWEEP
            # Create SSW frames for every sector and send them to the MAC protocol
            for i in range(len(self.pencil_IDs)):
                curr_pencil_ID = self.pencil_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_pencil_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.PENCIL_RF_GAIN))  # Use sector RF gain
                trn_sector_sweep_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP, self.SSWtype,
                                                                   self.number_of_pencils - 1 - i, curr_pencil_ID)
                self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_sector_sweep_payload))
            # Send Sector Sweep Finished Message via Quasi-omni beam
            trn_sector_sweep_finished_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP_FINISHED, self.SSWtype, 0,
                                                                        self.quasiomni_ID)
            # Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_request = pmt.cons(meta, trn_request_payload)
            self.message_port_pub(pmt.intern('out'), TRN_request)
            self.last_tx_time = time.time()
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_FEEDBACK_RECEIVED:
            self.last_state = self.EXHAUSTIVE_SEARCH_FEEDBACK_RECEIVED
            # Set Parameters
            self.tx_beam_ID = self.last_beam_ID_received
            self.tx_array_trained = True
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            # Send MAC control message
            send_TX_antenna_array_trained_message()

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_SSW_FEEDBACK_ACK, self.SSWtype, 0,
                                                                   self.last_beam_ID_received)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"),
                                pmt.from_long(self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_request_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.message_port_pub(pmt.intern('out'), TRN_request_ack)
            self.last_tx_time = time.time()

            # EXHAUSTIVE_SEARCH complete got back to state IDLE
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_IDLE

        ### Responder Station States
        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_TRN_REQUEST_RECEIVED:  # State at Responder Station
            self.last_state = self.EXHAUSTIVE_SEARCH_TRN_REQUEST_RECEIVED
            # TRN Request message received. Confirm reception with ACK and set state to receive SSW frames
            trn_request_ack_payload = self.generate_SSW_frame(self.TRN_REQUEST_ACK, self.SSWtype,
                                                              self.number_of_sectors, self.quasiomni_ID)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_request_ack = pmt.cons(meta, trn_request_ack_payload)
            self.message_port_pub(pmt.intern('out'), TRN_request_ack)
            self.last_tx_time = time.time()
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_RECEIVE_SSW_FRAMES:
            self.last_state = self.EXHAUSTIVE_SEARCH_RECEIVE_SSW_FRAMES
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_SEND_FEEDBACK:
            self.last_state = self.EXHAUSTIVE_SEARCH_SEND_FEEDBACK
            # EXHAUSTIVE_SEARCH sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID

            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: EXHAUSTIVE_SEARCH Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.SECTOR_RF_GAIN

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_SSW_FEEDBACK, self.SSWtype, 0, self.best_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.last_tx_time = time.time()
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_WAITFORNEXTRESPONSE

        if self.exhaustive_search_state == self.EXHAUSTIVE_SEARCH_FEEDBACK_ACK_RECEIVED:
            self.last_state = self.EXHAUSTIVE_SEARCH_FEEDBACK_ACK_RECEIVED
            # EXHAUSTIVE_SEARCH complete -> go back to state IDLE to start Responder TXSS if not already executed
            self.exhaustive_search_state = self.EXHAUSTIVE_SEARCH_IDLE
            self.SSWtype = self.RESPONDER_SSW

        # When Responder receives the sweep complete message, return the Request ack directly from the next pencil responder beam
        # Remember to create a table of all combinations and rssi values
        # Full Feedback is returned at the complete end (when no responder beam is left)

        # First Request by sending the responder station the number of beams to test
        # Make sure at responder to take the right (the received) beam ID for sending the ACK
        return 0

    def SLS_timer_based_wait_for_next_response(self, state):
        with self.thread_lock:
            # print 'Wait for next response'
            if self.timer_SLS_timer_based != 0:
                self.timer_SLS_timer_based.cancel()
            if state == self.SLS_SWEEP:
                self.timer_SLS_timer_based = threading.Timer(self.timeout_SLS_timer_based * (self.number_of_sectors),
                                                             self.SLS_timer_based_wait_for_next_response_timeout)
                self.timer_SLS_timer_based.start()
            elif state == self.SLS_SEND_FEEDBACK:
                if self.retransmit_counter < 2:
                    self.timer_SLS_timer_based = threading.Timer(self.timeout_SLS_timer_based,
                                                                 self.SLS_timer_based_wait_for_next_response_timeout)
                    self.timer_SLS_timer_based.start()
                    self.retransmit_counter += 1
                else:
                    self.retransmit_counter = 0
                    self.SLS_timer_based_state = self.SLS_IDLE
                    self.SLS_timer_based()

    def SLS_timer_based_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_SLS_timer_based != 0:
                self.timer_SLS_timer_based.cancel()
            self.retransmit_counter = 0

    def SLS_timer_based_wait_for_next_response_timeout(self):
        with self.thread_lock:
            print('[Beamsteering Protocol]: SLS (TB) Timer Timeout')
            self.SLS_timer_based_state = self.last_state
            self.SLS_timer_based()

    def SLS_timer_based(self):
        # print('SLS_timer_based called')
        # FSM for SLS phase based on one-sided quasi-omni beam links

        ### General States
        if self.SLS_timer_based_state == self.SLS_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined SLS state!')
            self.SLS_timer_based_state == self.SLS_IDLE
            self.last_state = self.SLS_IDLE
            self.tx_array_trained = False

        if self.SLS_timer_based_state == self.SLS_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: SLS_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_sector_beam, self.SECTOR_RF_GAIN)
            self.tx_RF_gain = self.SECTOR_RF_GAIN
            self.last_state = self.SLS_FEEDBACK_ACK_RECEIVED
            self.SLS_timer_based_state = self.SLS_IDLE

        if self.SLS_timer_based_state == self.SLS_LAST_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: SLS LAST SSW FRAME')
            # SLS sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: SLS Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.SECTOR_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Sector Beam: ', self.best_responder_sector_beam)
                self.SLS_timer_based_state = self.SLS_SEND_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Sector Beam: ', self.best_initiator_sector_beam)
                self.SLS_timer_based_state = self.SLS_SWEEP

        if self.SLS_timer_based_state == self.SLS_FEEDBACK_RECEIVED:
            # print('[Beamsteering Protocol]: SLS FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.SECTOR_RF_GAIN
            self.tx_beam_ID = self.best_responder_sector_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_sector_beam,
                                                                   self.best_initiator_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # SLS complete got back to state IDLE
            self.SLS_timer_based_state = self.SLS_IDLE

        if self.SLS_timer_based_state == self.SLS_RECEIVE_SSW_FRAMES:
            # print('[Beamsteering Protocol]: SLS SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.SLS_timer_based_state == self.SLS_SEND_FEEDBACK:
            print('[Beamsteering Protocol]: SEND SLS FEEDBACK')
            self.last_state = self.SLS_SEND_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_sector_beam, self.best_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.SLS_timer_based_wait_for_next_response(self.SLS_SEND_FEEDBACK)

        if self.SLS_timer_based_state == self.SLS_IDLE:
            # print('[Beamsteering Protocol]: SLS IDLE')
            self.last_state = self.SLS_IDLE
            if self.tx_array_trained == False:
                # print('[Beamsteering Protocol]: SLS IDLE - not trained')
                if self.my_station_type == self.INITIATOR:
                    self.SLS_timer_based_state = self.SLS_SWEEP
            else:
                # print('[Beamsteering Protocol]: SLS IDLE - trained')
                return

        if self.SLS_timer_based_state == self.SLS_SWEEP:
            # print('[Beamsteering Protocol]: SLS SWEEP')
            self.last_state = self.SLS_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every sector and send them to the MAC protocol
            for i in range(len(self.sector_IDs)):
                curr_sector_ID = self.sector_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_sector_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                trn_sector_sweep_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP, self.my_station_type,
                                                                   self.number_of_sectors - 1 - i, curr_sector_ID,
                                                                   self.best_initiator_sector_beam)
                pmt_to_send = pmt.cons(meta, trn_sector_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                # self.ready.wait()
                time.sleep(0.065)
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.SLS_timer_based_wait_for_next_response(self.SLS_SWEEP)

    def iterative_search_wait_for_next_response(self, state):
        # print 'Wait for next response'
        if self.timer_iterative_search != 0:
            self.timer_iterative_search.cancel()
        if state == self.ITERATIVE_SECTOR_SWEEP:
            self.timer_iterative_search = threading.Timer(self.timeout_iterative_search * (self.number_of_sectors),
                                                          self.iterative_search_wait_for_next_response_timeout)
            self.timer_iterative_search.start()
        if state == self.ITERATIVE_PENCIL_SWEEP:
            if self.retransmit_counter < 2:
                self.timer_iterative_search = threading.Timer(self.timeout_iterative_search * (6),
                                                              self.iterative_search_wait_for_next_response_timeout)
                self.timer_iterative_search.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.iterative_search_state = self.ITERATIVE_IDLE
                self.iterative_search()
        elif state == self.ITERATIVE_SEND_SECTOR_FEEDBACK or state == self.ITERATIVE_SEND_PENCIL_FEEDBACK:
            if self.retransmit_counter < 2:
                self.timer_iterative_search = threading.Timer(self.timeout_iterative_search,
                                                              self.iterative_search_wait_for_next_response_timeout)
                self.timer_iterative_search.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.iterative_search_state = self.ITERATIVE_IDLE
                self.iterative_search()

    def iterative_search_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_iterative_search != 0:
                self.timer_iterative_search.cancel()
            self.retransmit_counter = 0

    def iterative_search_wait_for_next_response_timeout(self):
        # with self.thread_lock:
        print('[Beamsteering Protocol]: Iterative Search Timer Timeout')
        self.iterative_search_state = self.last_state
        self.iterative_search()

    def iterative_search(self):
        ### General States
        if self.iterative_search_state == self.ITERATIVE_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined ITERATIVE state!')
            return 0

        if self.iterative_search_state == self.ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE_SECTOR_FEEDBACK_ACK RECEIVED')
            self.last_state = self.ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED
            self.iterative_search_state = self.ITERATIVE_PENCIL_SWEEP

        if self.iterative_search_state == self.ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE_PENCIL_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_pencil_beam, self.PENCIL_RF_GAIN)
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.last_state = self.ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED
            self.iterative_search_state = self.ITERATIVE_IDLE

        if self.iterative_search_state == self.ITERATIVE_LAST_SECTOR_SSW_FRAME_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE LAST SECTOR SSW FRAME')
            # Iterative sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: ITERATIVE Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.SECTOR_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Sector Beam: ', self.best_responder_sector_beam)
                self.iterative_search_state = self.ITERATIVE_SEND_SECTOR_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Sector Beam: ', self.best_initiator_sector_beam)
                self.iterative_search_state = self.ITERATIVE_SECTOR_SWEEP

        if self.iterative_search_state == self.ITERATIVE_LAST_PENCIL_SSW_FRAME_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE LAST PENCIL SSW FRAME')
            # Iterative sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: ITERATIVE Best Pencil Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.PENCIL_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Pencil Beam: ', self.best_responder_pencil_beam)
                self.iterative_search_state = self.ITERATIVE_SEND_PENCIL_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Pencil Beam: ', self.best_initiator_sector_beam)
                self.iterative_search_state = self.ITERATIVE_PENCIL_SWEEP

        if self.iterative_search_state == self.ITERATIVE_SECTOR_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE SECTOR FEEDBACK RECEIVED')

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_sector_beam,
                                                                   self.best_initiator_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # SECTOR SLS complete

        if self.iterative_search_state == self.ITERATIVE_PENCIL_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE PENCIL FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.tx_beam_ID = self.best_responder_pencil_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_pencil_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_pencil_beam,
                                                                   self.best_initiator_pencil_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_feedback_ack)

            # SLS complete got back to state IDLE
            self.iterative_search_state = self.ITERATIVE_IDLE

        if self.iterative_search_state == self.ITERATIVE_RECEIVE_SECTOR_SSW_FRAMES:
            print('[Beamsteering Protocol]: SECTOR SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.iterative_search_state == self.ITERATIVE_RECEIVE_PENCIL_SSW_FRAMES:
            print('[Beamsteering Protocol]: PENCIL SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.iterative_search_state == self.ITERATIVE_SEND_SECTOR_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND ITERATIVE SECTOR SLS FEEDBACK')
            self.last_state = self.ITERATIVE_SEND_SECTOR_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_sector_beam,
                                                               self.best_responder_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.iterative_search_wait_for_next_response(self.ITERATIVE_SEND_SECTOR_FEEDBACK)

        if self.iterative_search_state == self.ITERATIVE_SEND_PENCIL_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND ITERATIVE PENCIL SLS FEEDBACK')
            self.last_state = self.ITERATIVE_SEND_PENCIL_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_pencil_beam,
                                                               self.best_responder_pencil_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.iterative_search_wait_for_next_response(self.ITERATIVE_SEND_PENCIL_FEEDBACK)

        if self.iterative_search_state == self.ITERATIVE_IDLE:
            # print('[Beamsteering Protocol]: ITERATIVE IDLE')
            self.last_state = self.ITERATIVE_IDLE
            if self.tx_array_trained == False:
                if self.my_station_type == self.INITIATOR:
                    # print('[Beamsteering Protocol]: ITERATIVE IDLE - not trained')
                    self.iterative_search_state = self.ITERATIVE_SECTOR_SWEEP
            else:
                # print('[Beamsteering Protocol]: ITERATIVE IDLE - trained')
                return

        if self.iterative_search_state == self.ITERATIVE_SECTOR_SWEEP:
            print('[Beamsteering Protocol]: ITERATIVE SECTOR SWEEP')
            self.last_state = self.ITERATIVE_SECTOR_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every sector and send them to the MAC protocol
            for i in range(len(self.sector_IDs)):
                curr_sector_ID = self.sector_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_sector_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                trn_sector_sweep_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP, self.my_station_type,
                                                                   self.number_of_sectors - 1 - i, curr_sector_ID, 0)
                pmt_to_send = pmt.cons(meta, trn_sector_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                # self.ready.wait()
                time.sleep(0.06)
            # Send Sector Sweep Finished Message via Quasi-omni beam
            trn_sector_sweep_finished_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP_FINISHED,
                                                                        self.my_station_type, 0, self.quasiomni_ID,
                                                                        self.best_initiator_sector_beam)
            # Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_SSW_finished = pmt.cons(meta, trn_sector_sweep_finished_payload)
            self.packet_queue.put(TRN_SSW_finished)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.iterative_search_wait_for_next_response(self.ITERATIVE_SECTOR_SWEEP)

        if self.iterative_search_state == self.ITERATIVE_PENCIL_SWEEP:
            print('[Beamsteering Protocol]: ITERATIVE PENCIL SWEEP')
            self.last_state = self.ITERATIVE_PENCIL_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Find Pencil beam in best sector
            if self.my_station_type == self.INITIATOR:
                if self.best_initiator_sector_beam >= 45 and self.best_initiator_sector_beam <= 57:
                    in_sector_pencil_IDs = self.SECTOR_TO_PENCIL_MAPPING[self.best_initiator_sector_beam - 45]
                else:
                    in_sector_pencil_IDs = self.pencil_IDs
            elif self.my_station_type == self.RESPONDER:
                if self.best_responder_sector_beam >= 45 and self.best_responder_sector_beam <= 57:
                    in_sector_pencil_IDs = self.SECTOR_TO_PENCIL_MAPPING[self.best_responder_sector_beam - 45]
                else:
                    in_sector_pencil_IDs = self.pencil_IDs
            # Create SSW frames for every pencil and send them to the MAC protocol
            for i in range(len(in_sector_pencil_IDs) - 1):
                curr_pencil_ID = in_sector_pencil_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_pencil_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.PENCIL_RF_GAIN))  # Use pencil RF gain
                trn_pencil_sweep_payload = self.generate_SSW_frame(self.TRN_PENCIL_SWEEP, self.my_station_type,
                                                                   self.number_of_pencils - 1 - i, curr_pencil_ID, 0)
                pmt_to_send = pmt.cons(meta, trn_pencil_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                # self.ready.wait()
                time.sleep(0.06)
            # Send Pencil Sweep Finished Message via Quasi-omni beam
            trn_pencil_sweep_finished_payload = self.generate_SSW_frame(self.TRN_PENCIL_SWEEP_FINISHED,
                                                                        self.my_station_type, 0, self.quasiomni_ID,
                                                                        self.best_initiator_pencil_beam)
            # Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_SSW_finished = pmt.cons(meta, trn_pencil_sweep_finished_payload)
            self.packet_queue.put(TRN_SSW_finished)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.iterative_search_wait_for_next_response(self.ITERATIVE_PENCIL_SWEEP)

    def iterative_search_timer_based_wait_for_next_response(self, state):
        # print 'Wait for next response'
        if self.timer_iterative_search_timer_based != 0:
            self.timer_iterative_search_timer_based.cancel()
        if state == self.ITERATIVE_SECTOR_SWEEP:
            self.timer_iterative_search_timer_based = threading.Timer(
                self.timeout_iterative_search_timer_based * (self.number_of_sectors),
                self.iterative_search_timer_based_wait_for_next_response_timeout)
            self.timer_iterative_search_timer_based.start()
        if state == self.ITERATIVE_PENCIL_SWEEP:
            if self.retransmit_counter < 3:
                self.timer_iterative_search_timer_based = threading.Timer(self.timeout_iterative_search_timer_based * 6,
                                                                          self.iterative_search_timer_based_wait_for_next_response_timeout)  # max 6 pencil beams per sector
                self.timer_iterative_search_timer_based.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.iterative_search_timer_based_state = self.ITERATIVE_IDLE
                self.iterative_search_timer_based()
        elif state == self.ITERATIVE_SEND_SECTOR_FEEDBACK or state == self.ITERATIVE_SEND_PENCIL_FEEDBACK:
            if self.retransmit_counter < 3:
                self.timer_iterative_search_timer_based = threading.Timer(self.timeout_iterative_search_timer_based,
                                                                          self.iterative_search_timer_based_wait_for_next_response_timeout)
                self.timer_iterative_search_timer_based.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.iterative_search_timer_based_state = self.ITERATIVE_IDLE
                self.iterative_search_timer_based()

    def iterative_search_timer_based_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_iterative_search_timer_based != 0:
                self.timer_iterative_search_timer_based.cancel()
            self.retransmit_counter = 0

    def iterative_search_timer_based_wait_for_next_response_timeout(self):
        # with self.thread_lock:
        print('[Beamsteering Protocol]: Iterative Search Timer Timeout')
        self.iterative_search_timer_based_state = self.last_state
        self.iterative_search_timer_based()

    def iterative_search_timer_based(self):
        ### General States
        if self.iterative_search_timer_based_state == self.ITERATIVE_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined ITERATIVE state!')
            return 0

        if self.iterative_search_timer_based_state == self.ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE_SECTOR_FEEDBACK_ACK RECEIVED')
            self.last_state = self.ITERATIVE_SECTOR_FEEDBACK_ACK_RECEIVED
            self.iterative_search_timer_based_state = self.ITERATIVE_PENCIL_SWEEP

        if self.iterative_search_timer_based_state == self.ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE_PENCIL_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_pencil_beam, self.PENCIL_RF_GAIN)
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.last_state = self.ITERATIVE_PENCIL_FEEDBACK_ACK_RECEIVED
            self.iterative_search_timer_based_state = self.ITERATIVE_IDLE

        if self.iterative_search_timer_based_state == self.ITERATIVE_LAST_SECTOR_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: ITERATIVE LAST SECTOR SSW FRAME')
            # Iterative sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: ITERATIVE Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.SECTOR_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Sector Beam: ', self.best_responder_sector_beam)
                self.iterative_search_timer_based_state = self.ITERATIVE_SEND_SECTOR_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Sector Beam: ', self.best_initiator_sector_beam)
                self.iterative_search_timer_based_state = self.ITERATIVE_SECTOR_SWEEP

        if self.iterative_search_timer_based_state == self.ITERATIVE_LAST_PENCIL_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: ITERATIVE LAST PENCIL SSW FRAME')
            # Iterative sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: ITERATIVE Best Pencil Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.PENCIL_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Pencil Beam: ', self.best_responder_pencil_beam)
                self.iterative_search_timer_based_state = self.ITERATIVE_SEND_PENCIL_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Pencil Beam: ', self.best_initiator_pencil_beam)
                self.iterative_search_timer_based_state = self.ITERATIVE_PENCIL_SWEEP

        if self.iterative_search_timer_based_state == self.ITERATIVE_SECTOR_FEEDBACK_RECEIVED:
            # print('[Beamsteering Protocol]: ITERATIVE SECTOR FEEDBACK RECEIVED')

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_sector_beam,
                                                                   self.best_initiator_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # SECTOR SLS complete

        if self.iterative_search_timer_based_state == self.ITERATIVE_PENCIL_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: ITERATIVE PENCIL FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.tx_beam_ID = self.best_responder_pencil_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_pencil_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_pencil_beam,
                                                                   self.best_initiator_pencil_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.PENCIL_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_feedback_ack)

            # SLS complete got back to state IDLE
            self.iterative_search_timer_based_state = self.ITERATIVE_IDLE

        if self.iterative_search_timer_based_state == self.ITERATIVE_RECEIVE_SECTOR_SSW_FRAMES:
            # print('[Beamsteering Protocol]: SECTOR SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.iterative_search_timer_based_state == self.ITERATIVE_RECEIVE_PENCIL_SSW_FRAMES:
            # print('[Beamsteering Protocol]: PENCIL SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.iterative_search_timer_based_state == self.ITERATIVE_SEND_SECTOR_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND ITERATIVE SECTOR SLS FEEDBACK')
            self.last_state = self.ITERATIVE_SEND_SECTOR_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_sector_beam,
                                                               self.best_responder_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.iterative_search_timer_based_wait_for_next_response(self.ITERATIVE_SEND_SECTOR_FEEDBACK)

        if self.iterative_search_timer_based_state == self.ITERATIVE_SEND_PENCIL_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND ITERATIVE PENCIL SLS FEEDBACK')
            self.last_state = self.ITERATIVE_SEND_PENCIL_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_pencil_beam,
                                                               self.best_responder_pencil_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.PENCIL_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.iterative_search_timer_based_wait_for_next_response(self.ITERATIVE_SEND_PENCIL_FEEDBACK)

        if self.iterative_search_timer_based_state == self.ITERATIVE_IDLE:
            # print('[Beamsteering Protocol]: ITERATIVE IDLE')
            self.last_state = self.ITERATIVE_IDLE
            if self.tx_array_trained == False:
                if self.my_station_type == self.INITIATOR:
                    # print('[Beamsteering Protocol]: ITERATIVE IDLE - not trained')
                    self.iterative_search_timer_based_state = self.ITERATIVE_SECTOR_SWEEP
            else:
                # print('[Beamsteering Protocol]: ITERATIVE IDLE - trained')
                return

        if self.iterative_search_timer_based_state == self.ITERATIVE_SECTOR_SWEEP:
            # print('[Beamsteering Protocol]: ITERATIVE SECTOR SWEEP')
            self.last_state = self.ITERATIVE_SECTOR_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every sector and send them to the MAC protocol
            for i in range(len(self.sector_IDs)):
                curr_sector_ID = self.sector_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_sector_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                trn_sector_sweep_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP, self.my_station_type,
                                                                   self.number_of_sectors - 1 - i, curr_sector_ID,
                                                                   self.best_initiator_sector_beam)
                pmt_to_send = pmt.cons(meta, trn_sector_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.ready.wait()
                time.sleep(0.06)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.iterative_search_timer_based_wait_for_next_response(self.ITERATIVE_SECTOR_SWEEP)

        if self.iterative_search_timer_based_state == self.ITERATIVE_PENCIL_SWEEP:
            # print('[Beamsteering Protocol]: ITERATIVE PENCIL SWEEP')
            self.last_state = self.ITERATIVE_PENCIL_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Find Pencil beam in best sector
            if self.my_station_type == self.INITIATOR:
                if self.best_initiator_sector_beam >= 45 and self.best_initiator_sector_beam <= 57:
                    in_sector_pencil_IDs = self.SECTOR_TO_PENCIL_MAPPING[self.best_initiator_sector_beam - 45]
                else:
                    in_sector_pencil_IDs = self.pencil_IDs
            elif self.my_station_type == self.RESPONDER:
                if self.best_responder_sector_beam >= 45 and self.best_responder_sector_beam <= 57:
                    in_sector_pencil_IDs = self.SECTOR_TO_PENCIL_MAPPING[self.best_responder_sector_beam - 45]
                else:
                    in_sector_pencil_IDs = self.pencil_IDs
            # Create SSW frames for every pencil and send them to the MAC protocol
            for i in range(len(in_sector_pencil_IDs) - 1):
                curr_pencil_ID = in_sector_pencil_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_pencil_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.PENCIL_RF_GAIN))  # Use pencil RF gain
                trn_pencil_sweep_payload = self.generate_SSW_frame(self.TRN_PENCIL_SWEEP, self.my_station_type,
                                                                   self.number_of_pencils - 1 - i, curr_pencil_ID,
                                                                   self.best_initiator_pencil_beam)
                pmt_to_send = pmt.cons(meta, trn_pencil_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                # self.ready.wait()
                time.sleep(0.06)

            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.iterative_search_timer_based_wait_for_next_response(self.ITERATIVE_PENCIL_SWEEP)

    def SLS_wait_for_next_response(self, state):
        # print 'Wait for next response'
        if self.timer_SLS != 0:
            self.timer_SLS.cancel()
        # if state == self.SLS_SEND_TRN_REQUEST:
        #     #Run infinitely
        #     self.timer_SLS = threading.Timer(self.timeout_SLS, self.SLS_wait_for_next_response_timeout)
        #     self.timer_SLS.start()
        if state == self.SLS_SWEEP:
            self.timer_SLS = threading.Timer(self.timeout_SLS * (self.number_of_sectors),
                                             self.SLS_wait_for_next_response_timeout)
            self.timer_SLS.start()
        elif state == self.SLS_SEND_FEEDBACK:
            if self.retransmit_counter < 2:
                self.timer_SLS = threading.Timer(self.timeout_SLS, self.SLS_wait_for_next_response_timeout)
                self.timer_SLS.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.SLS_state = self.SLS_IDLE
                self.SLS()

    def SLS_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_SLS != 0:
                self.timer_SLS.cancel()
            self.retransmit_counter = 0

    def SLS_wait_for_next_response_timeout(self):
        # with self.thread_lock:
        print('[Beamsteering Protocol]: SLS Timer Timeout')
        self.SLS_state = self.last_state
        self.SLS()

    def SLS(self):
        # FSM for SLS phase based on two-sided quasi-omni beam links
        # print 'SLS called. last state: ', self.SLS_state

        ### General States
        if self.SLS_state == self.SLS_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined SLS state!')
            return 0

        if self.SLS_state == self.SLS_FEEDBACK_ACK_RECEIVED:
            # print('[Beamsteering Protocol]: SLS_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_sector_beam, self.SECTOR_RF_GAIN)
            self.tx_RF_gain = self.SECTOR_RF_GAIN
            self.last_state = self.SLS_FEEDBACK_ACK_RECEIVED
            self.SLS_state = self.SLS_IDLE

        if self.SLS_state == self.SLS_LAST_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: SLS LAST SSW FRAME')
            # SLS sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: SLS Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.SECTOR_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Sector Beam: ', self.best_responder_sector_beam)
                self.SLS_state = self.SLS_SEND_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Sector Beam: ', self.best_initiator_sector_beam)
                self.SLS_state = self.SLS_SWEEP

        # if self.SLS_state == self.SLS_TRN_REQUEST_ACK_RECEIVED:
        #     #print('[Beamsteering Protocol]: TRN REQUEST ACK RECEIVED')
        #     self.last_state = self.SLS_TRN_REQUEST_ACK_RECEIVED
        #     #Correct SLS_TRN_REQUEST is received -> Sector sweep can start
        #     self.SLS_state = self.SLS_SWEEP

        if self.SLS_state == self.SLS_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: SLS FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.SECTOR_RF_GAIN
            self.tx_beam_ID = self.best_responder_sector_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_sector_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_sector_beam,
                                                                   self.best_initiator_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_feedback_ack)

            # SLS complete got back to state IDLE
            self.SLS_state = self.SLS_IDLE

        # if self.SLS_state == self.SLS_TRN_REQUEST_RECEIVED: #State at Responder Station
        #     print('[Beamsteering Protocol]: TRN REQUEST RECEIVED')
        #     #TRN Request message received. Confirm reception with ACK and set state to receive SSW frames
        #     trn_request_ack_payload = self.generate_SSW_frame(self.TRN_REQUEST_ACK, self.my_station_type, self.number_of_sectors, self.quasiomni_ID, 0)
        #     meta = pmt.make_dict()
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(self.BEAMSTEERING_PROTOCOL_MESSAGE)) # Set beam track request header flag 
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"), pmt.from_long(0)) # Set beam track request header flag 
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(self.quasiomni_ID)) # Use quasi-omni beam
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.from_long(self.QUASI_OMNI_RF_GAIN)) # Use quasi-omni RF gain
        #     TRN_request_ack = pmt.cons(meta, trn_request_ack_payload)
        #     self.packet_queue.put(TRN_request_ack)
        #     self.send_from_queue()
        #     #self.message_port_pub(pmt.intern('out'), TRN_request_ack)

        if self.SLS_state == self.SLS_RECEIVE_SSW_FRAMES:
            # print('[Beamsteering Protocol]: SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.SLS_state == self.SLS_SEND_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND SLS FEEDBACK')
            self.last_state = self.SLS_SEND_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_sector_beam, self.best_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.SLS_wait_for_next_response(self.SLS_SEND_FEEDBACK)

        if self.SLS_state == self.SLS_IDLE:
            # print('[Beamsteering Protocol]: SLS IDLE')
            self.last_state = self.SLS_IDLE
            if self.tx_array_trained == False:
                if self.my_station_type == self.INITIATOR:
                    # print('[Beamsteering Protocol]: SLS IDLE - not trained')
                    self.SLS_state = self.SLS_SWEEP
            else:
                # print('[Beamsteering Protocol]: SLS IDLE - trained')
                return

        if self.SLS_state == self.SLS_SWEEP:
            print('[Beamsteering Protocol]: SLS SWEEP')
            self.last_state = self.SLS_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every sector and send them to the MAC protocol
            for i in range(len(self.sector_IDs)):
                curr_sector_ID = self.sector_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_sector_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                trn_sector_sweep_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP, self.my_station_type,
                                                                   self.number_of_sectors - 1 - i, curr_sector_ID, 0)
                pmt_to_send = pmt.cons(meta, trn_sector_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                self.ready.wait()
                time.sleep(0.06)
            # Send Sector Sweep Finished Message via Quasi-omni beam
            trn_sector_sweep_finished_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP_FINISHED,
                                                                        self.my_station_type, 0, self.quasiomni_ID,
                                                                        self.best_initiator_sector_beam)
            # Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_SSW_finished = pmt.cons(meta, trn_sector_sweep_finished_payload)
            self.packet_queue.put(TRN_SSW_finished)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.SLS_wait_for_next_response(self.SLS_SWEEP)

        # if self.SLS_state == self.SLS_SEND_TRN_REQUEST:
        #     #print('[Beamsteering Protocol]: SEND TRN REQUEST')
        #     self.last_state = self.SLS_SEND_TRN_REQUEST
        #     #Start with TRN Request from Initiator to Responder Station
        #     trn_request_payload = self.generate_SSW_frame(self.TRN_REQUEST, self.my_station_type, self.number_of_sectors, self.quasiomni_ID, 0)
        #     #Add tags/meta
        #     meta = pmt.make_dict()
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(self.BEAMSTEERING_PROTOCOL_MESSAGE)) # Set beam track request header flag 
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"), pmt.from_long(1)) # Set beam track request header flag 
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(self.quasiomni_ID)) # Use quasi-omni beam
        #     meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.from_long(self.QUASI_OMNI_RF_GAIN)) # Use quasi-omni RF gain
        #     TRN_request = pmt.cons(meta, trn_request_payload)
        #     self.packet_queue.put(TRN_request)
        #     self.send_from_queue()
        #     #self.message_port_pub(pmt.intern('out'), TRN_request)
        #     #Reset variables
        #     self.list_of_beam_and_rssi = []
        #     self.last_beam_ID_received = -1
        #     self.last_rssi_received = 0
        #     self.cdown = 0
        #     self.direction = -1
        #     #Wait for response
        #     self.SLS_wait_for_next_response(self.SLS_SEND_TRN_REQUEST)

    def PLS_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_PLS != 0:
                self.timer_PLS.cancel()
            self.retransmit_counter = 0

    def PLS_wait_for_next_response_timeout(self):
        # with self.thread_lock:
        print('[Beamsteering Protocol]: PLS Timer Timeout')
        self.PLS_state = self.last_state
        self.PLS()

    def PLS_wait_for_next_response(self, state):
        # print 'Wait for next response'
        if self.timer_PLS != 0:
            self.timer_PLS.cancel()
        if state == self.PLS_SWEEP:
            self.timer_PLS = threading.Timer(self.timeout_PLS * (self.number_of_pencils),
                                             self.PLS_wait_for_next_response_timeout)
            self.timer_PLS.start()
        elif state == self.PLS_SEND_FEEDBACK:
            if self.retransmit_counter < 2:
                self.timer_PLS = threading.Timer(self.timeout_PLS, self.PLS_wait_for_next_response_timeout)
                self.timer_PLS.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.PLS_state = self.PLS_IDLE
                self.PLS()

    def PLS(self):
        # FSM for PLS phase based on two-sided quasi-omni beam links

        ### General States
        if self.PLS_state == self.PLS_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined PLS state!')
            return 0

        if self.PLS_state == self.PLS_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: PLS_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_pencil_beam, self.PENCIL_RF_GAIN)
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.last_state = self.PLS_FEEDBACK_ACK_RECEIVED
            self.PLS_state = self.PLS_IDLE

        if self.PLS_state == self.PLS_LAST_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: PLS LAST SSW FRAME')
            # PLS sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: PLS Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.PENCIL_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Pencil Beam: ', self.best_responder_pencil_beam)
                self.PLS_state = self.PLS_SEND_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Pencil Beam: ', self.best_initiator_pencil_beam)
                self.PLS_state = self.PLS_SWEEP

        if self.PLS_state == self.PLS_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: PLS FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.tx_beam_ID = self.best_responder_pencil_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_pencil_beam,
                                                                   self.best_initiator_pencil_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.PENCIL_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # PLS complete got back to state IDLE
            self.PLS_state = self.PLS_IDLE

        if self.PLS_state == self.PLS_RECEIVE_SSW_FRAMES:
            # print('[Beamsteering Protocol]: PLS SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.PLS_state == self.PLS_SEND_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND PLS FEEDBACK')
            self.last_state = self.PLS_SEND_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_pencil_beam, self.best_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.PENCIL_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.PLS_wait_for_next_response(self.PLS_SEND_FEEDBACK)

        if self.PLS_state == self.PLS_IDLE:
            # print('[Beamsteering Protocol]: PLS IDLE')
            self.last_state = self.PLS_IDLE
            if self.tx_array_trained == False:
                # print('[Beamsteering Protocol]: PLS IDLE - not trained')
                if self.my_station_type == self.INITIATOR:
                    self.PLS_state = self.PLS_SWEEP
            else:
                # print('[Beamsteering Protocol]: PLS IDLE - trained')
                return

        if self.PLS_state == self.PLS_SWEEP:
            print('[Beamsteering Protocol]: PLS SWEEP')
            self.last_state = self.PLS_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every pencil and send them to the MAC protocol
            for i in range(len(self.pencil_IDs)):
                curr_pencil_ID = self.pencil_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_pencil_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.PENCIL_RF_GAIN))  # Use sector RF gain
                trn_pencil_sweep_payload = self.generate_SSW_frame(self.TRN_PENCIL_SWEEP, self.my_station_type,
                                                                   self.number_of_pencils - 1 - i, curr_pencil_ID, 0)
                pmt_to_send = pmt.cons(meta, trn_pencil_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                self.ready.wait()
                time.sleep(0.06)
            # Send Pencil Sweep Finished Message via Quasi-omni beam
            trn_pencil_sweep_finished_payload = self.generate_SSW_frame(self.TRN_PENCIL_SWEEP_FINISHED,
                                                                        self.my_station_type, 0, self.quasiomni_ID,
                                                                        self.best_initiator_pencil_beam)
            # Add tags/meta
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.quasiomni_ID))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.QUASI_OMNI_RF_GAIN))  # Use quasi-omni RF gain
            TRN_SSW_finished = pmt.cons(meta, trn_pencil_sweep_finished_payload)
            self.packet_queue.put(TRN_SSW_finished)
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.PLS_wait_for_next_response(self.PLS_SWEEP)

    def PLS_timer_based_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_PLS_timer_based != 0:
                self.timer_PLS_timer_based.cancel()
            self.retransmit_counter = 0

    def PLS_timer_based_wait_for_next_response_timeout(self):
        # with self.thread_lock:
        print('[Beamsteering Protocol]: PLS Timer Timeout')
        self.PLS_timer_based_state = self.last_state
        self.PLS_timer_based()

    def PLS_timer_based_wait_for_next_response(self, state):
        # print 'Wait for next response'
        if self.timer_PLS_timer_based != 0:
            self.timer_PLS_timer_based.cancel()
        if state == self.PLS_SWEEP:
            self.timer_PLS_timer_based = threading.Timer(self.timeout_PLS_timer_based * (self.number_of_pencils),
                                                         self.PLS_timer_based_wait_for_next_response_timeout)
            self.timer_PLS_timer_based.start()
        elif state == self.PLS_SEND_FEEDBACK:
            if self.retransmit_counter < 2:
                self.timer_PLS_timer_based = threading.Timer(self.timeout_PLS_timer_based,
                                                             self.PLS_timer_based_wait_for_next_response_timeout)
                self.timer_PLS_timer_based.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.PLS_timer_based_state = self.PLS_IDLE
                self.PLS_timer_based()

    def PLS_timer_based(self):
        # FSM for PLS phase based on one-sided quasi-omni beam links

        ### General States
        if self.PLS_timer_based_state == self.PLS_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined PLS state!')
            return 0

        if self.PLS_timer_based_state == self.PLS_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: PLS_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_pencil_beam, self.PENCIL_RF_GAIN)
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.last_state = self.PLS_FEEDBACK_ACK_RECEIVED
            self.PLS_timer_based_state = self.PLS_IDLE

        if self.PLS_timer_based_state == self.PLS_LAST_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: PLS LAST SSW FRAME')
            # PLS sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: PLS Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.PENCIL_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Pencil Beam: ', self.best_responder_pencil_beam)
                self.PLS_timer_based_state = self.PLS_SEND_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_pencil_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Pencil Beam: ', self.best_initiator_pencil_beam)
                self.PLS_timer_based_state = self.PLS_SWEEP

        if self.PLS_timer_based_state == self.PLS_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: PLS FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.PENCIL_RF_GAIN
            self.tx_beam_ID = self.best_responder_pencil_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_pencil_beam,
                                                                   self.best_initiator_pencil_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.PENCIL_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # PLS complete got back to state IDLE
            self.PLS_timer_based_state = self.PLS_IDLE

        if self.PLS_timer_based_state == self.PLS_RECEIVE_SSW_FRAMES:
            # print('[Beamsteering Protocol]: PLS SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.PLS_timer_based_state == self.PLS_SEND_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND PLS FEEDBACK')
            self.last_state = self.PLS_SEND_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_PENCIL_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_pencil_beam, self.best_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_pencil_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.PENCIL_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.PLS_timer_based_wait_for_next_response(self.PLS_SEND_FEEDBACK)

        if self.PLS_timer_based_state == self.PLS_IDLE:
            # print('[Beamsteering Protocol]: PLS IDLE')
            self.last_state = self.PLS_IDLE
            if self.tx_array_trained == False:
                # print('[Beamsteering Protocol]: PLS IDLE - not trained')
                if self.my_station_type == self.INITIATOR:
                    self.PLS_timer_based_state = self.PLS_SWEEP
            else:
                # print('[Beamsteering Protocol]: PLS IDLE - trained')
                return

        if self.PLS_timer_based_state == self.PLS_SWEEP:
            # print('[Beamsteering Protocol]: PLS SWEEP')
            self.last_state = self.PLS_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every pencil and send them to the MAC protocol
            for i in range(len(self.pencil_IDs)):
		#print('Type:', type(self.fixed_beam), type(self.pencil_IDs[i]))
                if (self.sweeping):
                   curr_pencil_ID = self.pencil_IDs[i]
                else:
                   curr_pencil_ID = numpy.int64(self.fixed_beam)
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                   self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                   pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_pencil_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.PENCIL_RF_GAIN))  # Use sector RF gain
                trn_pencil_sweep_payload = self.generate_SSW_frame(self.TRN_PENCIL_SWEEP, self.my_station_type,
                                                                   self.number_of_pencils - 1 - i, curr_pencil_ID,
                                                                   self.best_initiator_pencil_beam)
                pmt_to_send = pmt.cons(meta, trn_pencil_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                # self.ready.wait()
                time.sleep(self.beam_interval)
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.PLS_timer_based_wait_for_next_response(self.PLS_SWEEP)

    def history_search_wait_for_next_response(self, state):
        # print 'Wait for next response'
        if self.timer_history_search != 0:
            self.timer_history_search.cancel()
        # if state == self.SLS_SEND_TRN_REQUEST:
        #     #Run infinitely
        #     self.timer_SLS = threading.Timer(self.timeout_SLS, self.SLS_wait_for_next_response_timeout)
        #     self.timer_SLS.start()
        if state == self.SLS_SWEEP:
            self.timer_history_search = threading.Timer(self.timeout_history_search * (self.number_of_sectors),
                                                        self.history_search_wait_for_next_response_timeout)
            self.timer_history_search.start()
        elif state == self.SLS_SEND_FEEDBACK:
            if self.retransmit_counter < 2:
                self.timer_history_search = threading.Timer(self.timeout_history_search,
                                                            self.history_search_wait_for_next_response_timeout)
                self.timer_history_search.start()
                self.retransmit_counter += 1
            else:
                self.retransmit_counter = 0
                self.history_search_state = self.SLS_IDLE
                self.history_search()

    def history_search_stop_wait_timer(self):
        with self.thread_lock:
            if self.timer_history_search != 0:
                self.timer_history_search.cancel()
            self.retransmit_counter = 0

    def history_search_wait_for_next_response_timeout(self):
        # with self.thread_lock:
        print('[Beamsteering Protocol]: SLS Timer Timeout')
        self.history_search_state = self.last_state
        self.history_search()

    def history_search(self):
        # print('History search_timer_based called')

        ### General States
        if self.history_search_state == self.SLS_UNDEFINED:
            print('[Beamsteering Protocol]: Undefined SLS state!')
            return 0

        if self.history_search_state == self.SLS_FEEDBACK_ACK_RECEIVED:
            print('[Beamsteering Protocol]: SLS_FEEDBACK_ACK RECEIVED')
            self.tx_array_trained = True
            self.send_TX_antenna_array_trained_message(self.best_initiator_sector_beam, self.SECTOR_RF_GAIN)
            self.tx_RF_gain = self.SECTOR_RF_GAIN
            self.last_state = self.SLS_FEEDBACK_ACK_RECEIVED
            self.history_search_state = self.SLS_IDLE

        if self.history_search_state == self.SLS_LAST_SSW_FRAME_RECEIVED:
            # print('[Beamsteering Protocol]: SLS LAST SSW FRAME')
            # history_search sweep finished message received -> evaluate best beam and send feedback message
            last_RSSI = -50
            last_beam_ID = -1
            for beam_ID, RSSI in self.list_of_beam_and_rssi:
                if RSSI > last_RSSI:
                    last_RSSI = RSSI
                    last_beam_ID = beam_ID
            if last_beam_ID == -1:
                print('[Beamsteering Protocol]: ERROR: SLS Best Sector Evaluation Failed!')
                # Setting best beam to quasi-omni one
                last_beam_ID = 0
            self.best_beam = last_beam_ID
            self.best_beam_gain = self.SECTOR_RF_GAIN
            if self.my_station_type == self.INITIATOR:
                self.best_responder_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Responder Sector Beam: ', self.best_responder_sector_beam)
                self.history_search_state = self.SLS_SEND_FEEDBACK
            elif self.my_station_type == self.RESPONDER:
                self.best_initiator_sector_beam = last_beam_ID
                print('[Beamsteering Protocol]: Best Initiator Sector Beam: ', self.best_initiator_sector_beam)
                self.history_search_state = self.SLS_SWEEP

        if self.history_search_state == self.SLS_FEEDBACK_RECEIVED:
            print('[Beamsteering Protocol]: history_search FEEDBACK RECEIVED')
            # Set Parameters
            self.tx_array_trained = True
            self.tx_RF_gain = self.SECTOR_RF_GAIN
            self.tx_beam_ID = self.best_responder_sector_beam
            # print '[Beamsteering Protocol]: Best Responder Beam: ', self.best_responder_beam
            # Send MAC control message
            self.send_TX_antenna_array_trained_message(self.tx_beam_ID, self.tx_RF_gain)

            # Send Feedback ACK message
            trn_ssw_feedback_ack_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK_ACK,
                                                                   self.my_station_type, 0,
                                                                   self.best_responder_sector_beam,
                                                                   self.best_initiator_sector_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_responder_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            TRN_feedback_ack = pmt.cons(meta, trn_ssw_feedback_ack_payload)
            self.packet_queue.put(TRN_feedback_ack)
            self.send_from_queue()
            # SLS complete got back to state IDLE
            self.history_search_state = self.SLS_IDLE

        if self.history_search_state == self.SLS_RECEIVE_SSW_FRAMES:
            # print('[Beamsteering Protocol]: SLS SSW FRAME RECEIVED')
            # Save received tuple of Beam ID and corresponding RSSI value in a tuple list
            self.list_of_beam_and_rssi.append((self.last_beam_ID_received, self.last_rssi_received))

        if self.history_search_state == self.SLS_SEND_FEEDBACK:
            # print('[Beamsteering Protocol]: SEND SLS FEEDBACK')
            self.last_state = self.SLS_SEND_FEEDBACK

            # Send Feedback message (Best beam ID is included in the beam_ID field)
            trn_ssw_feedback_payload = self.generate_SSW_frame(self.TRN_SECTOR_SSW_FEEDBACK, self.my_station_type, 0,
                                                               self.best_initiator_sector_beam, self.best_beam)
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                pmt.from_long(0))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"),
                                pmt.from_long(self.best_initiator_sector_beam))  # Use quasi-omni beam
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                pmt.from_long(self.SECTOR_RF_GAIN))  # Use quasi-omni RF gain
            self.packet_queue.put(pmt.cons(meta, trn_ssw_feedback_payload))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, trn_ssw_feedback_payload))
            self.history_search_timer_based_wait_for_next_response(self.SLS_SEND_FEEDBACK)

        if self.history_search_state == self.SLS_IDLE:
            # print('[Beamsteering Protocol]: SLS IDLE')
            self.last_state = self.SLS_IDLE
            if self.tx_array_trained == False:
                # print('[Beamsteering Protocol]: SLS IDLE - not trained')
                if self.my_station_type == self.INITIATOR:
                    self.history_search_state = self.SLS_SWEEP
            else:
                # print('[Beamsteering Protocol]: SLS IDLE - trained')
                return

        if self.history_search_state == self.SLS_SWEEP:
            print('[Beamsteering Protocol]: history_search SWEEP')
            self.last_state = self.SLS_SWEEP
            # Reset variables
            self.list_of_beam_and_rssi = []
            self.last_beam_ID_received = -1
            self.last_rssi_received = 0
            self.cdown = 0
            self.direction = -1
            # Create SSW frames for every sector and send them to the MAC protocol
            for i in range(len(self.sector_IDs)):
                curr_sector_ID = self.sector_IDs[i]
                meta = pmt.make_dict()
                meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                    self.BEAMSTEERING_PROTOCOL_MESSAGE))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                    pmt.from_long(0))  # Set beam track request header flag
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(curr_sector_ID))
                meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                    pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                trn_sector_sweep_payload = self.generate_SSW_frame(self.TRN_SECTOR_SWEEP, self.my_station_type,
                                                                   self.number_of_sectors - 1 - i, curr_sector_ID, 0)
                pmt_to_send = pmt.cons(meta, trn_sector_sweep_payload)
                self.packet_queue.put(pmt_to_send)
                self.send_from_queue()
                # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                self.ready.wait()
                time.sleep(0.06)
            # self.message_port_pub(pmt.intern('out'), TRN_SSW_finished)
            if self.my_station_type == self.INITIATOR:
                # Wait for response
                self.history_search_timer_based_wait_for_next_response(self.SLS_SWEEP)
    
    def fixed_beam_backup_link_wait_for_next_burst_timeout(self):
        print('[Beamsteering Protocol]: Fixed Beam with Backup Link, restart burst')
        self.fixed_beam_backup_link() # call the state machine
    
    def fixed_beam_backup_link_wait_for_next_burst(self):
        if self.timer_fixed_beam_backup_link_wait_for_next_burst != 0:
            self.timer_fixed_beam_backup_link_wait_for_next_burst.cancel()
        
        self.timer_fixed_beam_backup_link_wait_for_next_burst = threading.Timer(self.fixed_beam_backup_link_next_burst_delay,
                                                                                self.fixed_beam_backup_link_wait_for_next_burst_timeout)
        self.timer_fixed_beam_backup_link_wait_for_next_burst.start()
    
    def fixed_beam_backup_link(self):
        # Fixed Beam with Backup Link state machine
        
        if self.fixed_beam_backup_link_state == self.FIXED_BEAM_BACKUP_LINK_STATE_DATA_TRX:
            if self.my_station_type == self.INITIATOR:
                # if initiator, just keep sending SSW frames
                for i in range(self.fixed_beam_backup_link_data_burst_packet_no):
                    meta = pmt.make_dict()
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                                       self.BEAMSTEERING_PROTOCOL_MESSAGE))
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                       pmt.from_long(0))  # Set beam track request header flag
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(self.tx_beam_ID))
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                        pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                    trn_fixed_beam_backup_link_payload = self.generate_SSW_frame(self.TRN_FIXED_BEAM_BACKUP_LINK_DATA_BURST, self.my_station_type,
                                                                       self.fixed_beam_backup_link_data_burst_packet_no - 1 - i, self.tx_beam_ID, 0)
                    pmt_to_send = pmt.cons(meta, trn_fixed_beam_backup_link_payload)
                    self.packet_queue.put(pmt_to_send)
                    self.send_from_queue()
                    # self.message_port_pub(pmt.intern('out'), pmt_to_send)
                    # self.ready.wait()
                    time.sleep(self.beam_interval)
                # self.fixed_beam_backup_link_wait_for_next_burst() # call function to set timer for next burst
                
            else:
                # if responder, do nothing, except for processing packets from the initiator
                pass
        
        if self.fixed_beam_backup_link_state == self.FIXED_BEAM_BACKUP_LINK_STATE_REPORT:
            if self.my_station_type == self.RESPONDER:
                # if responder, check input from lidar (if not checked yet) and decide the link to use
                if self.fixed_beam_backup_link_checked_lidar == False:
                    new_beam_id = -1
                    ptype = 0
                    if self.fixed_beam_backup_link_lidar_obstacle_msg:  
                        # if there is an obstacle, we should use the backup link
                        new_beam_id = self.fixed_beam_backup_link_backup_beam_id
                        ptype = self.TRN_FIXED_BEAM_BACKUP_LINK_SWITCH_BACKUP
                        print('Fixed Beam with Backup Link: Message to be sent: switch to backup link')
                    else:
                        # if there is no obstacle, we should use the default link
                        new_beam_id = self.fixed_beam_backup_link_default_beam_id
                        ptype = self.TRN_FIXED_BEAM_BACKUP_LINK_SWITCH_DEFAULT
                        print('Fixed Beam with Backup Link: Message to be sent: switch to default link')
                    
                    meta = pmt.make_dict()
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"), pmt.from_long(
                                        self.BEAMSTEERING_PROTOCOL_MESSAGE))
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("beam_track_req"),
                                        pmt.from_long(0))  # Set beam track request header flag
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(self.tx_beam_ID))
                    meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"),
                                        pmt.from_long(self.SECTOR_RF_GAIN))  # Use sector RF gain
                    
                    for i in range(self.fixed_beam_backup_link_beam_switch_message_retrans_no + 1):
                        # construct packet to send to initiator, as many times as stated
                        trn_fixed_beam_backup_link_payload = self.generate_SSW_frame(ptype, self.my_station_type, 
                                                                    self.fixed_beam_backup_link_beam_switch_message_retrans_no - i, self.tx_beam_ID, new_beam_id)
                        pmt_to_send = pmt.cons(meta, trn_fixed_beam_backup_link_payload)
                        self.packet_queue.put(pmt_to_send)
                        self.send_from_queue()
                        time.sleep(self.beam_interval)
                    
                    if new_beam_id != self.tx_beam_ID:
                        # if beam is supposed to change, send the SPI manager a related message
                        pmt_to_send = pmt.from_long(new_beam_id)
                        self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
                        
                        self.tx_beam_ID = new_beam_id
                        self.rx_beam_ID = new_beam_id
                    
                    self.fixed_beam_backup_link_checked_lidar = True
                    
            else: # if initiator, just wait for a message from the responder
                pass
    
    def fixed_beam_backup_link_set_next_state(self):
        if self.fixed_beam_backup_link_state == self.FIXED_BEAM_BACKUP_LINK_STATE_DATA_TRX:
            # set timer to switch to next state, TX/RX switch + 100 ms offset for handling the other operations
            self.timer_fixed_beam_backup_link_next_state = threading.Timer(self.fixed_beam_backup_link_report_state_duration + self.fixed_beam_backup_link_wait_tx_rx_switch + 0.1, self.fixed_beam_backup_link_set_next_state)
            self.timer_fixed_beam_backup_link_next_state.start() # start the timer
            self.fixed_beam_backup_link_state = self.FIXED_BEAM_BACKUP_LINK_STATE_REPORT # switch to report state
            if self.my_station_type == self.RESPONDER:
                # if I am the responder, I should switch from RX to TX to send link report
                pmt_to_send = pmt.from_long(self.FIXED_BEAM_BACKUP_LINK_SPI_SWITCH_TX)
                self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
            elif self.my_station_type == self.INITIATOR:
                # cancel the restart burst timer, as we are switching from data state to report state
                # if self.timer_fixed_beam_backup_link_wait_for_next_burst != 0:
                #     self.timer_fixed_beam_backup_link_wait_for_next_burst.cancel()
                # if I am the initiator, I should switch from TX to RX to receive link report
                pmt_to_send = pmt.from_long(self.FIXED_BEAM_BACKUP_LINK_SPI_SWITCH_RX)
                self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
            time.sleep(self.fixed_beam_backup_link_wait_tx_rx_switch) # wait for enough time for the TX/RX switch
            #self.timer_fixed_beam_backup_link_next_state = threading.Timer(self.fixed_beam_backup_link_report_state_duration, self.fixed_beam_backup_link_set_next_state)
            #self.timer_fixed_beam_backup_link_next_state.start() # start the timer
            
        elif self.fixed_beam_backup_link_state == self.FIXED_BEAM_BACKUP_LINK_STATE_REPORT:
            # set timer to switch to next state, TX/RX switch + 100 ms offset for handling the other operations
            self.timer_fixed_beam_backup_link_next_state = threading.Timer(self.fixed_beam_backup_link_data_state_duration + self.fixed_beam_backup_link_wait_tx_rx_switch + 0.1, self.fixed_beam_backup_link_set_next_state)
            self.timer_fixed_beam_backup_link_next_state.start() # start the timer
            self.fixed_beam_backup_link_state = self.FIXED_BEAM_BACKUP_LINK_STATE_DATA_TRX # switch to data state
            if self.my_station_type == self.RESPONDER:
                # set the lidar checked variable back to false
                self.fixed_beam_backup_link_checked_lidar = False
                # if I am the responder, I should switch from TX to RX for data reception
                pmt_to_send = pmt.from_long(self.FIXED_BEAM_BACKUP_LINK_SPI_SWITCH_RX)
                self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
            elif self.my_station_type == self.INITIATOR:
                # if I am the initiator, I should switch from RX to TX for data transmission
                pmt_to_send = pmt.from_long(self.FIXED_BEAM_BACKUP_LINK_SPI_SWITCH_TX)
                self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
            time.sleep(self.fixed_beam_backup_link_wait_tx_rx_switch) # wait for enough time for the TX/RX switch
            #self.timer_fixed_beam_backup_link_next_state = threading.Timer(self.fixed_beam_backup_link_data_state_duration, self.fixed_beam_backup_link_set_next_state)
            #self.timer_fixed_beam_backup_link_next_state.start() # start the timer
        
        elif self.fixed_beam_backup_link_state == -1:
            # first call, set timer to switch to next state, TX/RX switch + 100 ms offset for handling the other operations
            self.timer_fixed_beam_backup_link_next_state = threading.Timer(self.fixed_beam_backup_link_data_state_duration + 2 * self.fixed_beam_backup_link_wait_tx_rx_switch + 0.1, self.fixed_beam_backup_link_set_next_state)
            self.timer_fixed_beam_backup_link_next_state.start() # start the timer
            self.fixed_beam_backup_link_state = self.FIXED_BEAM_BACKUP_LINK_STATE_DATA_TRX # switch to data state
            # set TX and RX beam IDs to default beam
            self.tx_beam_ID = self.fixed_beam_backup_link_default_beam_id
            self.rx_beam_ID = self.fixed_beam_backup_link_default_beam_id
            # send message to SPI manager
            pmt_to_send = pmt.from_long(self.fixed_beam_backup_link_default_beam_id)
            self.message_port_pub(pmt.intern('spi_manager_out'), pmt_to_send)
            time.sleep(2 * self.fixed_beam_backup_link_wait_tx_rx_switch) # wait for enough time for the beam ID setup
            #self.timer_fixed_beam_backup_link_next_state = threading.Timer(self.fixed_beam_backup_link_data_state_duration, self.fixed_beam_backup_link_set_next_state)
            #self.timer_fixed_beam_backup_link_next_state.start() # start the timer
        
        else:
            print("[Beamsteering Protocol]: Invalid state for fixed beam with backup link.")
            return
        
        self.fixed_beam_backup_link() # call state machine
    
    def send_TX_antenna_array_trained_message(self, best_beam, best_beam_gain):
        with self.thread_lock:
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"),
                                pmt.from_long(self.MAC_SET_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(best_beam))
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_RF_gain"), pmt.from_long(best_beam_gain))
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_array_trained"), pmt.from_bool(True))
            self.packet_queue.put(pmt.cons(meta, pmt.PMT_NIL))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, pmt.PMT_NIL))

    def send_TX_antenna_array_requires_training_message(self):
        with self.thread_lock:
            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.string_to_symbol("msg_type"),
                                pmt.from_long(self.MAC_SET_MESSAGE))  # Set beam track request header flag
            meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_array_trained"), pmt.from_bool(False))
            self.packet_queue.put(pmt.cons(meta, pmt.PMT_NIL))
            self.send_from_queue()
            # self.message_port_pub(pmt.intern('out'), pmt.cons(meta, pmt.PMT_NIL))

    def log_events(self, event, packet_type, direction, cdown, TX_beam_used, best_beam_feedback, evm, rssi,
                   preamble_rms, preamble_snr, preamble_rss, rx_beam_id, tt_az_angle, tt_el_angle):
        timestamp = time.time()
        with open(self.log_file_name, 'a') as log_file:
            csv_writer = csv.DictWriter(log_file, fieldnames=self.csv_fields)
            csv_writer.writerow({'Timestamp': timestamp, 'Event': event, 'Packet Type': packet_type,
                                 'Direction': direction, 'CDOWN': cdown, 'Used TX Beam': TX_beam_used,
                                 'Beam Feedback': best_beam_feedback, 'EVM': evm, 'RSSI': rssi,
                                 'Preamble RMS': preamble_rms, 'RSS (before AGC)': preamble_rss,
                                 'RX Beam ID': rx_beam_id, 'TT Az angle': tt_az_angle, 'TT El angle': tt_el_angle})
        
        # per sector logging                       
        if self.log_per_sector:
            with open(self.curr_sector_fname, 'a') as sector_log_file:
                csv_writer = csv.DictWriter(sector_log_file, fieldnames=self.csv_fields)
                csv_writer.writerow({'Timestamp': timestamp, 'Event': event, 'Packet Type': packet_type,
                                 'Direction': direction, 'CDOWN': cdown, 'Used TX Beam': TX_beam_used,
                                 'Beam Feedback': best_beam_feedback, 'EVM': evm, 'RSSI': rssi,
                                 'Preamble RMS': preamble_rms, 'RSS (before AGC)': preamble_rss,
                                 'RX Beam ID': rx_beam_id, 'TT Az angle': tt_az_angle, 'TT El angle': tt_el_angle})
                
            

    def handle_beam_id_message(self, msg):
        beamId = pmt.to_float(msg)
        self.fixed_beam = beamId

    def handle_sweeping_message(self, msg):
        sweeping = pmt.to_bool(msg)
        self.sweeping = sweeping

    def handle_tt_message(self, msg):
        # turntable position received, save az and el info and create appropiate csv file
        if self.log_per_sector:
            msg_str = pmt.symbol_to_string(msg)
            l = msg_str.split(';')
            self.last_tt_az_angle_received = float(l[0])
            self.last_tt_el_angle_received = float(l[1])
            tt_inv_time = float(l[2])
            self.tt_run_no = int(l[3])
            
            # set timer so that the program switches to the new csv file only as the invalid time is about to end
            self.tt_inv_timer = threading.Timer(tt_inv_time - 0.15, self.csv_switch_sector)
            self.tt_inv_timer.start()
            

    def handle_lidar_message(self, msg):
        # information received from the lidar analysis, decide if you are going to switch links
        # normally there probably will be a lot more signal processing here, but right now just going with 1s and 0s
        msg_cont = pmt.to_long(msg)
        
        if msg_cont == 1:
            self.fixed_beam_backup_link_lidar_obstacle_msg = True    # we should switch to/stay on backup link
        elif msg_cont == 0:
            self.fixed_beam_backup_link_lidar_obstacle_msg = False   # we should switch to/stay on default link
        
    
    def csv_switch_sector(self):
        if self.curr_sector_fname != "": # if file already created and sector ended, move it to the final destination for syncronization
            shutil.copyfile(self.curr_sector_fname, self.curr_sector_fname_final_dest)            
        
        self.curr_sector_fname = self.log_per_sector_temp_dir + 'Station_' + str(
                        self.station_code) + '_Az_' + str(self.last_tt_az_angle_received) + '_El_' + str(self.last_tt_el_angle_received) + '_Run_' + str(self.tt_run_no) + '.csv'
        self.curr_sector_fname_final_dest = self.log_per_sector_save_dir + 'Station_' + str(
                        self.station_code) + '_Az_' + str(self.last_tt_az_angle_received) + '_El_' + str(self.last_tt_el_angle_received) + '_Run_' + str(self.tt_run_no) + '.csv'
            
        if self.curr_sector_fname not in self.log_per_sector_fnames:
            # if data from azimuth/elevation pair is received for the first time, first create the file and the header
            with open(self.curr_sector_fname, 'w') as sector_log_file:
                csv_writer = csv.DictWriter(sector_log_file, fieldnames=self.csv_fields)
                csv_writer.writeheader()
            self.log_per_sector_fnames.append(self.curr_sector_fname) # add to the list of created files
    
    def forecast(self, noutput_items, ninput_items_required):
        # setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items

    def work(self, input_items, output_items):
        #print('general_work called')
        #output_items[0][:] = input_items[0]
        #consume(0, len(input_items[0]))
        # self.consume_each(len(input_items[0]))
        #return len(output_items[0])
        return 0
    
    def forward_info_to_gui(self, tx_beam_id, rx_beam_id = None, best_beam = None, last_rssi = None, last_preamble_snr = None, preamble_rss = None):
        meta = pmt.make_dict()
        meta = pmt.dict_add(meta, pmt.string_to_symbol("tx_beam_id"), pmt.from_long(tx_beam_id))
        if rx_beam_id != None:
            meta = pmt.dict_add(meta, pmt.string_to_symbol("rx_beam_id"), pmt.from_float(rx_beam_id))
        if best_beam != None:
            meta = pmt.dict_add(meta, pmt.string_to_symbol("best_beam"), pmt.from_long(best_beam))
        if last_rssi != None:
            meta = pmt.dict_add(meta, pmt.string_to_symbol("last_rssi"), pmt.from_long(last_rssi))
        if last_preamble_snr != None:
            meta = pmt.dict_add(meta, pmt.string_to_symbol("last_preamble_snr"), pmt.from_float(last_preamble_snr))
        if preamble_rss != None:
            meta = pmt.dict_add(meta, pmt.string_to_symbol("preamble_rss"), pmt.from_float(preamble_rss))
        
        self.message_port_pub(pmt.intern('gui_out'), meta)

