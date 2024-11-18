/*
 * Copyright 2024 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

/***********************************************************************************/
/* This file is automatically generated using bindtool and can be manually edited  */
/* The following lines can be configured to regenerate this file during cmake      */
/* If manual edits are made, the following tags should be modified accordingly.    */
/* BINDTOOL_GEN_AUTOMATIC(0)                                                       */
/* BINDTOOL_USE_PYGCCXML(0)                                                        */
/* BINDTOOL_HEADER_FILE(phase_freq_correction.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(096105799118c1cea6e9d6728aac36af)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/iNETS_PacketizedLink/phase_freq_correction.h>
// pydoc.h is automatically generated in the build directory
#include <phase_freq_correction_pydoc.h>

void bind_phase_freq_correction(py::module& m)
{

    using phase_freq_correction    = ::gr::iNETS_PacketizedLink::phase_freq_correction;


    py::class_<phase_freq_correction, gr::sync_block, gr::block, gr::basic_block,
        std::shared_ptr<phase_freq_correction>>(m, "phase_freq_correction", D(phase_freq_correction))

        .def(py::init(&phase_freq_correction::make),
           py::arg("num_preamble_samples"),
           D(phase_freq_correction,make)
        )
        



        ;




}







