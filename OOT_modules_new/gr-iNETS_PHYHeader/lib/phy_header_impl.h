/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PHYHEADER_PHY_HEADER_IMPL_H
#define INCLUDED_INETS_PHYHEADER_PHY_HEADER_IMPL_H

#include <gnuradio/iNETS_PHYHeader/phy_header.h>
#include <boost/enable_shared_from_this.hpp>
#include <boost/crc.hpp>
#include <boost/cstdint.hpp>
#include <gnuradio/tags.h>
#include <gnuradio/digital/api.h>

namespace gr {
  namespace iNETS_PHYHeader {

    class phy_header_impl : public phy_header
    {
     private:
      int get_bit(int byte, int index);

     public:
      phy_header_impl();
      ~phy_header_impl();

      bool header_formatter(long packet_len, unsigned char* out, const std::vector<tag_t>& tags);
      bool header_parser(const unsigned char* header, std::vector<tag_t>& tags);
    };

  } // namespace iNETS_PHYHeader
} // namespace gr

#endif /* INCLUDED_INETS_PHYHEADER_PHY_HEADER_IMPL_H */
