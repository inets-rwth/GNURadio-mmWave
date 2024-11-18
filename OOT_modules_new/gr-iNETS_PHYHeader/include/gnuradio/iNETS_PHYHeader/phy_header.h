/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PHYHEADER_PHY_HEADER_H
#define INCLUDED_INETS_PHYHEADER_PHY_HEADER_H

#include <gnuradio/iNETS_PHYHeader/api.h>
#include <gnuradio/digital/packet_header_default.h>
#include <gnuradio/block.h>

namespace gr {
  namespace iNETS_PHYHeader {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PHYHeader
     *
     */
    class INETS_PHYHEADER_API phy_header : virtual public digital::packet_header_default
    {
     public:
      typedef std::shared_ptr<phy_header> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PHYHeader::phy_header.
       *
       * To avoid accidental use of raw pointers, iNETS_PHYHeader::phy_header's
       * constructor is in a private implementation
       * class. iNETS_PHYHeader::phy_header::make is the public interface for
       * creating new instances.
       */
      static sptr make();
      
     protected:
      phy_header();
    };

  } // namespace iNETS_PHYHeader
} // namespace gr

#endif /* INCLUDED_INETS_PHYHEADER_PHY_HEADER_H */
