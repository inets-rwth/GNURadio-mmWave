/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_ESTIMATE_DBM_FF_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_ESTIMATE_DBM_FF_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/estimate_dBm_ff.h>
#include <pmt/pmt.h>

namespace gr {
  namespace iNETS_PacketizedLink {
  
    #define EPS 0.0000000000001

    class estimate_dBm_ff_impl : public estimate_dBm_ff
    {
     private:
        double d_avg;
        double d_beta;
        double d_alpha;
        int i_sps;
        int i_N;
        int i_counter;
        double d_last_sent_rss;
        pmt::pmt_t d_key;

     public:
      estimate_dBm_ff_impl(float alpha, int sps, int N);
      ~estimate_dBm_ff_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_ESTIMATE_DBM_FF_IMPL_H */
