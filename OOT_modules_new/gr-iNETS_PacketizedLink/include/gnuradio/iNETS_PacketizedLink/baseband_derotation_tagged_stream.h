/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_TAGGED_STREAM_H
#define INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_TAGGED_STREAM_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API baseband_derotation_tagged_stream : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<baseband_derotation_tagged_stream> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::baseband_derotation_tagged_stream.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::baseband_derotation_tagged_stream's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::baseband_derotation_tagged_stream::make is the public interface for
       * creating new instances.
       */
      static sptr make(float mu);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_BASEBAND_DEROTATION_TAGGED_STREAM_H */
