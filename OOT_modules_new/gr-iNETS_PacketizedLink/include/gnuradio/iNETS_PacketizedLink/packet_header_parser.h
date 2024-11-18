/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_PACKET_HEADER_PARSER_H
#define INCLUDED_INETS_PACKETIZEDLINK_PACKET_HEADER_PARSER_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>
#include <gnuradio/digital/packet_header_default.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief Post header metadata as a PMT
     * \ingroup packet_operators_blk
     *
     * \details
     * In a sense, this is the inverse block to packet_headergenerator_bb.
     * The difference is, the parsed header is not output as a stream,
     * but as a PMT dictionary, which is published to message port with
     * the id "header_data".
     *
     * The dictionary consists of the tags created by the header formatter
     * object. You should be able to use the exact same formatter object
     * as used on the Tx side in the packet_headergenerator_bb.
     *
     * If only a header length is given, this block uses the default header
     * format.
     *
     */
    class INETS_PACKETIZEDLINK_API packet_header_parser : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<packet_header_parser> sptr;

     /*!
       * \param header_formatter Header object. This should be the same as used for
       *                         packet_headergenerator_bb.
       */
      static sptr make(const gr::digital::packet_header_default::sptr& header_formatter, bool print_warnings);
      /*!
       * \param header_len Number of bytes per header
       * \param len_tag_key Length Tag Key
       */
      static sptr make(long header_len, const std::string& len_tag_key);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_PACKET_HEADER_PARSER_H */
