/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS, RWTH Aachen University.
 * Author: Florian Wischeler, updated by Niklas Beckmann
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_CHUNKS_TO_SYMBOLS_TAGGED_STREAM_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_CHUNKS_TO_SYMBOLS_TAGGED_STREAM_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/chunks_to_symbols_tagged_stream.h>
#include <gnuradio/digital/constellation.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class chunks_to_symbols_tagged_stream_impl : public chunks_to_symbols_tagged_stream
    {
     private:
      std::shared_ptr<gr::digital::constellation> d_constellation;
      pmt::pmt_t d_mcs_tag_name;
      unsigned int d_mcs;
      unsigned int d_dim;

     protected:
      int calculate_output_stream_length(const gr_vector_int &ninput_items);

     public:
      chunks_to_symbols_tagged_stream_impl(const std::string& mcs_tag_name);
      ~chunks_to_symbols_tagged_stream_impl();

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

#endif /* INCLUDED_INETS_PACKETIZEDLINK_CHUNKS_TO_SYMBOLS_TAGGED_STREAM_IMPL_H */
