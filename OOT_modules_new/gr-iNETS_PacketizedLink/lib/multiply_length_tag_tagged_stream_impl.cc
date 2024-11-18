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
#include "multiply_length_tag_tagged_stream_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    multiply_length_tag_tagged_stream::sptr
    multiply_length_tag_tagged_stream::make(const std::string &lengthtagname, const std::string &mcstagname)
    {
      return gnuradio::get_initial_sptr
        (new multiply_length_tag_tagged_stream_impl(lengthtagname, mcstagname));
    }


    /*
     * The private constructor
     */
    multiply_length_tag_tagged_stream_impl::multiply_length_tag_tagged_stream_impl(const std::string &lengthtagname, const std::string &mcstagname)
      : gr::block("multiply_length_tag_tagged_stream",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex))),
              d_lengthtag(pmt::mp(lengthtagname)),
              d_mcstag(pmt::mp(mcstagname)),
              d_scalar(8)
    {
        set_tag_propagation_policy(TPP_DONT);
        set_relative_rate(1);
    }

    /*
     * Our virtual destructor.
     */
    multiply_length_tag_tagged_stream_impl::~multiply_length_tag_tagged_stream_impl()
    {
    }

    int
    multiply_length_tag_tagged_stream_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      const void* in = input_items[0];
      void* out = output_items[0];
      int mcs = 0;
      bool mcs_tag_found = false;
      bool length_tag_found = false;
      int length_tag_offset = 0;
      long packet_len = 0;

      // move data across ( wasteful memcopy :< )
      memcpy(out, in, noutput_items*sizeof(gr_complex));

      // move and update tags
      std::vector<tag_t> tags;
      get_tags_in_range(tags, 0, nitems_read(0), nitems_read(0)+noutput_items);
      // First get all tags
      for (size_t i=0; i<tags.size(); i++) {
            if (pmt::eqv(tags[i].key , d_mcstag)) {
                // propagate with value update (scaled)
                mcs_tag_found = true;
                mcs = pmt::to_long(tags[i].value);
                // Maps MCS to Constellation
                if (mcs <= 5) {
                  d_scalar = 8;
                } else if (mcs > 5 && mcs <= 9) {
                  d_scalar = 4;
                } else if (mcs > 10 && mcs <= 12) {
                  d_scalar = 2;
                } else {
                  std::cout << "[Multiply Length Tag] Invalid MCS tag received" << std::endl;
                }
                
                add_item_tag(0, tags[i].offset, tags[i].key, tags[i].value, tags[i].srcid );
            }
            
            if(pmt::eqv(tags[i].key , d_lengthtag)) {
                // propagate with value update (scaled)
                length_tag_found = true;
                //std::cout << "[Multiply Length Tag] Length tag found" << std::endl;
                length_tag_offset = tags[i].offset;
                packet_len = pmt::to_long(tags[i].value);
            } else {
                // propagate unmodified
                add_item_tag(0, tags[i].offset, tags[i].key, tags[i].value, tags[i].srcid);
            }
      }
      
      // Propagate Length tag
      if (length_tag_found == true) {
        add_item_tag(0, length_tag_offset, d_lengthtag, pmt::from_long(packet_len * d_scalar));
      }

      consume_each(noutput_items);
      return noutput_items;
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
