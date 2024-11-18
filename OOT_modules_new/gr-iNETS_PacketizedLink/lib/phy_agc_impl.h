/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_PHY_AGC_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_PHY_AGC_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/phy_agc.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class phy_agc_impl : public phy_agc
    {
     private:
      float d_decay_rate;
      float d_attack_rate;
      float d_reference;
      float d_gain;
      float d_max_gain;
      pmt::pmt_t d_me;
      pmt::pmt_t d_key;

     public:
      phy_agc_impl(float decay_rate, float attack_rate, float reference, float gain, float max_gain);
      ~phy_agc_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_PHY_AGC_IMPL_H */
