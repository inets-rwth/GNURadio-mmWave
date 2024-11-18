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
/* BINDTOOL_HEADER_FILE(evk_standalone_SPI_manager.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(670938d6b5b7ea1950f4373abe3fd07c)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/iNETS_SIVERSControl/evk_standalone_SPI_manager.h>
// pydoc.h is automatically generated in the build directory
#include <evk_standalone_SPI_manager_pydoc.h>

void bind_evk_standalone_SPI_manager(py::module& m)
{

    using evk_standalone_SPI_manager    = ::gr::iNETS_SIVERSControl::evk_standalone_SPI_manager;


    py::class_<evk_standalone_SPI_manager, gr::block, gr::basic_block,
        std::shared_ptr<evk_standalone_SPI_manager>>(m, "evk_standalone_SPI_manager", D(evk_standalone_SPI_manager))

        .def(py::init(&evk_standalone_SPI_manager::make),
           py::arg("__gr_usrp_source"),
           py::arg("antenna_array_m"),
           py::arg("SPI_CLK_PIN"),
           py::arg("SPI_SDI_PIN"),
           py::arg("SPI_SDO_PIN"),
           py::arg("SPI_CS_PIN"),
           py::arg("SPI_CLK_DIVIDER"),
           py::arg("SPI_GPIO_PORT"),
           D(evk_standalone_SPI_manager,make)
        )
        



        ;




}








