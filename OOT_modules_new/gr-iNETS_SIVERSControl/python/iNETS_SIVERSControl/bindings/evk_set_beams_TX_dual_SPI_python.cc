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
/* BINDTOOL_HEADER_FILE(evk_set_beams_TX_dual_SPI.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(3426f5d77c3d42d349bab015d9068b24)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/iNETS_SIVERSControl/evk_set_beams_TX_dual_SPI.h>
// pydoc.h is automatically generated in the build directory
#include <evk_set_beams_TX_dual_SPI_pydoc.h>

void bind_evk_set_beams_TX_dual_SPI(py::module& m)
{

    using evk_set_beams_TX_dual_SPI    = ::gr::iNETS_SIVERSControl::evk_set_beams_TX_dual_SPI;


    py::class_<evk_set_beams_TX_dual_SPI, gr::tagged_stream_block, gr::block, gr::basic_block,
        std::shared_ptr<evk_set_beams_TX_dual_SPI>>(m, "evk_set_beams_TX_dual_SPI", D(evk_set_beams_TX_dual_SPI))

        .def(py::init(&evk_set_beams_TX_dual_SPI::make),
           py::arg("gr_usrp_sink"),
           py::arg("length_tag_k"),
           py::arg("beam_tag_k"),
           py::arg("initial_beam_index"),
           py::arg("SPI_CLK_PIN_28"),
           py::arg("SPI_SDI_PIN_28"),
           py::arg("SPI_SDO_PIN_28"),
           py::arg("SPI_CS_PIN_28"),
           py::arg("SPI_CLK_PIN_60"),
           py::arg("SPI_SDI_PIN_60"),
           py::arg("SPI_SDO_PIN_60"),
           py::arg("SPI_CS_PIN_60"),
           py::arg("SPI_CLK_DIVIDER"),
           py::arg("SPI_GPIO_PORT"),
           D(evk_set_beams_TX_dual_SPI,make)
        )
        



        ;




}








