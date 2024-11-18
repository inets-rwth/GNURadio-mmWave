/* -*- c++ -*- */
/*
 * Copyright 2019 iNETS, RWTH Aachen University.
 *
 * Author: Florian Wischeler, Niklas Beckmann
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "repack_bits_tagged_stream_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    repack_bits_tagged_stream::sptr
    /*
     * param mode describtion
     * param len_tag_key describtion
     * param mcs_tag_key describtion
    */
    repack_bits_tagged_stream::make(bool mode, const std::string &len_tag_key, const std::string &mcs_tag_key, bool align_output, endianness_t endianness)
    {
      return gnuradio::get_initial_sptr
        (new repack_bits_tagged_stream_impl(mode, len_tag_key, mcs_tag_key, align_output, endianness));
    }
    
    /*
     * The private constructor
     */
    repack_bits_tagged_stream_impl::repack_bits_tagged_stream_impl(bool mode, const std::string &len_tag_key, const std::string &mcs_tag_key, bool align_output, endianness_t endianness)
      : gr::tagged_stream_block("repack_bits_tagged_stream",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(1, 1, sizeof(char)), len_tag_key),
        d_mode(mode),
        d_in_index(0), d_out_index(0),
        d_align_output(align_output),
        d_endianness(endianness),
        d_mcs(0)
    {
      if (d_mode == false) //Pack bits
      {
        d_k = 1; //Values are set to worst case values since constellation.bits_per_symbol is unknown and individual for each packet
        d_l = 8;
      }
      else //Unpack bits
      {
        d_k = 8; //Values are set to worst case values since constellation.bits_per_symbol is unknown and individual for each packet
        d_l = 1;
      }
      set_relative_rate((double) d_k / d_l);
    }

    /*
     * Our virtual destructor.
     */
    repack_bits_tagged_stream_impl::~repack_bits_tagged_stream_impl()
    {
    }

    int
    repack_bits_tagged_stream_impl::calculate_output_stream_length(const gr_vector_int &ninput_items)
    {
      // Maybe needs to be set to worst case values here
      int n_out_bytes_required = (ninput_items[0] * d_k) / d_l;
      if ((ninput_items[0] * d_k) % d_l && !d_align_output) {
        n_out_bytes_required++;
      }
      return n_out_bytes_required;
    }

    int
    repack_bits_tagged_stream_impl::work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      gr::thread::scoped_lock guard(d_setlock);
      const unsigned char *in = (const unsigned char *) input_items[0];
      unsigned char *out = (unsigned char *) output_items[0];
      int bytes_to_write = noutput_items;

      // Read MCS tag and set d_k and d_l
      // define global MCS loookup table
      std::vector<tag_t> mcs_tags;
      get_tags_in_window(mcs_tags, 0, 0, ninput_items[0], pmt::intern("mcs"));
      if (mcs_tags.size() == 0) {
        std::cout << "[Tagged Stream Repack Bits] ERROR: No MCS tag received." << std::endl;
      } //else if (mcs_tags.size() > 1) { // Ignore
        //std::cout << "[Tagged Stream Repack Bits] ERROR: More than 1 MCS tag received. List size: " << mcs_tags.size() << std::endl;
      //}

      int bits_per_symbol = 1;
      
      for (int i = 0; i < noutput_items; i++) {
        // Get MCS Tag
        for (std::vector<gr::tag_t>::size_type j = 0; j < mcs_tags.size(); j++) {
          if (mcs_tags[j].offset == (nitems_written(0) + i)) {
            d_mcs = pmt::to_long(mcs_tags[j].value);
            //std::cout << "[Tagged Stream Repack Bits] Received MCS tag " << d_mcs << std::endl;
          }
        }
      }
      if (d_mcs <= 5) {
        bits_per_symbol = 1;
      } else if (d_mcs > 5 && d_mcs <= 9) {
        bits_per_symbol = 2;
      } else if (d_mcs > 10 && d_mcs <= 12) {
        bits_per_symbol = 4;
      } else {
        std::cout << "[Tagged Stream Repack Bits] Invalid MCS tag received" << std::endl;
      }

      if (d_mode == false) { //Pack bits
        d_k = bits_per_symbol;
        d_l = 8;
      } else {
        d_k = 8;
        d_l = bits_per_symbol;
      }
      set_relative_rate((double) d_k / d_l);

      // noutput_items could be larger than necessary --> Set aligment
      int bytes_to_read = ninput_items[0];
      bytes_to_write = bytes_to_read * d_k / d_l;
      if (!d_align_output && (((bytes_to_read * d_k) % d_l) != 0)) {
        bytes_to_write++;
      }

      int n_read = 0;
      int n_written = 0;
      switch(d_endianness) {
        case GR_LSB_FIRST:
          while(n_written < bytes_to_write && n_read < ninput_items[0]) {
            if(d_out_index == 0) { // Starting a fresh byte
              out[n_written] = 0;
            }
            out[n_written] |= ((in[n_read] >> d_in_index) & 0x01) << d_out_index;

            d_in_index = (d_in_index + 1) % d_k;
            d_out_index = (d_out_index + 1) % d_l;
            if (d_in_index == 0) {
              n_read++;
              d_in_index = 0;
            }
            if (d_out_index == 0) {
              n_written++;
              d_out_index = 0;
            }
          }

          if (d_out_index) {
            n_written++;
            d_out_index = 0;
          }
          break;

        case GR_MSB_FIRST:
          while (n_written < bytes_to_write && n_read < ninput_items[0]) {
            if (d_out_index == 0) { // Starting a fresh byte
              out[n_written] = 0;
            }
            out[n_written] |= ((in[n_read] >> (d_k - 1 - d_in_index)) & 0x01) << (d_l - 1 - d_out_index);

            d_in_index = (d_in_index + 1) % d_k;
            d_out_index = (d_out_index + 1) % d_l;
            if (d_in_index == 0) {
              n_read++;
              d_in_index = 0;
            }
            if (d_out_index == 0) {
              n_written++;
              d_out_index = 0;
            }
          }
          if (d_out_index) {
            n_written++;
            d_out_index = 0;
          }
          break;

        default:
          throw std::runtime_error("[Tagged Stream Repack Bits] ERROR: Unrecognized endianness value.");
      }
      return n_written;
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
