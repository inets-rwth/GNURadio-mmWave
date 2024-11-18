/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_CONSTELLATION_DECODER_TAGGED_STREAM_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_CONSTELLATION_DECODER_TAGGED_STREAM_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/constellation_decoder_tagged_stream.h>
#include <gnuradio/digital/constellation.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class constellation_decoder_tagged_stream_impl : public constellation_decoder_tagged_stream
    {
     private:
        gr::digital::constellation_sptr d_constellation;
        unsigned int d_dim;
        unsigned int d_mcs;
        pmt::pmt_t d_mcs_tag_name;

     public:
      constellation_decoder_tagged_stream_impl(const std::string& mcs_tag_name);
      ~constellation_decoder_tagged_stream_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);

    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_CONSTELLATION_DECODER_TAGGED_STREAM_IMPL_H */
