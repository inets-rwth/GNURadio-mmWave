#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2022 iNETS RWTH - Florian Wischeler
# updated by Niklas Beckmann
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

class TX_logger(gr.basic_block):
    """
    docstring for block TX_logger
    """
    def __init__(self, station_name, mode):
        gr.basic_block.__init__(self,
            name="TX_logger",
            in_sig=[0],
            out_sig=[0])

    def forecast(self, noutput_items, ninput_items_required):
        #setup size of input_items[i] for work call
        for i in range(len(ninput_items_required)):
            ninput_items_required[i] = noutput_items

    def general_work(self, input_items, output_items):
        output_items[0][:] = input_items[0]
        consume(0, len(input_items[0]))
        #self.consume_each(len(input_items[0]))
        return len(output_items[0])

