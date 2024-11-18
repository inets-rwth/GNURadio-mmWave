/* -*- c++ -*- */
/*
 * Copyright 2024 iNETS.
 * Written by Berk Acikgoez. Adapted from evk02001_set_beams_TX_USB in the same OOT module.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_SIVERSCONTROL_EVK_SET_BEAMS_TX_SINGLE_SPI_H
#define INCLUDED_INETS_SIVERSCONTROL_EVK_SET_BEAMS_TX_SINGLE_SPI_H

#include <gnuradio/iNETS_SIVERSControl/api.h>
#include <gnuradio/tagged_stream_block.h>
#include <gnuradio/uhd/usrp_sink.h>

namespace gr {
  namespace iNETS_SIVERSControl {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_SIVERSControl
     *
     */
    class INETS_SIVERSCONTROL_API evk_set_beams_TX_single_SPI : virtual public gr::tagged_stream_block
    {
     public:
      typedef std::shared_ptr<evk_set_beams_TX_single_SPI> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_SIVERSControl::evk_set_beams_TX_single_SPI.
       *
       * To avoid accidental use of raw pointers, iNETS_SIVERSControl::evk_set_beams_TX_single_SPI's
       * constructor is in a private implementation
       * class. iNETS_SIVERSControl::evk_set_beams_TX_single_SPI::make is the public interface for
       * creating new instances.
       */
      static sptr make(gr::uhd::usrp_sink::sptr gr_usrp_sink, 
                    const std::string &length_tag_k, 
                    const std::string &beam_tag_k,
                    const int &initial_beam_index,
                    const std::string &antenna_array_m,
                    const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
                    const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
                    const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT,
                    const bool &fixed_beam_m);
    };

  } // namespace iNETS_SIVERSControl
} // namespace gr

#endif /* INCLUDED_INETS_SIVERSCONTROL_EVK_SET_BEAMS_TX_SINGLE_SPI_H */
