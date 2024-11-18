/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_PHASE_FREQ_CORRECTION_H
#define INCLUDED_INETS_PACKETIZEDLINK_PHASE_FREQ_CORRECTION_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API phase_freq_correction : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<phase_freq_correction> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::phase_freq_correction.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::phase_freq_correction's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::phase_freq_correction::make is the public interface for
       * creating new instances.
       */
      static sptr make(int num_preamble_samples);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_PHASE_FREQ_CORRECTION_H */
