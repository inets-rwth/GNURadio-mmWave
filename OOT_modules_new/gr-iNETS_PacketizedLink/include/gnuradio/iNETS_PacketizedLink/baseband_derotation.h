/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_H
#define INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>
#include <gnuradio/digital/constellation.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API baseband_derotation : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<baseband_derotation> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::baseband_derotation.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::baseband_derotation's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::baseband_derotation::make is the public interface for
       * creating new instances.
       */
      static sptr make(float mu, gr::digital::constellation_sptr constellation);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_H */
