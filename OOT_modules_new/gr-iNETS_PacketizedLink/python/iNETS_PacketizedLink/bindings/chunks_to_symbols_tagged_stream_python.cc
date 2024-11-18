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
/* BINDTOOL_HEADER_FILE(chunks_to_symbols_tagged_stream.h)                                        */
/* BINDTOOL_HEADER_FILE_HASH(58b40f1a414f467970bdd0986e74727c)                     */
/***********************************************************************************/

#include <pybind11/complex.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace py = pybind11;

#include <gnuradio/iNETS_PacketizedLink/chunks_to_symbols_tagged_stream.h>
// pydoc.h is automatically generated in the build directory
#include <chunks_to_symbols_tagged_stream_pydoc.h>

void bind_chunks_to_symbols_tagged_stream(py::module& m)
{

    using chunks_to_symbols_tagged_stream    = ::gr::iNETS_PacketizedLink::chunks_to_symbols_tagged_stream;


    py::class_<chunks_to_symbols_tagged_stream, gr::tagged_stream_block, gr::block, gr::basic_block,
        std::shared_ptr<chunks_to_symbols_tagged_stream>>(m, "chunks_to_symbols_tagged_stream", D(chunks_to_symbols_tagged_stream))

        .def(py::init(&chunks_to_symbols_tagged_stream::make),
           py::arg("mcs_tag_name"),
           D(chunks_to_symbols_tagged_stream,make)
        )
        



        ;




}








