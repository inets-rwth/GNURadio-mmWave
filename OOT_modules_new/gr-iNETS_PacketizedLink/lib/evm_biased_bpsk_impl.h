/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_EVM_BIASED_BPSK_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_EVM_BIASED_BPSK_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/evm_biased_bpsk.h>
#include <gnuradio/digital/constellation.h>
#include <pmt/pmt.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class evm_biased_bpsk_impl : public evm_biased_bpsk
    {
     private:
      std::vector<gr_complex> d_constellation_points;
      int d_number_of_header_samples;
      double d_evm;
      pmt::pmt_t d_key;

     public:
      evm_biased_bpsk_impl(int number_of_header_samples);
      ~evm_biased_bpsk_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_EVM_BIASED_BPSK_IMPL_H */
