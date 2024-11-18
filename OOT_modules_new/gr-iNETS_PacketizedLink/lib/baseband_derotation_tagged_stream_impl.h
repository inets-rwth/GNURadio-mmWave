/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_TAGGED_STREAM_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_TAGGED_STREAM_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/baseband_derotation_tagged_stream.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class baseband_derotation_tagged_stream_impl : public baseband_derotation_tagged_stream
    {
     private:
        float f_mu;
        float f_error;
        int i_mcs;
        float wrap_phase(float phi);

     public:
      baseband_derotation_tagged_stream_impl(float mu);
      ~baseband_derotation_tagged_stream_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_TAGGED_STREAM_IMPL_H */
