/* -*- c++ -*- */
/*
 * Copyright 2024 iNETS.
 * Written by Berk Acikgoez. Adapted from evk02001_set_beams_TX_USB in the same OOT module.
 * SPI_RW_WRAPPER forked from https://github.com/EttusResearch/uhd/blob/master/host/examples/spi.cpp on 12.01.2024.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_SIVERSCONTROL_EVK_SET_BEAMS_TX_SINGLE_SPI_IMPL_H
#define INCLUDED_INETS_SIVERSCONTROL_EVK_SET_BEAMS_TX_SINGLE_SPI_IMPL_H

#include <gnuradio/iNETS_SIVERSControl/evk_set_beams_TX_single_SPI.h>
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

    class evk_set_beams_TX_single_SPI_impl : public evk_set_beams_TX_single_SPI
    {
     private:
      gr::uhd::usrp_sink::sptr gr_usrp;
      std::string length_tag_key;
      std::string beam_tag_key;
        
      multi_usrp::sptr m_usrp;
      std::vector<spi_pconf> periph_cfgs;
      spi_iface::sptr spi_ref;
      spi_config_t config;
      
      std::string antenna_array_model;
      bool fixed_beam_mode;  
      long packet_length;
      bool burst_transmission_complete;
      long number_of_samples_of_burst_left;
      bool packet_arrived;
      int beam_id;
      int beam_id_offset;
      int initial_beam_id;
      int tx_rf_gain;
      long all_consumed_items;
      
      void handle_beamsteering_protocol_message(const pmt::pmt_t& msg);
        
      uint32_t SPI_RW_WRAPPER(uint32_t payload, uint8_t payload_length);

     protected:
      //int calculate_output_stream_length(const gr_vector_int &ninput_items);
      
      // override the following two functions
      void parse_length_tags(const std::vector< std::vector< tag_t >> & tags, gr_vector_int & n_input_items_reqd);
      void update_length_tags(int n_produced, int n_ports);

     public:
      evk_set_beams_TX_single_SPI_impl(gr::uhd::usrp_sink::sptr gr_usrp_sink, 
                    const std::string &length_tag_k, 
                    const std::string &beam_tag_k,
                    const int &initial_beam_index,
                    const std::string &antenna_array_m,
                    const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
                    const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
                    const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT,
                    const bool &fixed_beam_m);
      ~evk_set_beams_TX_single_SPI_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_int &ninput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_SIVERSControl
} // namespace gr

#endif /* INCLUDED_INETS_SIVERSCONTROL_EVK_SET_BEAMS_TX_SINGLE_SPI_IMPL_H */
