/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include <boost/format.hpp>
#include "packet_header_parser_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    packet_header_parser::sptr
    packet_header_parser::make(long header_len, const std::string &len_tag_key)
    {
      const gr::digital::packet_header_default::sptr header_formatter(new gr::digital::packet_header_default(header_len, len_tag_key));
      return gnuradio::get_initial_sptr (new packet_header_parser_impl(header_formatter));
    }
    
    packet_header_parser::sptr
    packet_header_parser::make(const gr::digital::packet_header_default::sptr &header_formatter, bool print_warnings)
    {
      return gnuradio::get_initial_sptr
        (new packet_header_parser_impl(header_formatter, print_warnings));
    }

    /*
     * The private constructor
     */
    packet_header_parser_impl::packet_header_parser_impl(const gr::digital::packet_header_default::sptr &header_formatter, bool print_warnings)
      : gr::sync_block("packet_header_parser",
              gr::io_signature::make(1, 1, sizeof(unsigned char)),
              gr::io_signature::make(0, 0, 0)),
              d_header_formatter(header_formatter),
              d_port(pmt::mp("header_data")),
              d_print_warnings(print_warnings)
    {
        message_port_register_out(d_port);
        set_output_multiple(header_formatter->header_len());
    }

    /*
     * Our virtual destructor.
     */
    packet_header_parser_impl::~packet_header_parser_impl()
    {
    }

    int
    packet_header_parser_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const unsigned char *in = (const unsigned char *) input_items[0];

      if (noutput_items < d_header_formatter->header_len()) {
	      return 0;
      }

      std::vector<tag_t> tags;
      get_tags_in_range(tags, 0, nitems_read(0), nitems_read(0)+d_header_formatter->header_len());

      if (!d_header_formatter->header_parser(in, tags)) {
        if (d_print_warnings) {
           std::cout << "Detected an invalid packet" << std::endl;
        }
        message_port_pub(d_port, pmt::PMT_F);
      } else {
        pmt::pmt_t dict(pmt::make_dict());
        for (unsigned i = 0; i < tags.size(); i++) {
          dict = pmt::dict_add(dict, tags[i].key, tags[i].value);
        }
	    message_port_pub(d_port, dict);
      }

      return d_header_formatter->header_len();
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
