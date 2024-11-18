# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT iNETS_SIVERSControl_sources)
    MESSAGE(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT iNETS_SIVERSControl_sources)

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

list(APPEND iNETS_SIVERSControl_python_files
    evk_set_beams_TX_single_SPI_python.cc
    evk_set_beams_TX_dual_SPI_python.cc
    evk_standalone_SPI_manager_python.cc python_bindings.cc)

GR_PYBIND_MAKE_OOT(iNETS_SIVERSControl
   ../../..
   gr::iNETS_SIVERSControl
   "${iNETS_SIVERSControl_python_files}")

# copy bindings extension for use in QA test module
add_custom_command(TARGET iNETS_SIVERSControl_python POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:iNETS_SIVERSControl_python>
    ${PROJECT_BINARY_DIR}/test_modules/gnuradio/iNETS_SIVERSControl/
)

install(TARGETS iNETS_SIVERSControl_python DESTINATION ${GR_PYTHON_DIR}/gnuradio/iNETS_SIVERSControl COMPONENT pythonapi)
