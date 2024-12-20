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
/* BINDTOOL_HEADER_FILE(frame_sync_cc.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(9b05ff01e69b6091650a8650de020d05)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/iNETS_PacketizedLink/frame_sync_cc.h>
// pydoc.h is automatically generated in the build directory
#include <frame_sync_cc_pydoc.h>

void bind_frame_sync_cc(py::module& m)
{

    using frame_sync_cc    = ::gr::iNETS_PacketizedLink::frame_sync_cc;


    py::class_<frame_sync_cc, gr::block, gr::basic_block,
        std::shared_ptr<frame_sync_cc>>(m, "frame_sync_cc", D(frame_sync_cc))

        .def(py::init(&frame_sync_cc::make),
           py::arg("preamble"),
           py::arg("preamble_constellation"),
           py::arg("detection_threshold"),
           py::arg("alpha"),
           py::arg("len_tag_key") = "packet_len",
           D(frame_sync_cc,make)
        )
        




        
        .def("set_preamble_constellation",&frame_sync_cc::set_preamble_constellation,       
            py::arg("preamble_constellation"),
            D(frame_sync_cc,set_preamble_constellation)
        )

        ;




}








