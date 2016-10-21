/*****************************************************************************
 * example.c: libx264 API usage example
 *****************************************************************************
 * Copyright (C) 2014-2016 x264 project
 *
 * Authors: Anton Mitrofanov <BugMaster@narod.ru>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02111, USA.
 *
 * This program is also available under a commercial proprietary license.
 * For more information, contact us at licensing@x264.com.
 *****************************************************************************/

#ifdef _WIN32
#include <io.h>       /* _setmode() */
#include <fcntl.h>    /* _O_BINARY */
#endif

#include <stdint.h>
#include <stdio.h>
#include <x264.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

double b_target = 0;
double crf = 0;
double time_slot_length = 0.1;
const int fps = 30;
FILE* input_file;
FILE* output_file;
FILE* log_file;

#define FAIL_IF_ERROR( cond, ... )\
do\
{\
    if( cond )\
    {\
        fprintf( stderr, __VA_ARGS__ );\
        goto fail;\
    }\
} while( 0 )

int gcd ( int a, int b )
{
  int c;
  while ( a != 0 ) {
     c = a; a = b%a;  b = c;
  }
  return b;
}

int main( int argc, char **argv )
{
    int width, height;
    x264_param_t param;
    x264_picture_t pic;
    x264_picture_t pic_out;
    x264_t *h;
    int i_frame = 0;
    int i_frame_size;
    x264_nal_t *nal;
    int i_nal;

/**
#ifdef _WIN32
    _setmode( _fileno( stdin ),  _O_BINARY );
    _setmode( _fileno( stdout ), _O_BINARY );
    _setmode( _fileno( stderr ), _O_BINARY );
#endif
**/

    FAIL_IF_ERROR( !(argc > 1), "Example usage: vbr 352x288 <input.yuv >output.h264\n" );
    FAIL_IF_ERROR( 2 != sscanf( argv[1], "%dx%d", &width, &height ), "resolution not specified or incorrect\n" );
    FAIL_IF_ERROR( 1 != sscanf( argv[2], "%lf", &time_slot_length ), "time_slot_length incorrect\n" );
    FAIL_IF_ERROR( 1 != sscanf( argv[3], "%lf", &crf ), "crf incorrect\n" );
    FAIL_IF_ERROR( NULL == (input_file = fopen(argv[4], "rb")), "input file incorrect\n" );
    FAIL_IF_ERROR( NULL == (output_file = fopen(argv[5], "wb+")), "output file incorrect\n" );
    FAIL_IF_ERROR( NULL == (log_file = fopen(argv[6], "w+")), "log file incorrect\n" );

    const double frames_interval = time_slot_length * fps;

    /* Get default params for preset/tuning */
    if( x264_param_default_preset( &param, "medium", NULL ) < 0 )
        goto fail;

    /* Configure non-default params */
    param.i_csp = X264_CSP_I420;
    param.i_width  = width;
    param.i_height = height;
    param.i_bframe = 0;
    param.i_frame_reference = 1;
    param.i_keyint_max = 48;
    param.i_sync_lookahead = 0;
    param.b_intra_refresh = 1;
    param.b_vfr_input = 0;
    param.b_repeat_headers = 1;
    param.b_annexb = 1;
    param.analyse.b_ssim = 1;
    param.analyse.b_psy = 0;
    param.rc.i_rc_method = X264_RC_CRF;
    param.rc.f_rf_constant = crf;
    param.rc.i_lookahead = 0;

    /* Apply profile restrictions. */
    /*if( x264_param_apply_profile( &param, "high" ) < 0 )
        goto fail;*/

    if( x264_picture_alloc( &pic, param.i_csp, param.i_width, param.i_height ) < 0 )
        goto fail;
#undef fail
#define fail fail2

    h = x264_encoder_open( &param );
    if( !h )
        goto fail;
#undef fail
#define fail fail3

    int luma_size = width * height;
    int chroma_size = luma_size / 4;
    int frame_count = 0;
    int total_bytes = 0;
    double total_dssim = 0;
    /* Encode frames */
    for( ;; i_frame++ )
    {
        /* Read input frame */
        if( fread( pic.img.plane[0], 1, luma_size, input_file ) != luma_size )
            break;
        if( fread( pic.img.plane[1], 1, chroma_size, input_file ) != chroma_size )
            break;
        if( fread( pic.img.plane[2], 1, chroma_size, input_file ) != chroma_size )
            break;

        pic.i_pts = i_frame;
        
        if(frame_count == frames_interval)
        {
            double bit_rate = ((total_bytes * 8.0 / (1024* 1024)) / (frames_interval * 1.0 / fps)) ;
            double average_dssim = total_dssim / frames_interval;
            fprintf(stderr, "Average bitrate: %f, average dssim: %f\n", bit_rate, average_dssim);
            fprintf(log_file, "Average bitrate: %f, average dssim: %f\n", bit_rate, average_dssim);
            
            frame_count = 0;
            total_bytes = 0;
            total_dssim = 0;
        }

        i_frame_size = x264_encoder_encode( h, &nal, &i_nal, &pic, &pic_out );
        if( i_frame_size < 0 )
            goto fail;
        else if( i_frame_size )
        {
            fprintf(stderr, "Frame Index: %d, Size: %d, SSIM: %f\n", i_frame, i_frame_size, pic_out.prop.f_ssim);
            fprintf(log_file, "Frame Index: %d, Size: %d, SSIM: %f\n", i_frame, i_frame_size, pic_out.prop.f_ssim);
            frame_count++;
            total_bytes += i_frame_size;
            total_dssim += ((1 - pic_out.prop.f_ssim) / 2);
            if( !fwrite( nal->p_payload, i_frame_size, 1, output_file ) )
                goto fail;
        }
    }
    /* Flush delayed frames */
    while( x264_encoder_delayed_frames( h ) )
    {
        i_frame_size = x264_encoder_encode( h, &nal, &i_nal, NULL, &pic_out );
        if( i_frame_size < 0 )
            goto fail;
        else if( i_frame_size )
        {
            if( !fwrite( nal->p_payload, i_frame_size, 1, output_file ) )
                goto fail;
        }
    }

    x264_encoder_close( h );
    x264_picture_clean( &pic );
    fclose(input_file);
    fclose(output_file);
    fclose(log_file);
    return 0;

#undef fail
fail3:
    x264_encoder_close( h );
fail2:
    x264_picture_clean( &pic );
fail:
    fclose(input_file);
    fclose(output_file);
    fclose(log_file);
    return -1;
}
