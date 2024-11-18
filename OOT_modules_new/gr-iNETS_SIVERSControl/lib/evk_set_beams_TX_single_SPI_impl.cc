/* -*- c++ -*- */
/*
 * Copyright 2024 iNETS.
 * Written by Berk Acikgoez. Adapted from evk02001_set_beams_TX_USB in the same OOT module.
 * SPI_RW_WRAPPER forked from https://github.com/EttusResearch/uhd/blob/master/host/examples/spi.cpp on 12.01.2024.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <gnuradio/io_signature.h>
#include <gnuradio/basic_block.h>
#include <boost/pointer_cast.hpp>
#include <uhd/features/gpio_power_iface.hpp>
#include "evk_set_beams_TX_single_SPI_impl.h"

typedef uhd::features::gpio_power_iface gpio_power;
typedef uhd::stream_args_t str_args_t;

namespace gr {
  namespace iNETS_SIVERSControl {

    using input_type = gr_complex;
    using output_type = gr_complex;
    evk_set_beams_TX_single_SPI::sptr
    evk_set_beams_TX_single_SPI::make(gr::uhd::usrp_sink::sptr gr_usrp_sink, 
                    const std::string &length_tag_k, 
                    const std::string &beam_tag_k,
                    const int &initial_beam_index,
                    const std::string &antenna_array_m,
                    const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
                    const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
                    const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT,
                    const bool &fixed_beam_m)
    {
      return gnuradio::make_block_sptr<evk_set_beams_TX_single_SPI_impl>(gr_usrp_sink, length_tag_k, beam_tag_k,
                                    initial_beam_index, antenna_array_m,
                                    SPI_CLK_PIN, SPI_SDI_PIN, SPI_SDO_PIN,
                                    SPI_CS_PIN, SPI_CLK_DIVIDER, SPI_GPIO_PORT,
                                    fixed_beam_m);
    }


    /*
     * The private constructor
     */
    evk_set_beams_TX_single_SPI_impl::evk_set_beams_TX_single_SPI_impl(gr::uhd::usrp_sink::sptr gr_usrp_sink, 
                                    const std::string &length_tag_k, 
                                    const std::string &beam_tag_k,
                                    const int &initial_beam_index,
                                    const std::string &antenna_array_m,
                                    const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
                                    const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
                                    const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT,
                                    const bool &fixed_beam_m)
      : gr::tagged_stream_block("evk_set_beams_TX_single_SPI",
              gr::io_signature::make(1 /* min inputs */, 1 /* max inputs */, sizeof(input_type)),
              gr::io_signature::make(1 /* min outputs */, 1 /*max outputs */, sizeof(output_type)), length_tag_k)
    {
        // try to get the GNURadio USRP object
        try {
            gr_usrp = gr_usrp_sink;
        } catch(const std::runtime_error& err) {
            std::cerr << "Error while obtaining USRP sink pointer." << std::endl;
        }
        
        if (!gr_usrp) {
            std::cerr << "USRP pointer is not valid." << std::endl;
        }
        
        // try to get the corresponding multi USRP object
        try {
            m_usrp = gr_usrp -> get_device();
        } catch(const std::runtime_error& err) {
            std::cerr << "Rutnime error while getting the underlying MultiUSRP object." << std::endl;
        }
        
        if (!m_usrp) {
            std::cerr << "Pointer to MultiUSRP object invalid." << std::endl;
        }
        
        // try to set up for SPI
        try {
            // set GPIO pin sources
            std::vector<std::string> sources{"DB0_SPI", "DB0_SPI", "DB0_SPI", "DB0_SPI", 
                                            "DB0_SPI", "DB0_SPI", "DB0_SPI", "DB0_SPI", 
                                            "DB0_SPI", "DB0_SPI", "DB0_SPI", "DB0_SPI"};
            m_usrp->set_gpio_src(SPI_GPIO_PORT, sources);
            
            // set GPIO logic voltage level (3V3)
            gpio_power & gpio_handle = m_usrp->get_mb_controller().get_feature<gpio_power>();
            gpio_handle.set_port_voltage(SPI_GPIO_PORT, "3V3");
            
            // add 12 to all pin numbers if GPIO1 is used
            int shift_if_GPIO1;
            if (SPI_GPIO_PORT == "GPIO1") {
                shift_if_GPIO1 = 12;
            } else {
                shift_if_GPIO1 = 0;
            }
            
            // Create peripheral configuration per peripheral
            spi_pconf periph_cfg;
            periph_cfg.periph_clk = SPI_CLK_PIN + shift_if_GPIO1;
            periph_cfg.periph_sdi = SPI_SDI_PIN + shift_if_GPIO1;
            periph_cfg.periph_sdo = SPI_SDO_PIN + shift_if_GPIO1;
            periph_cfg.periph_cs  = SPI_CS_PIN + shift_if_GPIO1;
            
            // Set the data direction register
            uint32_t outputs = 0x0;
            outputs |= 1 << periph_cfg.periph_clk;
            outputs |= 1 << periph_cfg.periph_sdo;
            outputs |= 1 << periph_cfg.periph_cs;
            m_usrp->set_gpio_attr("GPIOA", "DDR", outputs & 0xFFFFFF);
            
            // set control register
            m_usrp->set_gpio_attr("GPIOA", "CTRL", 0, 0xFFFFFF);
            
            // get SPI controller
            auto & spi_get_iface = m_usrp->get_radio_control().get_feature<spi_getter_iface>();
            
            periph_cfgs.push_back(periph_cfg);
            spi_ref = spi_get_iface.get_spi_ref(periph_cfgs);
            
            // The spi_config_t holds items like the clock divider and the SDI and SDO edges
            config.divider            = SPI_CLK_DIVIDER;
            config.use_custom_divider = true;
            config.mosi_edge          = config.EDGE_RISE;
            config.miso_edge          = config.EDGE_RISE;
            
        } catch(const std::runtime_error& err) {
            std::cerr << "Error while setting USRP up for SPI operation." << std::endl;
        }
        
        // tag propagation policy - let no tags pass
        set_tag_propagation_policy(gr::block::tag_propagation_policy_t::TPP_DONT);
        
        length_tag_key = length_tag_k;
        beam_tag_key = beam_tag_k;
        
        antenna_array_model = antenna_array_m;
        // if EVK06002 is used, offset all beam IDs by 21 so that beams with elevation = 0.0 are selected.
        if (antenna_array_model == "EVK06002") {
            beam_id_offset = 21;
        } else {
            beam_id_offset = 0;
        }
        
        fixed_beam_mode = fixed_beam_m;
        
        packet_length = 0;
        burst_transmission_complete = true;
        number_of_samples_of_burst_left = 0;
        packet_arrived = false;
        initial_beam_id = initial_beam_index;
        beam_id = initial_beam_index;
        tx_rf_gain = 0xFF;
        all_consumed_items = 0;
        
        message_port_register_in(pmt::mp("beamsteering_protocol_msg"));
        
        set_msg_handler(pmt::mp("beamsteering_protocol_msg"), [this](const pmt::pmt_t& msg) { this->handle_beamsteering_protocol_message(msg); });
        
    }

    /*
     * Our virtual destructor.
     */
    evk_set_beams_TX_single_SPI_impl::~evk_set_beams_TX_single_SPI_impl()
    {
    }

    /* no need to implement this
    int
    evk_set_beams_TX_single_SPI_impl::calculate_output_stream_length(const gr_vector_int &ninput_items)
    {
      #pragma message("set the following appropriately and remove this warning")
      int noutput_items = 0;
      return noutput_items ;
    }
    */
    
    // override parse_length_tags to not remove the length tag so that we can use the length tag later on
    // code copied from the original definition of tagged_stream_block (gnuradio/gnuradio-runtime/lib), minor modifications
    void evk_set_beams_TX_single_SPI_impl::parse_length_tags(const std::vector<std::vector<tag_t>> & tags,
		            gr_vector_int & n_input_items_reqd) {
        for (unsigned i = 0; i < tags.size(); i++) {
            for (unsigned k = 0; k < tags[i].size(); k++) {
                if (tags[i][k].key == pmt::string_to_symbol(length_tag_key)) {
                    n_input_items_reqd[i] = pmt::to_long(tags[i][k].value);
                }
            }
        }
    }
    
    // prevent it from adding length tags on its own
    void evk_set_beams_TX_single_SPI_impl::update_length_tags(int n_produced, int n_ports) {
        return;
    }

    int
    evk_set_beams_TX_single_SPI_impl::work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      auto in = static_cast<const input_type*>(input_items[0]);
      auto out = static_cast<output_type*>(output_items[0]);

      /************** adapt evk02001_set_beams_TX_USB **************/
      
      // Reset consumed_items back to zero every time the work function is called
      long nin_items = ninput_items[0];
      int consumed_items = 0;
      
      // collect tags
      unsigned long samp0_count = nitems_read(0);
      std::vector <tag_t> tags;
      get_tags_in_range(tags, 0, samp0_count, samp0_count + nin_items);      
      
      //std::cout << "length_tag_key: " << length_tag_key << std::endl;
      //std::cout << "beam_tag_key: " << beam_tag_key << std::endl;
      
      //std::cout << "no of tags: " << std::dec << tags.size() << std::endl;
      //std::cout << "samp count: " << samp0_count << std::endl;
      //std::cout << "nin_items: " << nin_items << std::endl;
      //std::cout << "noutput_items: " << noutput_items << std::endl;
      
      /*
      std::vector <tag_t> tags_test;
      get_tags_in_range(tags_test, 0, 0, 2 * samp0_count + 1);
      
      std::cout << "tags_test size: " << tags_test.size() << std::endl;
      
      if (tags_test.size() > 0) {
        for (unsigned int i = 0; i < tags_test.size(); i++)
            std::cout << "tag " << i << ", name: " << tags_test[i].key << ", offset: " << tags_test[i].offset << std::endl;
      }
      */
      
      if (tags.size() > 0) {
        for (unsigned int i = 0; i < tags.size(); i++) {
            // std::cout << "tag " << i << ": " << tags[i].key << "(offset: " << tags[i].offset << ")" << std::endl;
            if (pmt::equal(tags[i].key, pmt::intern(length_tag_key))) { // length tag found
                // Actually this cannot happen, but to be sure we check here again that the tag is at the beginning of the burst
                if (tags[i].offset != samp0_count) {
                    std::cout << "[EVK Set Beams TX Single SPI] Error: length_tag not at the beginning of the burst!" << std::endl;
                    break;
                }
                packet_length = pmt::to_long(tags[i].value);
                
                if (burst_transmission_complete == true) {
                    number_of_samples_of_burst_left = packet_length;
                    packet_arrived = true;
                }
                
            } else if (pmt::equal(tags[i].key, pmt::intern(beam_tag_key))) { // beam tag found
                // Actually this cannot happen, but to be sure we check here again that the tag is at the beginning of the burst
                if (tags[i].offset != samp0_count) {
                    std::cout << "[EVK Set Beams TX Single SPI] ErrSet Beams TX Dual SPIor: beam_id tag not at the beginning of the burst!" << std::endl;
                    break;
                }
                
                beam_id = pmt::to_long(tags[i].value);
                
                if (beam_id > 63 || beam_id < 0) {
                    std::cout << "[EVK Set Beams TX Single SPI] Error: Beam ID should be between 0 and 63. Setting beam ID to 0." << std::endl;
                    beam_id = 0;
                }
                
            } else if (pmt::equal(tags[i].key, pmt::intern("tx_RF_gain"))) { // RF gain tag found
                // Actually this cannot happen, but to be sure we check here again that the tag is at the beginning of the burst
                if (tags[i].offset != samp0_count) {
                    std::cout << "[EVK Set Beams TX Single SPI] Error: RF gain tag not at the beginning of the burst!" << std::endl;
                    break;
                }
                
                tx_rf_gain = pmt::to_long(tags[i].value);
                
                if (tx_rf_gain > 0xFF || tx_rf_gain < 0x00) {
                    std::cout << "[EVK Set Beams TX Single SPI] Error: TX RF gain tag should be between 0x00 and 0xFF. Setting RF gain to 0x00." << std::endl;
                    tx_rf_gain = 0x00;
                }
            }
            
            // ignore other tags
        }
      }
      
      // initialize payload object
      uint32_t payload = 0;
      uint32_t readback;
      
      // Arrived packet can be processed since it is valid
      
      if (number_of_samples_of_burst_left > 0 && packet_arrived == true) {
        burst_transmission_complete = false;
        
        // set beam ID if the program is not in fixed beam mode
        if (!fixed_beam_mode) {
        
            // set main TX beam direction
            //std::cout << "Writing beam id " << std::dec << beam_id << " over SPI to the " << antenna_array_model << std::endl;
            
            if (antenna_array_model == "EVK02001") {
                payload = 0x0b108000;    
            } else { // EVK06002
                payload = 0x0a108000;
            }
            
            payload |= (((beam_id + beam_id_offset) << 8) & 0x3f00);
            SPI_RW_WRAPPER(payload, 32);
            
            //std::cout << "Reading beam id over SPI from the " << antenna_array_model << std::endl;
            
            if (antenna_array_model == "EVK02001") {
                payload = 0x0b1400;   
            } else { // EVK06002
                payload = 0x0a1400;
            }
            
            readback = SPI_RW_WRAPPER(payload, 24);
            
            if (antenna_array_model == "EVK02001") {
                std::cout << "[EVK02001] Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << std::endl; // bits 5:0  
            } else { // EVK06002
                std::cout << "[EVK06002] Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << " (beam no. " << (readback & 0x3F) - beam_id_offset << " with elevation = 0.0)" << std::endl; // bits 5:0
            }
        }
        
        // get current time to create timestamp
        auto updated_time = std::chrono::system_clock::now();
        long updated_time_full_seconds = long(std::chrono::duration_cast<std::chrono::seconds>(updated_time.time_since_epoch()).count());
        double updated_time_frac_seconds = (double(std::chrono::duration_cast<std::chrono::microseconds>(updated_time.time_since_epoch()).count()) / 1000000.0) - double(updated_time_full_seconds);
        
        // add updated timestamp to tag
        add_item_tag(0, nitems_written(0), pmt::intern("tx_time"), pmt::make_tuple(pmt::from_long(updated_time_full_seconds), pmt::from_double(updated_time_frac_seconds + 0.027))); // 0.015
        
        // the following line is already executed by tagged_stream_block::update_length_tags, unless overriden
        add_item_tag(0, nitems_written(0), pmt::intern(length_tag_key), pmt::from_long(packet_length));
       
        if (number_of_samples_of_burst_left >= nin_items) {
          consumed_items = nin_items;
        }
        else {
          consumed_items = number_of_samples_of_burst_left;
        }
          
        // Due to forecast manipulation and scheduler problems, ensure that consumed input items fit in output
        consumed_items = std::min(consumed_items, noutput_items);
        number_of_samples_of_burst_left -= consumed_items;
          
        if (number_of_samples_of_burst_left < 0) {
          std::cout << "[EVK Set Beams TX Single SPI] ERROR: Number of samples left negative!" << std::endl;
        }
        
        // just assuming transmission is complete (for all practical purposes)
        burst_transmission_complete = true;
          
        // Output
        for (int i = 0; i < consumed_items; i++) {
          out[i] = in[i];
        }
      }
      
      all_consumed_items += consumed_items;
      
      /*
      std::cout << "nin_items: " << std::dec << nin_items << std::endl;
      std::cout << "noutput_items: " << std::dec << noutput_items << std::endl;
      std::cout << "packet_length: " << packet_length << std::endl;
      std::cout << "consumed_items: " << consumed_items << std::endl;
      std::cout << "no. samples burst left: " << number_of_samples_of_burst_left << std::endl << std::endl;
      */
      
      return consumed_items;
    }
    
    void evk_set_beams_TX_single_SPI_impl::handle_beamsteering_protocol_message(const pmt::pmt_t& msg) {
        int msg_idx = pmt::to_long(msg);
        uint32_t payload, readback;
        std::string output_msg = "[EVK Set Beams TX Single SPI] Active RF modes: ";
        
        // msg_idx == -1: switch to RX
        // msg_idx == -2: switch to TX
        // msg_idx >= 0: switch to given beam id
        if (msg_idx == -1) {
            std::cout << "[EVK Set Beams TX Single SPI] Setting the " << antenna_array_model << " to RX mode of operation over SPI." << std::endl;
            if (antenna_array_model == "EVK02001") {
                // disable TX
                payload = 0x0f010200;
                SPI_RW_WRAPPER(payload, 32);
                
                // enable RX
                payload = 0x0f020100;
                SPI_RW_WRAPPER(payload, 32);
                
                // set payload for readback
                payload = 0x0f0400;
                
            } else { // EVK06002
                // disable TX
                payload = 0x0e010200;
                SPI_RW_WRAPPER(payload, 32);
                
                // enable RX
                payload = 0x0e020100;
                SPI_RW_WRAPPER(payload, 32);
                
                // set payload for readback
                payload = 0x0e0400;
            }
            
            std::cout << "[EVK Set Beams TX Single SPI] Reading TX/RX status over SPI from the " << antenna_array_model << std::endl;
            readback = SPI_RW_WRAPPER(payload, 24);
            if (readback & 0x2) {
                output_msg.append("TX ");
            }
            if (readback & 0x1) {
                output_msg.append("RX");
            }
                
            std::cout << output_msg << std::endl;
            
        } else if (msg_idx == -2) {
            std::cout << "[EVK Set Beams TX Single SPI] Setting the " << antenna_array_model << " to TX mode of operation over SPI." << std::endl;
            if (antenna_array_model == "EVK02001") {
                // disable RX
                payload = 0x0f010100;
                SPI_RW_WRAPPER(payload, 32);
                
                // enable TX
                payload = 0x0f020200;
                SPI_RW_WRAPPER(payload, 32);
                
                // set payload for readback
                payload = 0x0f0400;
                
            } else { // EVK06002
                // disable RX
                payload = 0x0e010100;
                SPI_RW_WRAPPER(payload, 32);
                
                // enable TX
                payload = 0x0e020200;
                SPI_RW_WRAPPER(payload, 32);
                
                // set payload for readback
                payload = 0x0e0400;
            }
            
            std::cout << "[EVK Set Beams TX Single SPI] Reading TX/RX status over SPI from the " << antenna_array_model << std::endl;
            readback = SPI_RW_WRAPPER(payload, 24);
            if (readback & 0x2) {
                output_msg.append("TX ");
            }
            if (readback & 0x1) {
                output_msg.append("RX");
            }
                
            std::cout << output_msg << std::endl;
        } else {
            if (antenna_array_model == "EVK02001") {
                // if received index is in the appropiate range
                if ((0 <= msg_idx) && (msg_idx < 22)) {
                    std::cout << "[EVK Set Beams TX Single SPI] Writing beam ID " << msg_idx << " over SPI to the EVK02001." << std::endl;
                    // write for RX beam ID
                    payload = 0x0e108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                    
                    // write for TX beam ID
                    payload = 0x0b108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                    
                } else {
                    std::cout << "[EVK Set Beams TX Single SPI] Invalid beam index. SPI write operation aborted." << std::endl;
                }
                // readback
                std::cout << "[EVK Set Beams TX Single SPI] Reading beam ID over SPI from the " << antenna_array_model << std::endl;
                payload = 0x0b1400; // 0x0e1400 for RX beam ID read
                readback = SPI_RW_WRAPPER(payload, 24);
                std::cout << "[EVK Set Beams TX Single SPI] TX Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << std::endl; // bits 5:0
                
            } else { // EVK06002
                // if received index is in the appropiate range
                if ((msg_idx == 0) || ((22 <= msg_idx) && (msg_idx < 44))) {
                    std::cout << "[EVK Set Beams TX Single SPI] Writing beam ID " << msg_idx << " over SPI to the EVK06002." << std::endl;
                    // write for RX beam ID - to be used during link status report (lidar)
                    payload = 0x0d108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                    
                    // write for TX beam ID
                    payload = 0x0a108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                    
                } else {
                    std::cout << "[EVK Set Beams TX Single SPI] Invalid beam index. SPI write operation aborted." << std::endl;
                }
                // readback
                std::cout << "[EVK Set Beams TX Single SPI] Reading beam ID over SPI from the " << antenna_array_model << std::endl;
                payload = 0x0a1400; // 0x0d1400 for RX beam ID read
                readback = SPI_RW_WRAPPER(payload, 24);
                std::cout << "[EVK Set Beams TX Single SPI] TX Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << " (beam no. " << (readback & 0x3F) - 21 << " with elevation = 0.0)" << std::endl; // bits 5:0
            }
        }
        // send readback value to main block
        //message_port_pub(pmt::mp("index_out"), pmt::from_long(readback & 0x3F));
    }
    
    uint32_t evk_set_beams_TX_single_SPI_impl::SPI_RW_WRAPPER(uint32_t payload, uint8_t payload_length) {
        /*
        std::cout << "Writing payload: 0x" << std::hex << payload << " with length "
                << std::dec << int(payload_length) << " bits" << std::endl
                << "Performing SPI transaction..." << std::endl;
        */
        uint32_t read_data = spi_ref->transact_spi(0, config, payload, payload_length, true);
        
        //std::cout << "Data read: 0x" << std::hex << read_data << std::endl;
        
        return read_data;
    }

  } /* namespace iNETS_SIVERSControl */
} /* namespace gr */
