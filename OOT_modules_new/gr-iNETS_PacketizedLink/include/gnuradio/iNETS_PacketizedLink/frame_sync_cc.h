/* -*- c++ -*- */
/*
 * Copyright 2024 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_FRAME_SYNC_CC_H
#define INCLUDED_INETS_PACKETIZEDLINK_FRAME_SYNC_CC_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/block.h>
#include <gnuradio/digital/constellation.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API frame_sync_cc : virtual public gr::block
    {
     public:
      typedef std::shared_ptr<frame_sync_cc> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::frame_sync_cc.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::frame_sync_cc's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::frame_sync_cc::make is the public interface for
       * creating new instances.
       */
      static sptr make(const std::vector<int> &preamble, gr::digital::constellation_sptr preamble_constellation, float detection_threshold, double alpha, const std::string &len_tag_key = "packet_len");
      virtual void set_preamble_constellation(gr::digital::constellation_sptr preamble_constellation) = 0;
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_FRAME_SYNC_CC_H */
