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
#include "constellation_decoder_tagged_stream_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    constellation_decoder_tagged_stream::sptr
    constellation_decoder_tagged_stream::make(const std::string& mcs_tag_name)
    {
      return gnuradio::get_initial_sptr
        (new constellation_decoder_tagged_stream_impl(mcs_tag_name));
    }

    /*
     * The private constructor
     */
    constellation_decoder_tagged_stream_impl::constellation_decoder_tagged_stream_impl(const std::string& mcs_tag_name)
      : gr::block("constellation_decoder_tagged_stream",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(unsigned char))),
              d_mcs_tag_name(pmt::string_to_symbol(mcs_tag_name)), d_mcs(0)
    {
        // worst case
        d_constellation = gr::digital::constellation_16qam::make()->base();
        d_dim = d_constellation->dimensionality();
        set_relative_rate(1.0 / ((double)d_dim));
    }

    /*
     * Our virtual destructor.
     */
    constellation_decoder_tagged_stream_impl::~constellation_decoder_tagged_stream_impl()
    {
    }

    void
    constellation_decoder_tagged_stream_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
        unsigned int input_required = noutput_items * d_dim;

        unsigned ninputs = ninput_items_required.size();
        for (unsigned int i = 0; i < ninputs; i++) {
            ninput_items_required[i] = input_required;
        }
    }

    int
    constellation_decoder_tagged_stream_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      gr_complex const *in = (const gr_complex*)input_items[0];
      unsigned char *out = (unsigned char*)output_items[0];

      std::vector<tag_t> mcs_tags;
      get_tags_in_window(mcs_tags, 0, 0, noutput_items, d_mcs_tag_name);
      
      for (int i = 0; i < noutput_items; i++) {
        // Get MCS Tag
        for (int j = 0; j < mcs_tags.size(); j++) {
            if (mcs_tags[j].offset == (nitems_written(0) + i)) {
                d_mcs = pmt::to_long(mcs_tags[j].value);
                //std::cout << "[Tagged Stream Constellation Decoder] Received MCS tag " << d_mcs << std::endl;
            }
        }

        // Maps MCS to Constellation
        if (d_mcs <= 5) {
          d_constellation = gr::digital::constellation_bpsk::make()->base();
        } else if (d_mcs > 5 && d_mcs <= 9) {
          d_constellation = gr::digital::constellation_qpsk::make()->base();
        } else if (d_mcs > 10 && d_mcs <= 12) {
          d_constellation = gr::digital::constellation_16qam::make()->base();
        } else {
          std::cout << "[Constellation Decoder Tagged Stream] Invalid MCS tag received" << std::endl;
        }
        d_dim = d_constellation->dimensionality();

        //Constellation Decoding
	    out[i] = d_constellation->decision_maker(&(in[i*d_dim]));
      }

      // Tell runtime system how many input items we consumed on each input stream.
      consume_each (noutput_items);

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
