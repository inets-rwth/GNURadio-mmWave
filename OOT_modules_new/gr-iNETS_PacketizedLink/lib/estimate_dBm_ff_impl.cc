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
#include "estimate_dBm_ff_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    estimate_dBm_ff::sptr
    estimate_dBm_ff::make(float alpha, int sps, int N)
    {
      return gnuradio::get_initial_sptr
        (new estimate_dBm_ff_impl(alpha, sps, N));
    }


    /*
     * The private constructor
     */
    estimate_dBm_ff_impl::estimate_dBm_ff_impl(float alpha, int sps, int N)
      : gr::sync_block("estimate_dBm_ff",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex))),
              d_avg(0.0),
              d_alpha(alpha),
              d_beta(1.0-alpha),
              i_sps(sps),
              i_N(N),
              i_counter(1),
              d_last_sent_rss(0.0)
    {
        d_key = pmt::string_to_symbol("rss");
    }

    /*
     * Our virtual destructor.
     */
    estimate_dBm_ff_impl::~estimate_dBm_ff_impl()
    {
    }

    int
    estimate_dBm_ff_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
      gr_complex *out = (gr_complex *) output_items[0];

      // output is equal to input
      memcpy(output_items[0], input_items[0], noutput_items * sizeof(gr_complex));

      for (int i = 0; i < noutput_items; i++) {
	    // Calculate RMS value of IQ sample
        double mag_sqrd = (in[i] * std::conj(in[i])).real();
	    // Apply single pole IIR LowPass Filter
        d_avg = d_beta * d_avg + d_alpha * mag_sqrd / 100; // 50 Ohm system

	    double rss;

	    if ( d_avg > EPS ) {
        	rss = 10.0*std::log10(d_avg)+30;
	    } else {
		    rss = -174;
	    }

	    pmt::pmt_t pmt_rss = pmt::from_double(rss);

	    // only attach a tag every Nth sample and only if the rss value changed significantly. This is done to reduce the load on the processor (otherwise the model might crash)
	    if ( i_counter >= i_N )  {
            double diff = d_last_sent_rss - rss;
            // if difference is greater than 0.5 dB, update the estimate that is kept in frame_sync_cc block downstream
            if ( std::abs(diff) > 0.5 ) {
                i_counter = 1;
                d_last_sent_rss = rss;
	            for (int s=0; s<i_sps; s++) {
	    	        add_item_tag(0, nitems_written(0) + i + s, d_key, pmt_rss);
	            }
            }
	    } else {
	        i_counter++;
	    }
      }
      // Tell runtime system how many output items we produced.
      return noutput_items;
    }
  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
