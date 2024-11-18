/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_CONSTELLATION_DECODER_TAGGED_STREAM_H
#define INCLUDED_INETS_PACKETIZEDLINK_CONSTELLATION_DECODER_TAGGED_STREAM_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API constellation_decoder_tagged_stream : virtual public gr::block
    {
     public:
      typedef std::shared_ptr<constellation_decoder_tagged_stream> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::constellation_decoder_tagged_stream.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::constellation_decoder_tagged_stream's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::constellation_decoder_tagged_stream::make is the public interface for
       * creating new instances.
       */
      static sptr make(const std::string& mcs_tag_name);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_CONSTELLATION_DECODER_TAGGED_STREAM_H */
