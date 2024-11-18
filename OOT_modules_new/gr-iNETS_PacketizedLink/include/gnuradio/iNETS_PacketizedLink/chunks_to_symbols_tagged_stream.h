/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_CHUNKS_TO_SYMBOLS_TAGGED_STREAM_H
#define INCLUDED_INETS_PACKETIZEDLINK_CHUNKS_TO_SYMBOLS_TAGGED_STREAM_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/tagged_stream_block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API chunks_to_symbols_tagged_stream : virtual public gr::tagged_stream_block
    {
     public:
      typedef std::shared_ptr<chunks_to_symbols_tagged_stream> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::chunks_to_symbols_tagged_stream.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::chunks_to_symbols_tagged_stream's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::chunks_to_symbols_tagged_stream::make is the public interface for
       * creating new instances.
       */
      static sptr make(const std::string& mcs_tag_name);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_CHUNKS_TO_SYMBOLS_TAGGED_STREAM_H */
