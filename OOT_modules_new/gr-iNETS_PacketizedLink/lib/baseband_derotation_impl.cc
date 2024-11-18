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
#include "baseband_derotation_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    baseband_derotation::sptr
    baseband_derotation::make(float mu, gr::digital::constellation_sptr constellation)
    {
      return gnuradio::get_initial_sptr
        (new baseband_derotation_impl(mu, constellation));
    }

    /*
     * The private constructor
     */
    baseband_derotation_impl::baseband_derotation_impl(float mu, gr::digital::constellation_sptr constellation)
      : gr::sync_block("baseband_derotation",
              gr::io_signature::make(1, 1, sizeof(gr_complex)),
              gr::io_signature::make(1, 1, sizeof(gr_complex))),
      f_error(0), f_mu(mu), c_constellation(constellation)
    {}

    /*
     * Our virtual destructor.
     */
    baseband_derotation_impl::~baseband_derotation_impl()
    {
    }

    int
    baseband_derotation_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
        gr_complex *out = (gr_complex *) output_items[0];

      // Do <+signal processing+>
        std::vector<tag_t> phi_tags;
        get_tags_in_window(phi_tags, 0, 0, noutput_items, pmt::intern("phi"));
        float arg = 0.0f;
        float error = 0.0f;
        
        for(int i = 0; i < noutput_items; i++)
        {
            for(int j = 0; j < phi_tags.size(); j++)
            {
                if(phi_tags[j].offset == (nitems_written(0) + i))
                {
                    float phi = pmt::to_float(phi_tags[j].value);
                    f_error = 0;
                }
            }
            
            out[i] = in[i] * std::polar(1.0f, -1.0f * f_error);
            
            arg = std::arg(out[i]);
            error = 0.0f;
            
            switch (c_constellation->points().size())
            {
                case 2 : {
                    if(arg > M_PI / 2.0f || arg < -M_PI / 2.0f)
                    {
                        if(arg < 0)
                        {
                            error = arg + M_PI;
                        }
                        else
                        {
                            error = arg - M_PI;
                        }
                    }
                    else
                    {
                        error = arg;
                    }
                    break;
                }
                case 4 : {
                    if (arg >= 0 && arg < (M_PI / 2.0f))
                    {
                        error = arg - (M_PI / 4.0f);
                    }
                    if (arg >= (M_PI / 2.0f))
                    {
                        error = arg - ((3.0f * M_PI) / 4.0f);
                    }
                    if (arg <= (-M_PI / 2.0f))
                    {
                        error = ((3.0f * M_PI) / 4.0f) + arg;
                    }
                    if (arg < 0 && arg > (-M_PI/2.0f))
                    {
                        error = (M_PI/4.0f) + arg;
                    }
                    break;
                }
                case 16 : {
                    c_constellation->decision_maker_pe(&out[i], &error);
                    error = -1.0 * error;
                    break;
                }
                default: std::cout << "[Baseband Derotation] Modulation not supported";
                    break;
            }
            f_error = wrap_phase(f_error + f_mu * error);
        }
      // Tell runtime system how many output items we produced.
      return noutput_items;
    }
    
    float baseband_derotation_impl::wrap_phase(float phi)
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

  } /* namespace iNETS_PacketizedLink */
} /* namespace gr */
