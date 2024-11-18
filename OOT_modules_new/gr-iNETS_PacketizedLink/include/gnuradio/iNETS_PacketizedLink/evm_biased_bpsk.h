/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_EVM_BIASED_BPSK_H
#define INCLUDED_INETS_PACKETIZEDLINK_EVM_BIASED_BPSK_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API evm_biased_bpsk : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<evm_biased_bpsk> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::evm_biased_bpsk.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::evm_biased_bpsk's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::evm_biased_bpsk::make is the public interface for
       * creating new instances.
       */
      static sptr make(int number_of_header_samples);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_EVM_BIASED_BPSK_H */
