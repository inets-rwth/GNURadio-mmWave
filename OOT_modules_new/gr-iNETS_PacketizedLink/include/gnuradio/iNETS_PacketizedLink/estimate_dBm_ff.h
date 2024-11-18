/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_ESTIMATE_DBM_FF_H
#define INCLUDED_INETS_PACKETIZEDLINK_ESTIMATE_DBM_FF_H

#include <gnuradio/iNETS_PacketizedLink/api.h>
#include <gnuradio/sync_block.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_PacketizedLink
     *
     */
    class INETS_PACKETIZEDLINK_API estimate_dBm_ff : virtual public gr::sync_block
    {
     public:
      typedef std::shared_ptr<estimate_dBm_ff> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_PacketizedLink::estimate_dBm_ff.
       *
       * To avoid accidental use of raw pointers, iNETS_PacketizedLink::estimate_dBm_ff's
       * constructor is in a private implementation
       * class. iNETS_PacketizedLink::estimate_dBm_ff::make is the public interface for
       * creating new instances.
       */
      static sptr make(float alpha, int sps, int N);
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_ESTIMATE_DBM_FF_H */
