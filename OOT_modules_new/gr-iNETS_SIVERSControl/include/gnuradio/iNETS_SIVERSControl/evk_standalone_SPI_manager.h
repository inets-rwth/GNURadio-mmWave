/* -*- c++ -*- */
/*
 * Standalone SPI manager that allows for a variety of use cases.
 *
 * Copyright 2024 iNETS.
 * Written by Berk Acikgoez.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_SIVERSCONTROL_EVK_STANDALONE_SPI_MANAGER_H
#define INCLUDED_INETS_SIVERSCONTROL_EVK_STANDALONE_SPI_MANAGER_H

#include <gnuradio/iNETS_SIVERSControl/api.h>
#include <gnuradio/block.h>
#include <gnuradio/uhd/usrp_source.h>

namespace gr {
  namespace iNETS_SIVERSControl {

    /*!
     * \brief <+description of block+>
     * \ingroup iNETS_SIVERSControl
     *
     */
    class INETS_SIVERSCONTROL_API evk_standalone_SPI_manager : virtual public gr::block
    {
     public:
      typedef std::shared_ptr<evk_standalone_SPI_manager> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of iNETS_SIVERSControl::evk_standalone_SPI_manager.
       *
       * To avoid accidental use of raw pointers, iNETS_SIVERSControl::evk_standalone_SPI_manager's
       * constructor is in a private implementation
       * class. iNETS_SIVERSControl::evk_standalone_SPI_manager::make is the public interface for
       * creating new instances.
       */
      static sptr make(gr::uhd::usrp_source::sptr __gr_usrp_source,
                            const std::string &antenna_array_m,
    		                const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
    		                const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
    		                const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT);
    };

  } // namespace iNETS_SIVERSControl
} // namespace gr

#endif /* INCLUDED_INETS_SIVERSCONTROL_EVK_STANDALONE_SPI_MANAGER_H */
