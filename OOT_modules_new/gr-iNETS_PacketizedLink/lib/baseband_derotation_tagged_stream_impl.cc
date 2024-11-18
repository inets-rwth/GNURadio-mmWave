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
#include <gnuradio/digital/constellation.h>
#include "baseband_derotation_tagged_stream_impl.h"

namespace gr {
  namespace iNETS_PacketizedLink {

    baseband_derotation_tagged_stream::sptr
    baseband_derotation_tagged_stream::make(float mu)
    {
      return gnuradio::get_initial_sptr
        (new baseband_derotation_tagged_stream_impl(mu));
    }

    /*
     * The private constructor
     */
    baseband_derotation_tagged_stream_impl::baseband_derotation_tagged_stream_impl(float mu)
      : gr::sync_block("baseband_derotation_tagged_stream",
                       gr::io_signature::make(1, 1, sizeof(gr_complex)),
                       gr::io_signature::make(1, 1, sizeof(gr_complex))),
      f_error(0), f_mu(mu), i_mcs(0)
    {}
    
    /*
     * Our virtual destructor.
     */
    baseband_derotation_tagged_stream_impl::~baseband_derotation_tagged_stream_impl()
    {
    }

    int
    baseband_derotation_tagged_stream_impl::work(int noutput_items,
        gr_vector_const_void_star &input_items,
        gr_vector_void_star &output_items)
    {
      const gr_complex *in = (const gr_complex *) input_items[0];
        gr_complex *out = (gr_complex *) output_items[0];

      // Do <+signal processing+>
        std::vector<tag_t> phi_tags;
        get_tags_in_window(phi_tags, 0, 0, noutput_items, pmt::intern("phi"));
        std::vector<tag_t> mcs_tags;
        get_tags_in_window(mcs_tags, 0, 0, noutput_items, pmt::intern("mcs"));
        float arg = 0.0f;
        float error = 0.0f;
        gr::digital::constellation_sptr qam16const_sptr = gr::digital::constellation_16qam::make();
        
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
            for(int j = 0; j < mcs_tags.size(); j++)
            {
                if(mcs_tags[j].offset == (nitems_written(0) + i))
                {
                    i_mcs = pmt::to_long(mcs_tags[j].value);
                    //std::cout << "[Baseband Derotation Tagged Stream] Received MCS tag " << i_mcs << std::endl;
                }
            }
            
            out[i] = in[i] * std::polar(1.0f, -1.0f * f_error);
            
            arg = std::arg(out[i]);
            error = 0.0f;
            
            //MCS   -   Modulation/Constellation Mapping for SC-PHY
            //00        DPBSK -> handeled here as BPSK
            //01-05     BPSK
            //06-09     QPSK
            //10-12     16QAM
            
            int constellation_points = 0;
            if (i_mcs <= 5)
            {
                constellation_points = 2;
            }
            else if (i_mcs > 5 && i_mcs <= 9)
            {
                constellation_points = 4;
            }
            else if (i_mcs > 10 && i_mcs <= 12)
            {
                constellation_points = 16;
            }
            else
            {
                std::cout << "[Baseband Derotation Tagged Stream] Invalid MCS tag received" << std::endl;
            }
            
            switch (constellation_points)
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
                    qam16const_sptr->decision_maker_pe(&out[i], &error);
                    error = -1.0 * error;
                    break;
                }
                default: std::cout << "[Baseband Derotation Tagged Stream] Modulation not supported" << std::endl;
                    break;
            }
            f_error = wrap_phase(f_error + f_mu * error);
        }

      // Tell runtime system how many output items we produced.
      return noutput_items;
    }
    
    float baseband_derotation_tagged_stream_impl::wrap_phase(float phi)
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
