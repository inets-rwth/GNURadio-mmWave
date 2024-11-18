/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS, RWTH Aachen University.
 *
 * Author: Florian Wischeler, updated by Niklas Beckmann
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_REPACK_BITS_TAGGED_STREAM_H
#define INCLUDED_INETS_PACKETIZEDLINK_REPACK_BITS_TAGGED_STREAM_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/tagged_stream_block.h>
#include <gnuradio/endianness.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief Repack k bits from the input stream onto l bits of the output stream. Depending on the mode you choose, the bits are either packed or unpacked.
     * Unpacking means in this regard that the byte sample input is assumed to contain 8 relevant bits which are then distributed on 8/constellation.bits_per_symbol with each byte sample output containing constellation.bits_per_symbol() relevant bits.
     * Packing means in this regard that the byte sample input is assumed to contain constellation.bits_per_symbol() relevant bits per input byte sample. Then 8/constellation.bits_per_symbol() bytes samples are merged together in one output byte sample with 8 relevant bits.
     * \ingroup iNETS_PacketizedLink
     * 
     * \details
     * This block operates on tagged streams. For correct operation it is required to provide packet_len and mcs tags.
     *
     */
    class INETS_PACKETIZEDLINK_API repack_bits_tagged_stream : virtual public gr::tagged_stream_block
    {
     public:
      typedef std::shared_ptr<repack_bits_tagged_stream> sptr;

      /*!
       * \param tsb_tag_key If not empty, this is the key for the length tag.
       * \param align_output If tsb_tag_key is given, this controls if the input
       *                     or the output is aligned.
       * \param endianness The endianness of the output data stream (LSB or MSB).
       */
      static sptr make(bool mode, const std::string &len_tag_key="paket_len", const std::string &mcs_tag_key="mcs", bool align_output=false, endianness_t endianness=GR_LSB_FIRST);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_REPACK_BITS_TAGGED_STREAM_H */
