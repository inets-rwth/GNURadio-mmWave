# Copyright 2020 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

########################################################################
# Check if there is C++ code at all
########################################################################
if(NOT iNETS_BeamManager_sources)
    MESSAGE(STATUS "No C++ sources... skipping python bindings")
    return()
endif(NOT iNETS_BeamManager_sources)

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

list(APPEND iNETS_BeamManager_python_files
    python_bindings.cc)

GR_PYBIND_MAKE_OOT(iNETS_BeamManager
   ../../..
   gr::iNETS_BeamManager
   "${iNETS_BeamManager_python_files}")

# copy bindings extension for use in QA test module
add_custom_command(TARGET iNETS_BeamManager_python POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:iNETS_BeamManager_python>
    ${PROJECT_BINARY_DIR}/test_modules/gnuradio/iNETS_BeamManager/
)

install(TARGETS iNETS_BeamManager_python DESTINATION ${GR_PYTHON_DIR}/gnuradio/iNETS_BeamManager COMPONENT pythonapi)
