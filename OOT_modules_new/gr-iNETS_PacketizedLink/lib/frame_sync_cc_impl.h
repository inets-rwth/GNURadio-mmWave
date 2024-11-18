/* -*- c++ -*- */
/*
 * Copyright 2023 iNETS - RWTH Aachen.
 *
 * SPDX-License-Identifier: GPL-3.0-or-later
 */

#ifndef INCLUDED_INETS_PACKETIZEDLINK_FRAME_SYNC_CC_IMPL_H
#define INCLUDED_INETS_PACKETIZEDLINK_FRAME_SYNC_CC_IMPL_H

#include <gnuradio/iNETS_PacketizedLink/frame_sync_cc.h>
#include <boost/thread.hpp>
#include <vector>

namespace gr {
  namespace iNETS_PacketizedLink {

    class frame_sync_cc_impl : public frame_sync_cc
    {
     private:
      const std::vector<int> v_preamble;
      std::vector<gr_complex> v_mod_preamble; //modulated preamble
      gr::digital::constellation_sptr c_preamble_constellation; //preamble modulation constellation
      int i_len_preamble; //preamble length
      float f_detection_threshold; //preamble detection threshold (correlation)
      float d_avg_corr; //previous correlation value
      std::string s_len_tag_key; // length tag
      int i_state; //detection state
      float f_last_corr; //last correlation value
      float f_d_f;
      std::complex<float> c_d_phi;
      boost::mutex m_set_lock; //mutex

      static const int DETECT = 0;
      static const int LENGTH_CHECK = 1;
      static const int PROCESS_PREAMBLE = 2;
      static const int SET_TRIGGER = 3;

      void modulate_preamble();
      float calculate_fd(const gr_complex* z, const gr_complex* x, const gr_complex* c, int N, int L0);
      std::complex<double> calculate_R(int m, const gr_complex* z, int L0);
      float wrap_phase(float phi);
      double get_rss(int start, int stop);
      int get_rx_beam_id(int start, int stop);
      int get_tt_az_angle(int start, int stop);
      int get_tt_el_angle(int start, int stop);

      uint64_t rx_time_full_sec;
      double rx_time_frac_sec;

      //SNR
      double d_y1;
      double d_y2;
      double d_alpha;
      double d_beta;

      double d_prev_sum;

      int i_tt_az_angle;
      int i_tt_el_angle;
      int i_rx_beam_id;

      double d_cur_rss;

     public:
      frame_sync_cc_impl(const std::vector<int> &preamble, gr::digital::constellation_sptr preamble_constellation, float detection_threshold, double alpha, const std::string &len_tag_key);
      ~frame_sync_cc_impl();

      void set_preamble_constellation(gr::digital::constellation_sptr preamble_constellation); 
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);
      
      int general_work(int noutput_items,
           gr_vector_int &ninput_items,
           gr_vector_const_void_star &input_items,
           gr_vector_void_star &output_items);

    };

  } // namespace iNETS_PacketizedLink
} // namespace gr

#endif /* INCLUDED_INETS_PACKETIZEDLINK_FRAME_SYNC_CC_IMPL_H */
