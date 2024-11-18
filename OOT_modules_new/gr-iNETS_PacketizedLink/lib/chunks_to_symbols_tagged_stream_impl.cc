/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS, RWTH Aachen University.
 * Author: Florian Wischeler, updated by Niklas Beckmann
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */


#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "chunks_to_symbols_tagged_stream_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    chunks_to_symbols_tagged_stream::sptr
    chunks_to_symbols_tagged_stream::make(const std::string& mcs_tag_name)
    {
      return gnuradio::get_initial_sptr
        (new chunks_to_symbols_tagged_stream_impl(mcs_tag_name));
    }

    /*
     * The private constructor
     */
    chunks_to_symbols_tagged_stream_impl::chunks_to_symbols_tagged_stream_impl(const std::string& mcs_tag_name)
      : gr::tagged_stream_block("chunks_to_symbols_tagged_stream",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(1, 1, sizeof(gr_complex)), "packet_len"),
              d_mcs_tag_name(pmt::string_to_symbol(mcs_tag_name)),
              d_mcs(0)
    {
        d_constellation = gr::digital::constellation_bpsk::make()->base();
        d_dim = d_constellation->dimensionality();
    }

    /*
     * Our virtual destructor.
     */
    chunks_to_symbols_tagged_stream_impl::~chunks_to_symbols_tagged_stream_impl()
    {
    }

    int
    chunks_to_symbols_tagged_stream_impl::calculate_output_stream_length(const gr_vector_int &ninput_items)
    {
      int n_out_bytes_required = ninput_items[0] / d_dim;
      return n_out_bytes_required;
    }

    int
    chunks_to_symbols_tagged_stream_impl::work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const unsigned char *in = (unsigned char*)input_items[0];
	  gr_complex *out = (gr_complex*)output_items[0];
      //long consumed_items = 0;

      std::vector<tag_t> tags;
	  get_tags_in_range(tags, 0, nitems_written(0), nitems_written(0) + ninput_items[0], d_mcs_tag_name);
	  // if(tags.size() == 0) {		
      //   //throw std::runtime_error("[Chunks to Symbols Tagged Streams] No MCS tag in input stream");
      //   std::cout << "[Chunks to Symbols Tagged Streams] No MCS tag in input stream" << std::endl;
	  // }
	  
      // Get MCS Tag
      if (tags.size() > 1) {
        std::cout << "[Chunks to Symbols Tagged Streams] More than one MCS tag in input stream" << std::endl;
        d_mcs = pmt::to_long(tags[0].value);
      } else if (tags.size() == 1) {
        d_mcs = pmt::to_long(tags[0].value);
      }

      // Maps MCS to Constellation
      if (d_mcs <= 5) {
        d_constellation = gr::digital::constellation_bpsk::make()->base();
      } else if (d_mcs > 5 && d_mcs <= 9) {
        d_constellation = gr::digital::constellation_qpsk::make()->base();
      } else if (d_mcs > 10 && d_mcs <= 12) {
        d_constellation = gr::digital::constellation_16qam::make()->base();
      } else {
        std::cout << "[Chunks to Symbols Tagged Stream] Invalid MCS tag received" << std::endl;
      }

      for (int i = 0; i < ninput_items[0]; i++) {
        d_constellation->map_to_points(in[i], out + i);
	  }
      d_dim = d_constellation->dimensionality();

      // Tell runtime system how many output items we produced.
      return ninput_items[0];
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
