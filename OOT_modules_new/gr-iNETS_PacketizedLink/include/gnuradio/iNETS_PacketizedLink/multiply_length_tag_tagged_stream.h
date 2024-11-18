/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_MULTIPLY_LENGTH_TAG_TAGGED_STREAM_H
#define INCLUDED_INETS_PACKETIZEDLINK_MULTIPLY_LENGTH_TAG_TAGGED_STREAM_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API multiply_length_tag_tagged_stream : virtual public gr::block
    {
     public:
      typedef std::shared_ptr<multiply_length_tag_tagged_stream> sptr;

      /*!
       * \brief Make a tagged stream multiply_length block.
       *
       * \param lengthtagname Length tag key
       * \param mcstagname MCS tag key
       */
      static sptr make(const std::string &lengthtagname, const std::string &mcstagname);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_MULTIPLY_LENGTH_TAG_TAGGED_STREAM_H */
