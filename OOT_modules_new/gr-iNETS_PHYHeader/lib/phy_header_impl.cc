/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#include <gnuradio/io_signature.h>
#include "phy_header_impl.h"

namespace gr {
  namespace iNETS_PHYHeader {

    phy_header::sptr phy_header::make()
    {
      return phy_header::sptr(new phy_header_impl());
    }

    phy_header::phy_header() : packet_header_default(64, "packet_len"){}


    phy_header_impl::phy_header_impl() : packet_header_default(64, "packet_len") {}


    phy_header_impl::~phy_header_impl() {}
    

    int phy_header_impl::get_bit(int byte, int index) { return (byte & (1 << index) ? 1 : 0); }

    bool
    phy_header_impl::header_formatter(long packet_len, unsigned char* out, const std::vector<tag_t>& tags)
    {
      boost::crc_basic<16> d_crc_impl(0x1021, 0xFFFF, 0, false, false);
      bool mcs_found = false;
      bool scrambler_seed_found = false;
      bool type_found = false;
      bool trn_len_found = false;
      bool beam_track_req_found = false;
      bool last_rssi_found = false;
	    long mcs = 0;
	    long len = packet_len;
      long scrambler_seed = 0;
      long type = 0;
      long trn_len = 0;
      long beam_track_req = 0;
      long last_rssi;

	    // read tags
      for (int i = 0; i < tags.size(); i++) {
        if (pmt::eq(tags[i].key, pmt::mp("mcs"))) {
          mcs_found = true;
          mcs = pmt::to_long(tags[i].value);
        } else if (pmt::eq(tags[i].key, pmt::mp("scrambler_seed"))) {
          scrambler_seed_found = true;
          scrambler_seed = pmt::to_long(tags[i].value);
        } else if (pmt::eq(tags[i].key, pmt::mp("packet_type"))) {
          type_found = true;
          type = pmt::to_long(tags[i].value);
        } else if (pmt::eq(tags[i].key, pmt::mp("trn_len"))) {
          trn_len_found = true;
          trn_len = pmt::to_long(tags[i].value);
        } else if (pmt::eq(tags[i].key, pmt::mp("beam_track_req"))) {
          beam_track_req_found = true;
          beam_track_req = pmt::to_long(tags[i].value);
        } else if (pmt::eq(tags[i].key, pmt::mp("last_rssi"))) {
          last_rssi_found = true;
          last_rssi = pmt::to_long(tags[i].value);
        }
      }

      // check if all tags are present
      if ((!mcs_found) || (!type_found) || (!trn_len_found) || (!last_rssi_found)) {
        std::cout << "[PHY header] Not all required tags received" << std::endl;
        //return false;
      }

      // Header fields

      // LSB first
      // first 7 bits represent the scrambler initialization
      out[ 0] = get_bit(scrambler_seed, 0);
      out[ 1] = get_bit(scrambler_seed, 1);
      out[ 2] = get_bit(scrambler_seed, 2);
      out[ 3] = get_bit(scrambler_seed, 3);
      out[ 4] = get_bit(scrambler_seed, 4);
      out[ 5] = get_bit(scrambler_seed, 5);
      out[ 6] = get_bit(scrambler_seed, 6);

      // bits 7 to 11 represent the modulation and coding scheme
      out[ 7] = get_bit(mcs, 0);
      out[ 8] = get_bit(mcs, 1);
      out[ 9] = get_bit(mcs, 2);
      out[10] = get_bit(mcs, 3);
      out[11] = get_bit(mcs, 4);

      // bits 12 to 29 represent the packet length
      out[12] = get_bit(len,  0);
      out[13] = get_bit(len,  1);
      out[14] = get_bit(len,  2);
      out[15] = get_bit(len,  3);
      out[16] = get_bit(len,  4);
      out[17] = get_bit(len,  5);
      out[18] = get_bit(len,  6);
      out[19] = get_bit(len,  7);
      out[20] = get_bit(len,  8);
      out[21] = get_bit(len,  9);
      out[22] = get_bit(len, 10);
      out[23] = get_bit(len, 11);
      out[24] = get_bit(len, 12);
      out[25] = get_bit(len, 13);
      out[26] = get_bit(len, 14);
      out[27] = get_bit(len, 15);
      out[28] = get_bit(len, 16);
      out[29] = get_bit(len, 17);

      // bit 30 is the "Additional PPDU" field and is set to 0 here
      out[30] = 0;

      // bit 31 is the "Packet Type" field
      out[31] = get_bit(type,  0);

      // bits 32 to 36 represent the TRN length
      out[32] = get_bit(trn_len,  0);
      out[33] = get_bit(trn_len,  1);
      out[34] = get_bit(trn_len,  2);
      out[35] = get_bit(trn_len,  3);
      out[36] = get_bit(trn_len,  4);

      // bit 37 is the "Aggregation" field and is set to 0 here
      out[37] = 0;

      // bit 38 is the "Beam Tracking Request" field
      out[38] = get_bit(beam_track_req,  0);

      // bits 39 to 42 represent the "Last RSSI" field and is set to 0 here
      out[39] = get_bit(last_rssi,  0);
      out[40] = get_bit(last_rssi,  1);
      out[41] = get_bit(last_rssi,  2);
      out[42] = get_bit(last_rssi,  3);

      // bit 43 is the "Turnaround" field and is set to 0 here
      out[43] = 0;

      // bits 44 to 47 are reserved and set to 0 here
      out[44] = 0;
      out[45] = 0;
      out[46] = 0;
      out[47] = 0;

      // bits 48 to 63 represent the header check sequence (HCS)
      // calculation of the HCS for bits 0-47 of the header
      // CRC 16-CCITT (X^16 + X^12 + X^5 + 1)
      d_crc_impl.reset();
      d_crc_impl.process_bits((unsigned char) scrambler_seed, 7);
      d_crc_impl.process_bits((unsigned char) mcs, 7);
      d_crc_impl.process_bits((unsigned char) len, 18);
      d_crc_impl.process_bits((unsigned char) 0, 1);
      d_crc_impl.process_bits((unsigned char) type, 1);
      d_crc_impl.process_bits((unsigned char) trn_len, 5);
      d_crc_impl.process_bits((unsigned char) 0, 1);
      d_crc_impl.process_bits((unsigned char) beam_track_req, 1);
      d_crc_impl.process_bits((unsigned char) last_rssi, 4);
      d_crc_impl.process_bits((unsigned char) 0, 5);
      unsigned char crc = d_crc_impl.checksum();
      //std::cout << "[PHY header] HCS: " << static_cast<unsigned>(crc) << std::endl;

      for (int i = 0; i < 16; i++) {
	      out[48 + i] = get_bit(crc, i);
      }

      return true;
    }

    bool phy_header_impl::header_parser(const unsigned char* in, std::vector<tag_t>& tags)
    {
      boost::crc_basic<16> d_crc_impl(0x1021, 0xFFFF, 0, false, false);
      long scrambler_seed = 0;
      long mcs = 0;
      long len = 0;
      long type = 0;
      long trn_len = 0;
      long beam_track_req = 0;
      long last_rssi = 0;
      long hcs = 0;
      tag_t tag;

      int k = 0; // Position in "in"

      // first 7 bits represent the scrambler initialization
      for (int i = 0; i < 7 && k < 64; i++, k++) {
	      scrambler_seed |= (((int) in[k]) & 1) << i;
      }
      tag.key = pmt::mp("scrambler_seed");
      tag.value = pmt::from_long(scrambler_seed);
      tags.push_back(tag);

      // bits 7 to 11 represent the modulation and coding scheme
      for (int i = 0; i < 5 && k < 64; i++, k++) {
	      mcs |= (((int) in[7+i]) & 1) << i;
      }
      if (mcs > 12) {
        std::cout << "[PHY header] Received MCS " << mcs << " not supported" << std::endl;
        return false;
      }
      tag.key = pmt::mp("mcs");
      tag.value = pmt::from_long(mcs);
      tags.push_back(tag);

      // bits 12 to 29 represent the packet length
      for (int i = 0; i < 18 && k < 64; i++, k++) {
	      len |= (((int) in[12+i]) & 1) << i;
      }
      if (len <= 0) {
        std::cout << "[PHY header] Received Packet seems to be too short" << std::endl;
        return false;
      }
      tag.key = pmt::mp("packet_len");
      tag.value = pmt::from_long(len);
      tags.push_back(tag);

      // bit 30 is the "Additional PPDU" field and is ignored here

      // bit 31 is the "Packet Type" field
	  type = ((int) in[31]) & 1;
      tag.key = pmt::mp("packet_type");
      tag.value = pmt::from_long(type);
      tags.push_back(tag);

      // bits 32 to 36 represent the TRN length
      for (int i = 0; i < 5 && k < 64; i++, k++) {
	      trn_len |= (((int) in[32+i]) & 1) << i;
      }
      tag.key = pmt::mp("trn_len");
      tag.value = pmt::from_long(trn_len);
      tags.push_back(tag);

      // bit 37 is the "Aggregation" field and is ignored here

      // bit 38 is the "Beam Tracking Request" field
      beam_track_req = ((int) in[38]) & 1;
      tag.key = pmt::mp("beam_track_req");
      tag.value = pmt::from_long(beam_track_req);
      tags.push_back(tag);

      // bits 39 to 42 represent the "Last RSSI" field and is set to 0 here
      for (int i = 0; i < 4 && k < 64; i++, k++) {
	      last_rssi |= (((int) in[39+i]) & 1) << i;
      }
      tag.key = pmt::mp("last_rssi");
      tag.value = pmt::from_long(last_rssi);
      tags.push_back(tag);

      // bit 43 is the "Turnaround" field and is ignored here

      // bits 44 to 47 are reserved and are ignored here

      // bits 48 to 63 represent the header check sequence (HCS)
      // calculation of the HCS for bits 0-47 of the header
      // CRC 16-CCITT (X^16 + X^12 + X^5 + 1)
      for (int i = 0; i < 16 && k < 64; i++, k++) {
	      hcs |= (((int) in[48+i]) & 1) << i;
      }
      //std::cout << "[PHY header] Received HCS: " << static_cast<unsigned>(hcs) << std::endl;

      // Calculate CRC/HCS
      d_crc_impl.reset();
      d_crc_impl.process_bits((unsigned char) scrambler_seed, 7);
      d_crc_impl.process_bits((unsigned char) mcs, 7);
      d_crc_impl.process_bits((unsigned char) len, 18);
      d_crc_impl.process_bits((unsigned char) 0, 1);
      d_crc_impl.process_bits((unsigned char) type, 1);
      d_crc_impl.process_bits((unsigned char) trn_len, 5);
      d_crc_impl.process_bits((unsigned char) 0, 1);
      d_crc_impl.process_bits((unsigned char) beam_track_req, 1);
      d_crc_impl.process_bits((unsigned char) last_rssi, 4);
      d_crc_impl.process_bits((unsigned char) 0, 5);
      unsigned char crc = d_crc_impl.checksum();
      //std::cout << "[PHY header] Calculated HCS: " << static_cast<unsigned>(crc) << std::endl;

      // Check if received and calculated HCS are identical
      if (hcs != crc) {
        std::cout << "[PHY header] Header Checksum Error" << std::endl;
        return false;
      }
	
      return true;
    }

  } /* namespace iNETS_PHYHeader */
} /* namespace gr */
