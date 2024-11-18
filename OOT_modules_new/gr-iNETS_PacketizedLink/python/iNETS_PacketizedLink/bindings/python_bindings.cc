/*
 * Copyright 2020 Free Software Foundation, Inc.
 *
 * This file is part of GNU Radio
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 */

#include <pybind11/pybind11.h>

#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <numpy/arrayobject.h>

namespace py = pybind11;

// Headers for binding functions
/**************************************/
// The following comment block is used for
// gr_modtool to insert function prototypes
// Please do not delete
/**************************************/
// BINDING_FUNCTION_PROTOTYPES(
    void bind_baseband_derotation(py::module& m);
    void bind_baseband_derotation_tagged_stream(py::module& m);
    void bind_chunks_to_symbols_tagged_stream(py::module& m);
    void bind_constellation_decoder_tagged_stream(py::module& m);
    void bind_estimate_dBm_ff(py::module& m);
    void bind_evm_biased_bpsk(py::module& m);
    void bind_frame_sync_cc(py::module& m);
    void bind_multiply_length_tag_tagged_stream(py::module& m);
    void bind_packet_header_parser(py::module& m);
    void bind_phase_freq_correction(py::module& m);
    void bind_phy_agc(py::module& m);
    void bind_phy_header_payload_demux(py::module& m);
    void bind_repack_bits_tagged_stream(py::module& m);
// ) END BINDING_FUNCTION_PROTOTYPES


// We need this hack because import_array() returns NULL
// for newer Python versions.
// This function is also necessary because it ensures access to the C API
// and removes a warning.
void* init_numpy()
{
    import_array();
    return NULL;
}

PYBIND11_MODULE(iNETS_PacketizedLink_python, m)
{
    // Initialize the numpy C API
    // (otherwise we will see segmentation faults)
    init_numpy();

    // Allow access to base block methods
    py::module::import("gnuradio.gr");

    /**************************************/
    // The following comment block is used for
    // gr_modtool to insert binding function calls
    // Please do not delete
    /**************************************/
    // BINDING_FUNCTION_CALLS(
    bind_baseband_derotation(m);
    bind_baseband_derotation_tagged_stream(m);
    bind_chunks_to_symbols_tagged_stream(m);
    bind_constellation_decoder_tagged_stream(m);
    bind_estimate_dBm_ff(m);
    bind_evm_biased_bpsk(m);
    bind_frame_sync_cc(m);
    bind_multiply_length_tag_tagged_stream(m);
    bind_packet_header_parser(m);
    bind_phase_freq_correction(m);
    bind_phy_agc(m);
    bind_phy_header_payload_demux(m);
    bind_repack_bits_tagged_stream(m);
    // ) END BINDING_FUNCTION_CALLS
}