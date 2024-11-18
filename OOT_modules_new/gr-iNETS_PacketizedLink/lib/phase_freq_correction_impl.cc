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
#include "phase_freq_correction_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    phase_freq_correction::sptr
    phase_freq_correction::make(int num_preamble_samples)
    {
      return gnuradio::get_initial_sptr
        (new phase_freq_correction_impl(num_preamble_samples));
    }

    /*
     * The private constructor
     */
    phase_freq_correction_impl::phase_freq_correction_impl(int num_preamble_samples)
      : gr::sync_block("phase_freq_correction",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex))),
              i_num_preamble_samples(num_preamble_samples)
    {}

    /*
     * Our virtual destructor.
     */
    phase_freq_correction_impl::~phase_freq_correction_impl()
    {
    }

    int
    phase_freq_correction_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
        const gr_complex *in = (const gr_complex *) input_items[0];
        gr_complex *out = (gr_complex *) output_items[0];

        // Do <+signal processing+>
        std::vector<tag_t> fd_tags;
        std::vector<tag_t> phi_tags;
        get_tags_in_window(fd_tags, 0, 0, noutput_items, pmt::intern("fd"));
        get_tags_in_window(phi_tags, 0, 0, noutput_items, pmt::intern("phi"));
	    //std::cout << "[Phase Freq Correction] Frequency correction is " << pmt::to_float(fd_tags[0].value) << std::endl;
        float f_d = 0;
        float phi = 0;
        for (int i = 0; i < noutput_items; i++) {
          for (int j = 0; j < fd_tags.size(); j++) {
            if (fd_tags[j].offset == (nitems_written(0) + i)) { // tags and samples have to be synced (fd tag should be at the beginning of the tagged stream)
              f_d = pmt::to_float(fd_tags[j].value); // read values for freq offset
              phi = pmt::to_float(phi_tags[j].value); // and phase offset
              r_rot.set_phase_incr(exp(gr_complex(0, f_d * -2.0f * M_PI))); // phase increment per sample
              r_rot.set_phase(exp(gr_complex(0, phi + f_d * -2.0f * M_PI * i_num_preamble_samples))); // initial phase (number of preamble samples has to be taken into account)
            }
          }
          out[i] =  r_rot.rotate(in[i]);
	      //std::cout << "[Phase Freq Corr] Output value " << out[i] << std::endl;
        }
      // Tell runtime system how many output items we produced.
      return noutput_items;
    }

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
