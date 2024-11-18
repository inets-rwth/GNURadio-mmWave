/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_PHY_AGC_H
#define INCLUDED_INETS_PACKETIZEDLINK_PHY_AGC_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API phy_agc : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<phy_agc> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::phy_agc.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::phy_agc's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::phy_agc::make is the public interface for
       * creating new instances.
       */
      static sptr make(float decay_rate, float attack_rate, float reference, float gain, float max_gain);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_PHY_AGC_H */
