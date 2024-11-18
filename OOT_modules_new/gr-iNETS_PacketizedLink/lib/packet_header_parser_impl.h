/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_PACKET_HEADER_PARSER_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_PACKET_HEADER_PARSER_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/packet_header_parser.h>

namespace gr {
  namespace iNETS_PacketizedLink {

    class packet_header_parser_impl : public packet_header_parser
    {
     private:
      gr::digital::packet_header_default::sptr d_header_formatter;
      const pmt::pmt_t d_port;
      bool d_print_warnings;

     public:
      packet_header_parser_impl(const gr::digital::packet_header_default::sptr &header_formatter, bool print_warnings=false);
      ~packet_header_parser_impl();

      // Where all the action really happens
      int work(
              int noutput_items,
              gr_vector_const_void_star &input_items,
              gr_vector_void_star &output_items
      );
    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_PACKET_HEADER_PARSER_IMPL_H */
