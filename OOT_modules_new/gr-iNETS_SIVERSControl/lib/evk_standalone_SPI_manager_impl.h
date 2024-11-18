/* -*- c++ -*- */
/*
 * Standalone SPI manager that allows for a variety of use cases.
 *
 * Copyright 2024 iNETS.
 * Written by Berk Acikgoez.
 * SPI_RW_WRAPPER forked from https://github.com/EttusResearch/uhd/blob/master/host/examples/spi.cpp on 12.01.2024.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_SIVERSCONTROL_EVK_STANDALONE_SPI_MANAGER_IMPL_H
#define INCLUDED_INETS_SIVERSCONTROL_EVK_STANDALONE_SPI_MANAGER_IMPL_H

#include <gnuradio/iNETS_SIVERSControl/evk_standalone_SPI_manager.h>
#include <uhd/usrp/multi_usrp.hpp>
#include <uhd/features/spi_getter_iface.hpp>
#include <pmt/pmt.h>

typedef uhd::usrp::multi_usrp multi_usrp;
typedef uhd::features::spi_getter_iface spi_getter_iface;
typedef uhd::features::spi_periph_config_t spi_pconf;
typedef uhd::spi_iface spi_iface;
typedef uhd::spi_config_t spi_config_t;

namespace gr {
  namespace iNETS_SIVERSControl {

    class evk_standalone_SPI_manager_impl : public evk_standalone_SPI_manager
    {
     private:
        // TODO: Allow for either sink or source to be used as USRP object.
        gr::uhd::usrp_source::sptr gr_usrp;
        multi_usrp::sptr m_usrp;
        std::vector<spi_pconf> periph_cfgs;
        spi_iface::sptr spi_ref;
        spi_config_t config;
        std::string antenna_array_model;
        
        void handle_index_message(const pmt::pmt_t& msg);
        void handle_beamsteering_protocol_message(const pmt::pmt_t& msg);
        
        uint32_t SPI_RW_WRAPPER(uint32_t payload, uint8_t payload_length);

     public:
      evk_standalone_SPI_manager_impl(gr::uhd::usrp_source::sptr __gr_usrp_source,
                            const std::string &antenna_array_m,
    		                const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
    		                const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
    		                const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT);
      ~evk_standalone_SPI_manager_impl();

      // Where all the action really happens
      //void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);

    };

  } // namespace iNETS_SIVERSControl
} // namespace gr

#endif /* INCLUDED_INETS_SIVERSCONTROL_EVK_STANDALONE_SPI_MANAGER_IMPL_H */
