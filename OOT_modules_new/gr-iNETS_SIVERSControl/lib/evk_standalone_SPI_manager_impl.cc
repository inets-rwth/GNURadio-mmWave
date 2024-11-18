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

#include <gnuradio/io_signature.h>
#include <uhd/features/gpio_power_iface.hpp>
#include "evk_standalone_SPI_manager_impl.h"

typedef uhd::features::gpio_power_iface gpio_power;

namespace gr {
  namespace iNETS_SIVERSControl {

    evk_standalone_SPI_manager::sptr
    evk_standalone_SPI_manager::make(gr::uhd::usrp_source::sptr __gr_usrp_source,
                            const std::string &antenna_array_m,
    		                const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
    		                const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
    		                const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT)
    {
      return gnuradio::make_block_sptr<evk_standalone_SPI_manager_impl>(__gr_usrp_source, antenna_array_m,
    		                SPI_CLK_PIN, SPI_SDI_PIN, SPI_SDO_PIN, SPI_CS_PIN,
    		                SPI_CLK_DIVIDER, SPI_GPIO_PORT);
    }


    /*
     * The private constructor
     */
    evk_standalone_SPI_manager_impl::evk_standalone_SPI_manager_impl(gr::uhd::usrp_source::sptr __gr_usrp_source,
                            const std::string &antenna_array_m,
    		                const int &SPI_CLK_PIN, const int &SPI_SDI_PIN,
    		                const int &SPI_SDO_PIN, const int &SPI_CS_PIN,
    		                const int &SPI_CLK_DIVIDER, const std::string &SPI_GPIO_PORT)
      : gr::block("evk_standalone_SPI_manager",
              gr::io_signature::make(0 /* min inputs */, 0 /* max inputs */, 0),
              gr::io_signature::make(0 /* min outputs */, 0 /*max outputs */, 0))
    {
        // try to get the GNURadio USRP object
        try {
            gr_usrp = __gr_usrp_source;
        } catch(const std::runtime_error& err) {
            std::cerr << "Error while obtaining USRP source pointer." << std::endl;
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
            std::cerr << "Pointer to multi USRP object invalid." << std::endl;
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
            std::cerr << "Error while setting (multi) USRP up for SPI operation." << std::endl;
        }
        
        antenna_array_model = antenna_array_m;
        
        message_port_register_in(pmt::mp("index_in"));
        message_port_register_out(pmt::mp("index_out"));
        
        message_port_register_in(pmt::mp("beamsteering_protocol_msg"));
        
        set_msg_handler(pmt::mp("index_in"), [this](const pmt::pmt_t& msg) { this->handle_index_message(msg); });
        set_msg_handler(pmt::mp("beamsteering_protocol_msg"), [this](const pmt::pmt_t& msg) { this->handle_beamsteering_protocol_message(msg); });
    }

    /*
     * Our virtual destructor.
     */
    evk_standalone_SPI_manager_impl::~evk_standalone_SPI_manager_impl()
    {
    }
    
    /*
    void
    evk_standalone_SPI_manager_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
    #pragma message("implement a forecast that fills in how many items on each input you need to produce noutput_items and remove this warning")
      // <+forecast+> e.g. ninput_items_required[0] = noutput_items
    }
    */

    int
    evk_standalone_SPI_manager_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
      // Tell runtime system how many input items we consumed on
      // each input stream.
      consume_each (noutput_items);

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }
    
    void evk_standalone_SPI_manager_impl::handle_index_message(const pmt::pmt_t& msg) {
        int msg_idx = pmt::to_long(msg);
        uint32_t payload, readback;
        if (antenna_array_model == "EVK02001") {
            // if received index is in the appropiate range
            if ((0 <= msg_idx) && (msg_idx < 22)) {
                // std::cout << "[EVK Standalone SPI Manager] Writing beam ID " << msg_idx << " over SPI to the EVK02001." << std::endl;
                payload = 0x0e108000;
                payload |= ((msg_idx << 8) & 0x3f00);
                SPI_RW_WRAPPER(payload, 32);
            } else {
                std::cout << "[EVK Standalone SPI Manager] Invalid beam index. SPI write operation aborted." << std::endl;
            }
            // readback
            // std::cout << "[EVK Standalone SPI Manager] Reading beam ID over SPI from the " << antenna_array_model << std::endl;
            payload = 0x0e1400;
            readback = SPI_RW_WRAPPER(payload, 24);
            std::cout << "[EVK02001 Standalone SPI Manager] Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << std::endl; // bits 5:0
        }
        
        else { // EVK06002
            // if received index is in the appropiate range
            if ((msg_idx == 0) || ((22 <= msg_idx) && (msg_idx < 44))) {
                // std::cout << "[EVK Standalone SPI Manager] Writing beam ID " << msg_idx << " over SPI to the EVK06002." << std::endl;
                payload = 0x0d108000;
                payload |= ((msg_idx << 8) & 0x3f00);
                SPI_RW_WRAPPER(payload, 32);
            } else {
                std::cout << "[EVK Standalone SPI Manager] Invalid beam index. SPI write operation aborted." << std::endl;
            }
            // readback
            // std::cout << "[EVK Standalone SPI Manager] Reading beam ID over SPI from the " << antenna_array_model << std::endl;
            payload = 0x0d1400;
            readback = SPI_RW_WRAPPER(payload, 24);
            std::cout << "[EVK06002 Standalone SPI Manager] Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << " (beam no. " << (readback & 0x3F) - 21 << " with elevation = 0.0)" << std::endl; // bits 5:0
        }
        
        // send readback value to main block
        message_port_pub(pmt::mp("index_out"), pmt::from_long(readback & 0x3F));
    }
    
    void evk_standalone_SPI_manager_impl::handle_beamsteering_protocol_message(const pmt::pmt_t& msg) {
        int msg_idx = pmt::to_long(msg);
        uint32_t payload, readback;
        std::string output_msg = "[EVK Standalone SPI Manager] Active RF modes: ";
        
        // msg_idx == -1: switch to RX
        // msg_idx == -2: switch to TX
        // msg_idx >= 0: switch to given beam id
        if (msg_idx == -1) {
            std::cout << "[EVK Standalone SPI Manager] Setting the " << antenna_array_model << " to RX mode of operation over SPI." << std::endl;
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
            
            std::cout << "[EVK Standalone SPI Manager] Reading TX/RX status over SPI from the " << antenna_array_model << std::endl;
            readback = SPI_RW_WRAPPER(payload, 24);
            if (readback & 0x2) {
                output_msg.append("TX ");
            }
            if (readback & 0x1) {
                output_msg.append("RX");
            }
                
            std::cout << output_msg << std::endl;
        } else if (msg_idx == -2) {
            std::cout << "[EVK Standalone SPI Manager] Setting the " << antenna_array_model << " to TX mode of operation over SPI." << std::endl;
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
            
            std::cout << "[EVK Standalone SPI Manager] Reading TX/RX status over SPI from the " << antenna_array_model << std::endl;
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
                    //std::cout << "[EVK Standalone SPI Manager] Writing beam ID " << msg_idx << " over SPI to the EVK02001." << std::endl;
                    // write for RX beam ID
                    payload = 0x0e108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                    
                    // write for TX beam ID - to be used during link status report (lidar)
                    payload = 0x0b108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                } else {
                    std::cout << "[EVK Standalone SPI Manager] Invalid beam index. SPI write operation aborted." << std::endl;
                }
                // readback
                // std::cout << "[EVK Standalone SPI Manager] Reading beam ID over SPI from the " << antenna_array_model << std::endl;
                payload = 0x0e1400; // 0x0b1400 for TX beam ID read
                readback = SPI_RW_WRAPPER(payload, 24);
                std::cout << "[EVK02001 Standalone SPI Manager] RX Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << std::endl; // bits 5:0
            } else { // EVK06002
                // if received index is in the appropiate range
                if ((msg_idx == 0) || ((22 <= msg_idx) && (msg_idx < 44))) {
                    //std::cout << "[EVK Standalone SPI Manager] Writing beam ID " << msg_idx << " over SPI to the EVK06002.") << std::endl;
                    // write for RX beam ID
                    payload = 0x0d108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                    
                    // write for TX beam ID - to be used during link status report (lidar)
                    payload = 0x0a108000;
                    payload |= ((msg_idx << 8) & 0x3f00);
                    SPI_RW_WRAPPER(payload, 32);
                } else {
                    std::cout << "[EVK Standalone SPI Manager] Invalid beam index. SPI write operation aborted." << std::endl;
                }
                // readback
                //std::cout << "[EVK Standalone SPI Manager] Reading beam ID over SPI from the " << antenna_array_model << std::endl;
                payload = 0x0d1400; // 0x0a1400 for TX beam ID read
                readback = SPI_RW_WRAPPER(payload, 24);
                std::cout << "[EVK06002 Standalone SPI Manager] RX Beam ID after SPI interaction: " << std::dec << (readback & 0x3F) << " (beam no. " << (readback & 0x3F) - 21 << " with elevation = 0.0)" << std::endl; // bits 5:0
            }
        }
        // send readback value to main block
        //message_port_pub(pmt::mp("index_out"), pmt::from_long(readback & 0x3F));
    }
    
    uint32_t evk_standalone_SPI_manager_impl::SPI_RW_WRAPPER(uint32_t payload, uint8_t payload_length) {
        /*
        std::cout << "[EVK Standalone SPI Manager] Writing payload: 0x" << std::hex << payload << " with length "
                << std::dec << int(payload_length) << " bits" << std::endl
                << "Performing SPI transaction..." << std::endl;
        */
        
        uint32_t read_data = spi_ref->transact_spi(0, config, payload, payload_length, true);
        
        // std::cout << "[EVK Standalone SPI Manager] Data read: 0x" << std::hex << read_data << std::endl;
        
        return read_data;
    }

  } /* namespace iNETS_SIVERSControl */
} /* namespace gr */
