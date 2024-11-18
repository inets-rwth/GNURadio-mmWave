/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_MULTIPLY_LENGTH_TAG_TAGGED_STREAM_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_MULTIPLY_LENGTH_TAG_TAGGED_STREAM_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/multiply_length_tag_tagged_stream.h>
#include <vector>
#include <pmt/pmt.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class multiply_length_tag_tagged_stream_impl : public multiply_length_tag_tagged_stream
    {
     private:
      pmt::pmt_t d_lengthtag;
      pmt::pmt_t d_mcstag;
      double d_scalar;
      size_t d_itemsize;

     public:
      multiply_length_tag_tagged_stream_impl(const std::string &lengthtagname, const std::string &mcstagname);
      ~multiply_length_tag_tagged_stream_impl();

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);

    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_MULTIPLY_LENGTH_TAG_TAGGED_STREAM_IMPL_H */
