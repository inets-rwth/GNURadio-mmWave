# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT iNETS_PacketizedLink_sources)
    MESSAGE(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT iNETS_PacketizedLink_sources)

########################################################################
# Check for pygccxml
########################################################################
GR_PYTHON_CHECK_MODULE_RAW(
    "pygccxml"
    "import pygccxml"
    PYGCCXML_FOUND
    )

include(GrPybind)

########################################################################
# Python Bindings
########################################################################
list(APPEND iNETS_PacketizedLink_python_files
    baseband_derotation_python.cc
    baseband_derotation_tagged_stream_python.cc
    chunks_to_symbols_tagged_stream_python.cc
    constellation_decoder_tagged_stream_python.cc
    estimate_dBm_ff_python.cc
    evm_biased_bpsk_python.cc
    frame_sync_cc_python.cc
    multiply_length_tag_tagged_stream_python.cc
    packet_header_parser_python.cc
    phase_freq_correction_python.cc
    phy_agc_python.cc
    phy_header_payload_demux_python.cc
    repack_bits_tagged_stream_python.cc
    python_bindings.cc)

GR_PYBIND_MAKE_OOT(iNETS_PacketizedLink
   ../../..
   gr::iNETS_PacketizedLink
   "${iNETS_PacketizedLink_python_files}")

# copy bindings extension for use in QA test module
add_custom_command(TARGET iNETS_PacketizedLink_python POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:iNETS_PacketizedLink_python>
    ${PROJECT_BINARY_DIR}/test_modules/gnuradio/iNETS_PacketizedLink/
)

install(TARGETS iNETS_PacketizedLink_python DESTINATION ${GR_PYTHON_DIR}/gnuradio/iNETS_PacketizedLink COMPONENT pythonapi)
