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
/* BINDTOOL_HEADER_FILE(phy_agc.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(87bd678b476e1b4483b630eb2a583e96)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/iNETS_PacketizedLink/phy_agc.h>
// pydoc.h is automatically generated in the build directory
#include <phy_agc_pydoc.h>

void bind_phy_agc(py::module& m)
{

    using phy_agc    = ::gr::iNETS_PacketizedLink::phy_agc;


    py::class_<phy_agc, gr::sync_block, gr::block, gr::basic_block,
        std::shared_ptr<phy_agc>>(m, "phy_agc", D(phy_agc))

        .def(py::init(&phy_agc::make),
           py::arg("decay_rate"),
           py::arg("attack_rate"),
           py::arg("reference"),
           py::arg("gain"),
           py::arg("max_gain"),
           D(phy_agc,make)
        )
        



        ;




}








