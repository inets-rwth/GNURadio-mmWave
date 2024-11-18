/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_PHY_HEADER_PAYLOAD_DEMUX_H
#define INCLUDED_INETS_PACKETIZEDLINK_PHY_HEADER_PAYLOAD_DEMUX_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API phy_header_payload_demux : virtual public gr::block
    {
     public:
      typedef std::shared_ptr<phy_header_payload_demux> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::phy_header_payload_demux.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::phy_header_payload_demux's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::phy_header_payload_demux::make is the public interface for
       * creating new instances.
       */
      static sptr make(int header_len, int symbols_per_header_byte, int guard_interval, const std::string &length_tag_key, const std::string &mcs_tag_key, const std::string &trigger_tag_key, bool output_symbols, size_t itemsize, const std::string &timing_tag_key, int samp_rate, const std::vector<std::string> &special_tags, const size_t header_padding);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_PHY_HEADER_PAYLOAD_DEMUX_H */
