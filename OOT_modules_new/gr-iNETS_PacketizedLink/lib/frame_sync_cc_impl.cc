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
#include <boost/assign/std/vector.hpp> // for 'operator+=()'
#include <boost/assert.hpp>
#include <gnuradio/tags.h>
#include <pmt/pmt.h>
#include <volk/volk.h>
#include "frame_sync_cc_impl.h"

using namespace std;
using namespace boost::assign; // bring 'operator+=()' into scope

namespace gr {
  namespace iNETS_PacketizedLink {
    
    enum out_port_indexes_t {
      PORT_HEADER = 0,
      PORT_PAYLOAD = 1,
      PORT_INPUTDATA = 0,
      PORT_TRIGGER = 1
    };
    
    frame_sync_cc::sptr
    frame_sync_cc::make(const std::vector<int> &preamble, gr::digital::constellation_sptr preamble_constellation, float detection_threshold, double alpha, const std::string &len_tag_key)
    {
      return gnuradio::get_initial_sptr
        (new frame_sync_cc_impl(preamble, preamble_constellation, detection_threshold, alpha, len_tag_key));
    }

    /*
     * The private constructor
     */
    frame_sync_cc_impl::frame_sync_cc_impl(const std::vector<int> &preamble, gr::digital::constellation_sptr preamble_constellation, float detection_threshold, double alpha, const std::string &len_tag_key)
      : gr::block("frame_sync_cc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make3(3, 3, sizeof(gr_complex), sizeof(gr_complex), sizeof(unsigned char))),
              f_detection_threshold(detection_threshold), s_len_tag_key(len_tag_key), i_state(DETECT), v_preamble(preamble), c_preamble_constellation(preamble_constellation), d_avg_corr(0), d_alpha(alpha)
    {
        i_len_preamble = v_preamble.size(); //length before preamble modulation
        modulate_preamble(); //modulate binary preamble so that we can compare it with received sequence
        i_len_preamble = v_mod_preamble.size(); //preamble length after modulation
        //std::cout << "[Frame Sync]: Using preamble of len " << i_len_preamble << std::endl;
        set_tag_propagation_policy(TPP_DONT); //do not propagate tags.
        set_output_multiple(1024);
        message_port_register_out(pmt::string_to_symbol("phase")); //output tag "phase"
        d_y1 = 0;
        d_y2 = 0;
        d_beta = 1.0-alpha;
        i_tt_az_angle = 0;
        i_tt_el_angle = 0;
        i_rx_beam_id = 0;
        d_cur_rss = 0.0;
        d_prev_sum = 0.0;
    }

    /*
     * Our virtual destructor.
     */
    frame_sync_cc_impl::~frame_sync_cc_impl()
    {
    }
    
    void frame_sync_cc_impl::set_preamble_constellation(gr::digital::constellation_sptr preamble_constellation)
    {
        std::cout << "[Frame Sync]: Setting preamble constellation" << std::endl;
        boost::lock_guard<boost::mutex> guard(m_set_lock);
        c_preamble_constellation = preamble_constellation;
        modulate_preamble();
    }

    void frame_sync_cc_impl::modulate_preamble()
    {
      v_mod_preamble.clear();
      int bits_per_sym = c_preamble_constellation->bits_per_symbol();
      //Use Big Endian (MSB first) to be compatible with constellation modulator block
      for(int i = 0; i < i_len_preamble; i+= bits_per_sym) {
        int val = 0;
        for(int j = 0; j < bits_per_sym; j++)
        {
          val += (v_preamble[i + ((bits_per_sym - 1) - j)] << j);
        }
        v_mod_preamble.push_back(c_preamble_constellation->points()[val]);
      }
    }

    void
    frame_sync_cc_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
        ninput_items_required[0] = noutput_items;
        ninput_items_required[1] = noutput_items;
        return;
    }
    
    std::complex<float>* curr_correlation_buffer; // = (gr_complex*)volk_malloc(sizeof(gr_complex)*256, volk_get_alignment());
    std::complex<float>* corr =  (gr_complex*)volk_malloc(sizeof(gr_complex)*256, volk_get_alignment());
    std::complex<float>* corr_conj =(gr_complex*)volk_malloc(sizeof(gr_complex)*256, volk_get_alignment());
    std::complex<float>* abs_corr = (gr_complex*)volk_malloc(sizeof(gr_complex)*256, volk_get_alignment());
    long rx_time = 0;

    int
    frame_sync_cc_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
        // Mutex
        boost::lock_guard<boost::mutex> guard(m_set_lock);
      
        // Input and Outputs
        const gr_complex *in = (const gr_complex *) input_items[0];
        //const float *gain_in = (const float *) input_items[1];
        gr_complex *out = (gr_complex *) output_items[0];
        gr_complex *corr_out = (gr_complex *) output_items[1];
        unsigned char *trig_out = (unsigned char *) output_items[2];
      
        // Define variables
        int consumed_items = 0;
        int produced_items = 0;
        int i, j;
        int preamble_items_left = 0;
        float preamble_p_sum = 0.0;
        //float gain_sum = 0.0;
        int i_plateau;
        gr_complex sum = 0;

        // look for rx_time tag
        std::vector<tag_t> tags;
        get_tags_in_window(tags, 0, 0, noutput_items, pmt::intern("rx_time"));
        if(tags.size() > 0) {
            rx_time_full_sec = pmt::to_uint64(pmt::tuple_ref(tags[0].value, 0));
            rx_time_frac_sec = pmt::to_double(pmt::tuple_ref(tags[0].value, 1));
	        //std::cout << "[Frame Sync]: Testing. i_len_preamble: " << i_len_preamble << ", input items: " << ninput_items[0] << std::endl;
            std::cout << "[Frame Sync]: Received rx_time tag. Offset:" << tags[0].offset << " Full Sec = " << rx_time_full_sec << " Frac Sec = " << rx_time_frac_sec << std::endl;
            add_item_tag(0, tags[0].offset, pmt::intern("rx_time"), pmt::make_tuple(pmt::from_uint64(rx_time_full_sec), pmt::from_double(rx_time_frac_sec)));
        }

        // look for current position of turntable and current rx beam
        int ttazang = get_tt_az_angle(0, noutput_items);
        if ( ttazang > -500 ) {
            i_tt_az_angle = ttazang; // update turntable azimuth position as soon was we see a tag
            std::cout << "[Frame Sync CC] Update turntable azimuth position." << i_tt_az_angle << std::endl;
        }
        int ttelang = get_tt_el_angle(0, noutput_items);
        if ( ttelang > -500 ) {
            i_tt_el_angle = ttelang; // update turntable elevation position as soon was we see a tag
        }
        int rxbeamid = get_rx_beam_id(0, noutput_items);
        if ( rxbeamid > -500 ) {
            i_rx_beam_id = rxbeamid; // update rx beam id as soon was we see a tag
            std::cout << "[Frame Sync CC] Update rx beam id." << i_rx_beam_id << std::endl;
        }

        double currss = get_rss(0, noutput_items);
        if ( currss > -500 ) {
            d_cur_rss = currss; // update if we get a new power value
            //std::cout << "[Frame Sync CC] Updated RSS estimate." << d_cur_rss << std::endl;
        }
     
        //std::cout << "[Frame Sync] Start correlation computation" << std::endl;
        for (i = 0; i < ninput_items[0] - i_len_preamble; i++) {
            trig_out[i] = 0;

            // Look for preamble in received signal by calculating the correlation with the preamble sequence.
            // Use differentially encoded preamble for increased detection range
            sum = 0;
            volk_32fc_x2_multiply_conjugate_32fc(corr, &in[i], &v_mod_preamble[0], i_len_preamble); //multiply input signal with conjugate version of preamble
            volk_32fc_conjugate_32fc(corr_conj, corr, i_len_preamble); //Calculate "Absolute" Value. 
            volk_32fc_x2_multiply_32fc(abs_corr, &corr[1], corr_conj, i_len_preamble - 1);
            curr_correlation_buffer = corr;

            // Calculate Overall Correlation for complete sequence
            for (j = 0; j < i_len_preamble - 1; j++) {
                sum += abs_corr[j];
            }
            corr_out[i] = std::abs(sum);

            // State Detect: No Preamble detected so far, but continously checking/detecting
            if (i_state == DETECT) {
	            //std::cout << "[PHY Frame Sync] i_state = DETECT" << std::endl;
                //std::cout << "[PHY Frame Sync] DETECT: Consumed Items " << consumed_items << "Produced " << produced_items << std::endl;
                if (std::abs(sum) > f_detection_threshold & std::abs(sum) > 5.0*d_prev_sum) {
	                //std::cout << "[Frame Sync] Preamble detected." << std::endl;
                    i_state = LENGTH_CHECK; //Preamble detected - State changed
                } else {
                    consumed_items++;
                    produced_items++;
                }
            }
            //d_avg_corr = (d_avg_corr + std::abs(sum)) / 2;
            //std::cout << d_avg_corr << std::endl;
        
            // State Pramble: Preamble was detected and checked whether it is long enough
            if (i_state == LENGTH_CHECK) {
	            //std::cout << "[Frame Sync] istate = LENGTH_CHECK" << std::endl;
                if ((ninput_items[0] - i_len_preamble - i) >= (i_len_preamble)) { //Are enough samples available?
                    i_state = PROCESS_PREAMBLE; //next state
                    preamble_items_left = i_len_preamble;
                } else {
		            //std::cout << "Preamble not long enough";
                    break;
                }
            }

            // State Process Pramble: Preamble was detected and is processed
            if (i_state == PROCESS_PREAMBLE) {
                //std::cout << "[PHY Frame Sync] Process Preamble " << std::endl;
                // Calculating Frequency Offset
                if (preamble_items_left == i_len_preamble) {
                    preamble_p_sum = 0.0;
                    //gain_sum = 0.0;
                    //d_y1 = 0;
                    //d_y2 = 0;
                    f_d_f = calculate_fd(curr_correlation_buffer, &in[i], &v_mod_preamble[0], i_len_preamble / 2, i_len_preamble);
                    //_d_phi = _mod_preamble[_len_preamble - 1] / in[i + (_len_preamble - 1)];
                    std::complex<float> curr_d_phi(0,0);
                    for (int j = 0; j < (i_len_preamble / 4); j++) {
                        std::complex<float> curr_pre_item = in[j + i] * std::polar(1.0f, (float)(-2.0 * M_PI * f_d_f * (float)j));
                        curr_d_phi += v_mod_preamble[j] / curr_pre_item;
                    }
                    curr_d_phi = curr_d_phi * (1.0f / std::abs(curr_d_phi));
                    c_d_phi = curr_d_phi;
                }
                preamble_p_sum += (in[i] * std::conj(in[i])).real();
                //gain_sum += gain_in[i];
                consumed_items++;
                produced_items++;
                preamble_items_left--;

                // SNR estimation (2nd and 4th order moment method)
                // This estimator uses knowledge of the kurtosis of the signal (\f$k_a)\f$ and noise (\f$k_w\f$) to make its estimation. We use Beaulieu's approximations here to M-PSK
                // signals and AWGN channels such that \f$k_a=1\f$ and \f$k_w=2\f$. These approximations significantly reduce the complexity of the calculations (and computations) required.
                // Reference: D. R. Pauluzzi and N. C. Beaulieu, "A comparison of SNR estimation techniques for the AWGN channel
	            double y1 = abs(in[i])*abs(in[i]); // Second Moment
	            d_y1 = d_alpha*y1 + d_beta*d_y1; // Filtered Update
	            double y2 = abs(in[i])*abs(in[i])*abs(in[i])*abs(in[i]); // Fourth Moment
	            d_y2 = d_alpha*y2 + d_beta*d_y2; // Filtered Update

                if (preamble_items_left == 0) {
                    //std::cout << "[PHY Frame Sync] No preamble items left." << std::endl;
                    i_state = SET_TRIGGER;
                    long p_rms = std::sqrt(preamble_p_sum / i_len_preamble) * 100; // (gain_sum / i_len_preamble);
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("preamble_rms"), pmt::from_double(p_rms)); //nitems_written(0) + i + 1 is beginning of packet PHY header
                    // Final calculation of SNR
                    double y1_2 = d_y1*d_y1;
                    double signal = sqrt(2*y1_2 - d_y2);
                    double noise = d_y1 - sqrt(2*y1_2 - d_y2);
                    //double rss = get_rss(i, i+i_len_preamble);
                    // we cheat a little and just pass the rss under the preamble_snr tag so we don't have to change every block...
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("preamble_rss"), pmt::from_double(d_cur_rss));
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("preamble_snr"), pmt::from_double(d_cur_rss));
                    //add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("preamble_snr"), pmt::from_double(10.0*log10(signal / noise)));
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("sample_offset"), pmt::from_uint64(nitems_written(0) + i + 1));
	                // rx angle
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("rx_beam_id"), pmt::from_double(i_rx_beam_id));
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("tt_az_angle"), pmt::from_double(i_tt_az_angle));
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("tt_el_angle"), pmt::from_double(i_tt_el_angle));
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("freq_offset"), pmt::from_float(f_d_f));
                    add_item_tag(0, nitems_written(0) + i + 1, pmt::intern("phi_rx"), pmt::from_float(std::arg(c_d_phi)));

                    continue;
                }
            }

            if (i_state == SET_TRIGGER) {
	            //std::cout << "[PHY Frame Sync] Set trigger." << std::endl;
                trig_out[i] = 1;
                add_item_tag(0, nitems_written(0) + i, pmt::intern("fd"), pmt::from_float(f_d_f));
                add_item_tag(0, nitems_written(0) + i, pmt::intern("phi"), pmt::from_float(std::arg(c_d_phi)));
	            // add RSS tag
                i_state = DETECT;
                consumed_items++;
                produced_items++;
                //std::cout << "[PHY Frame Sync] Consumed Items " << consumed_items << "Produced " << produced_items << std::endl;
            }

	        d_prev_sum = std::abs(sum);
        }

        for (i = 0; i < produced_items; i++) {
            out[i] = in[i];
        }

        // Tell runtime system how many input items we consumed on each input stream.
        consume_each(consumed_items);
        produce(0, produced_items);
        produce(1, produced_items);
        produce(2, produced_items);
        // Tell runtime system how many output items we produced.
        return WORK_CALLED_PRODUCE;
    }

    float frame_sync_cc_impl::wrap_phase(float phi)
    {
        while(phi > 2.0f * M_PI) {
            phi -= 2.0f * M_PI;
        }
        while(phi < -2.0f * M_PI) {
            phi += 2.0f * M_PI;
        }
        if(phi > M_PI) {
            phi = -(2.0f * M_PI - phi);
        }
        if(phi <= -M_PI) {
            phi = 2.0f * M_PI + phi;
        }
        return phi;
    }

    /*
     * Data aided frequency offset estimation.
     * See Eq. #8 in "Data-Aided Frequency Estimation for Burst Digital Transmission" by Mengali and Morelli
     */
    float frame_sync_cc_impl::calculate_fd(const gr_complex* z, const gr_complex* x,const gr_complex* c, int N, int L0)
    {
        double w_div =(float)N * (4.0f * (float)N * (float)N - 6.0f * (float)N * (float)L0 + 3.0f * (float)L0 * (float)L0 - 1.0f);
        //z(k) = x(k) * conj(c(k))
        //std::complex<double>* z = new std::complex<double>[L0];
        //for (int i = 0; i < L0; i++) {
        //    z[i] = (1 / std::abs(x[i])) * x[i] * std::conj(c[i]);
        //}

        double sum = 0;
        for (int i = 1; i <= N; i++) {
            double w = (3.0f * ((float)(L0 - i) * (float)(L0 - i + 1) - (float)N * (float)(L0 - N))) / w_div;
            double c1 = std::arg(calculate_R(i, z, L0));
            double c2 = std::arg(calculate_R(i - 1, z, L0));
            double c3 = c1 - c2;
            c3 = wrap_phase(c3);
            sum += w * c3;
        }
        return ((float)sum / (2.0f * M_PI));
    }

    std::complex<double> frame_sync_cc_impl::calculate_R(int m, const gr_complex* z, int L0)
    {
        std::complex<double> sum = 0;
        for (int i = m; i < L0; i++) {
            float x = std::arg(z[i]) - std::arg(z[i - m]);
            std::complex<float> x2 = std::polar(1.0f, x);
            sum += x2;
        }
        return ((1.0/(double)(L0 - m)) * sum);
    }

    double frame_sync_cc_impl::get_rss(int start, int stop) 
    {
      // look for rss tag (that was hopefully inserted before AGC)
      std::vector<tag_t> rss_tags;
      get_tags_in_window(rss_tags, 0, start, stop, pmt::intern("rss"));
      double rss_avg = -500.0;
      if(rss_tags.size() > 0) {
	    rss_avg = pmt::to_double(rss_tags[rss_tags.size()-1].value); // get the last one. we can be quite sure this is part of the packet while the first ones might occur before the preamble
      }
      return rss_avg;
    }

    int frame_sync_cc_impl::get_rx_beam_id(int start, int stop) 
    {
      // look for rss tag (that was hopefully inserted before AGC)
      std::vector<tag_t> tags;
      get_tags_in_window(tags, 0, start, stop, pmt::intern("rx_beam_id"));
      int rx_beam_id = -500;
      if(tags.size() > 0) {
	    rx_beam_id = (int)pmt::to_double(tags[0].value);
        std::cout << "[Frame Sync CC] Found rx_beam_id tag: " << rx_beam_id << std::endl;
      }
      return rx_beam_id;
    }

    int frame_sync_cc_impl::get_tt_az_angle(int start, int stop) 
    {
      // look for rss tag (that was hopefully inserted before AGC)
      std::vector<tag_t> tags;
      get_tags_in_window(tags, 0, start, stop, pmt::intern("tt_az_angle"));
      int tt_az_angle = -500;
      if(tags.size() > 0) {
	    tt_az_angle = (int)pmt::to_double(tags[0].value);
        std::cout << "[Frame Sync CC] Found tt_az_angle tag: " << tt_az_angle << std::endl;
      }
      return tt_az_angle;
    }

    int frame_sync_cc_impl::get_tt_el_angle(int start, int stop) 
    {
      //look for rss tag (that was hopefully inserted before AGC)
      std::vector<tag_t> tags;
      get_tags_in_window(tags, 0, start, stop, pmt::intern("tt_el_angle"));
      int tt_el_angle = -500;
      if(tags.size() > 0) {
	    tt_el_angle = (int)pmt::to_double(tags[0].value);
        std::cout << "[Frame Sync CC] Found tt_el_angle tag: " << tt_el_angle << std::endl;
      }
      return tt_el_angle;
    }
    
    
  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
