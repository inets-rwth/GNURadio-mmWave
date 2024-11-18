/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
 
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include <math.h>
#include "evm_biased_bpsk_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    evm_biased_bpsk::sptr
    evm_biased_bpsk::make(int number_of_header_samples)
    {
      return gnuradio::get_initial_sptr
        (new evm_biased_bpsk_impl(number_of_header_samples));
    }


    /*
     * The private constructor
     */
    evm_biased_bpsk_impl::evm_biased_bpsk_impl(int number_of_header_samples)
      : gr::sync_block("evm_biased_bpsk",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex)))
    {
        d_constellation_points = gr::digital::constellation_bpsk::make()->points();
        d_number_of_header_samples = number_of_header_samples;
        d_evm = 0;
        d_key = pmt::string_to_symbol("evm");
    }

    /*
     * Our virtual destructor.
     */
    evm_biased_bpsk_impl::~evm_biased_bpsk_impl()
    {
    }

    int
    evm_biased_bpsk_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      memcpy(output_items[0], input_items[0], noutput_items * sizeof(gr_complex));

      // Calculate biased EVM for BPSK Symbols
      for (int i = 0; i < noutput_items; i++) {
        // Biased EVM
        d_evm += std::min(std::norm(in[i]-d_constellation_points[0]), std::norm(in[i]-d_constellation_points[1]));
        // Reset EVM when packet header finished
        if ((i % (d_number_of_header_samples - 1)) == 0) {
          // Publish Tag
          pmt::pmt_t pmt_evm = pmt::from_double(10 * log10(d_evm / d_number_of_header_samples));
          add_item_tag(0, nitems_written(0) + i, d_key, pmt_evm);
          d_evm = 0;
        }
      }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
