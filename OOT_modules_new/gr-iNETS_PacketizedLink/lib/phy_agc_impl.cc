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
#include <volk/volk.h>
#include "phy_agc_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    phy_agc::sptr
    phy_agc::make(float decay_rate, float attack_rate, float reference, float gain, float max_gain)
    {
      return gnuradio::get_initial_sptr
        (new phy_agc_impl(decay_rate, attack_rate, reference, gain, max_gain));
    }

    /*
     * The private constructor
     */
    phy_agc_impl::phy_agc_impl(float decay_rate, float attack_rate, float reference, float gain, float max_gain)
      : gr::sync_block("phy_agc",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make2(2, 2, sizeof(gr_complex), sizeof(float))),
              d_decay_rate(decay_rate), d_attack_rate(attack_rate), d_reference(reference), d_gain(gain), d_max_gain(max_gain)
    {
      const int alignment_multiple = volk_get_alignment() / sizeof(gr_complex);
      set_alignment(std::max(1, alignment_multiple));
      d_key = pmt::string_to_symbol("agc");
      d_me = pmt::string_to_symbol("Gain of AGC");
    }

    /*
     * Our virtual destructor.
     */
    phy_agc_impl::~phy_agc_impl()
    {
    }

    int
    phy_agc_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex*)input_items[0];
      gr_complex *out = (gr_complex*)output_items[0];
      float *gain_out = (float*)output_items[1];

      int64_t nwritten = nitems_written(0);
      int counter = 0;
      int N = 100;

      for(unsigned i = 0; i < noutput_items; i++) {
        out[i] = in[i] * d_gain;

	    // add a tag with the agc gain
        nwritten += i;
        pmt::pmt_t pmt_agc = pmt::from_double(d_gain);
	    
	    /*
	    if (counter == N) {
	      add_item_tag(0, nwritten, d_key, pmt_agc, d_me);
	      counter = 0;
	    } else {
	      counter++;
	    }
	    */

	    // actually, this is power out and not gain out...
        gain_out[i] = (in[i] * std::conj(in[i])).real() * 100000;//d_gain;

	    float tmp = -d_reference + sqrt(out[i].real()*out[i].real() + out[i].imag()*out[i].imag());
	    float rate = d_decay_rate;
	    if((tmp) > d_gain) {
	      rate = d_attack_rate;
	    }
	    d_gain -= tmp*rate;

        if (d_gain < 0.0) {
          d_gain = 10e-5;
        }

        if (d_max_gain > 0.0 && d_gain > d_max_gain) {
          d_gain = d_max_gain;
        }
      }
      //std::cout << d_gain << std::endl;

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
