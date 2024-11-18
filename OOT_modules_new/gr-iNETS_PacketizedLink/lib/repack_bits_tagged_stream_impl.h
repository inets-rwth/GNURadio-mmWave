/* -*- c++ -*- */
/*
 * Copyright 2019 iNETS, RWTH Aachen University.
 *
 * Author: Florian Wischeler, Niklas Beckmann
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_REPACK_BITS_TAGGED_STREAM_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_REPACK_BITS_TAGGED_STREAM_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/repack_bits_tagged_stream.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class repack_bits_tagged_stream_impl : public repack_bits_tagged_stream
    {
     private:
      int d_mode; //! Operation mode: Pack (False) or Unpack (True)
      int d_k; //! Bits on input stream
      int d_l; //! Bits on output stream
      int d_in_index; // Current bit of input byte
      int d_out_index; // Current bit of output byte
      bool d_align_output; //! true if the output shall be aligned, false if the input shall be aligned
      endianness_t d_endianness;
      unsigned int d_mcs;

     protected:
      int calculate_output_stream_length(const gr_vector_int &ninput_items);

     public:
      repack_bits_tagged_stream_impl(bool mode, const std::string &len_tag_key="packet_len", const std::string &mcs_tag_key="mcs", bool align_output=false, endianness_t endianness=GR_LSB_FIRST);
      ~repack_bits_tagged_stream_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_int &ninput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_REPACK_BITS_TAGGED_STREAM_IMPL_H */
