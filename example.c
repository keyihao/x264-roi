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

void print_qpmap( int width, int height, float* qpmap)
{
    int width_in_mb = (int)ceil(width / 16.0);
    int height_in_mb = (int)ceil(height / 16.0);

    for(int i = 0; i < height_in_mb; i++)
    {
        for(int j = 0; j < width_in_mb; j++)
        {
            fprintf( stderr, "%.0f", qpmap[i*width_in_mb + j]);
        }
        fprintf( stderr, "\n");
    }
    return;
}

float* get_qpmap( int width, int height, double roi_size, float qpdelta )
{
    int width_in_mb = (int)ceil(width / 16.0);
    int height_in_mb = (int)ceil(height / 16.0);
    int width_height_mb_gcd = gcd(width_in_mb, height_in_mb);
    int min_width = width_in_mb / width_height_mb_gcd;
    int min_height = height_in_mb / width_height_mb_gcd;
    int qpmap_length = width_in_mb * height_in_mb;

    float* qpmap;
    qpmap = (float*)malloc(qpmap_length * sizeof(float));

    if(qpmap == NULL)
    {
        fprintf( stderr, "qpmap malloc failed\n" );
    }

    for(int i = 0; i < height_in_mb; i++)
    {
        for(int j = 0; j < width_in_mb; j++)
        {
            qpmap[i*width_in_mb + j] = qpdelta;
        }
    }

    if((roi_size - 0.0) < 1e-6)
    {
        return qpmap;
    } 

    int roi_in_mb = (int)round(roi_size * qpmap_length);
    double roi_factor = sqrt(roi_in_mb * 1.0 / (min_width * min_height));
    int roi_width_in_mb = (int)floor(roi_factor * min_width);
    int roi_height_in_mb = (int)floor(roi_factor * min_height);
    int roi_mb_remain = roi_in_mb - roi_width_in_mb * roi_height_in_mb;
    int remain_row = (int)ceil(roi_mb_remain * 1.0 / roi_width_in_mb);
    int roi_total_row = roi_height_in_mb + remain_row;
    int column_in_last_row = roi_mb_remain % roi_width_in_mb;
    int start_row_index = height_in_mb / 2 - (roi_total_row / 2 + roi_total_row % 2);
    int start_column_index = width_in_mb / 2 - (roi_width_in_mb / 2 + roi_width_in_mb % 2);

    for(int i = 0; i < roi_total_row; i++)
    {
        for(int j = 0; j < roi_width_in_mb; j++)
        {
            if( (i == roi_total_row - 1) && (j == column_in_last_row) && (column_in_last_row != roi_width_in_mb) && (column_in_last_row != 0))
                break;
            qpmap[(start_row_index + i)*width_in_mb + start_column_index + j] = 0;
        }
    }
    /**
    fprintf( stderr, "min_width: %d\n", min_width);
    fprintf( stderr, "min_height: %d\n", min_height);
    fprintf( stderr, "roi_factor: %f\n", roi_factor);
    fprintf( stderr, "roi_width_in_mb: %d\n", roi_width_in_mb);
    fprintf( stderr, "roi_height_in_mb: %d\n", roi_height_in_mb);
    fprintf( stderr, "roi_mb_remain: %d\n", roi_mb_remain);
    fprintf( stderr, "roi_total_row: %d\n", roi_total_row);
    fprintf( stderr, "column_in_last_row: %d\n", column_in_last_row);
    fprintf( stderr, "start_row_index: %d\n", start_row_index);
    fprintf( stderr, "start_column_index: %d\n", start_column_index);
    **/
    return qpmap;
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

#ifdef _WIN32
    _setmode( _fileno( stdin ),  _O_BINARY );
    _setmode( _fileno( stdout ), _O_BINARY );
    _setmode( _fileno( stderr ), _O_BINARY );
#endif

    FAIL_IF_ERROR( !(argc > 1), "Example usage: example 352x288 <input.yuv >output.h264\n" );
    FAIL_IF_ERROR( 2 != sscanf( argv[1], "%dx%d", &width, &height ), "resolution not specified or incorrect\n" );

    float* qpmap;
    qpmap = get_qpmap(width, height, 0.2, 20);
    //print_qpmap(width, height, qpmap);
    //return 0;

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
    param.b_intra_refresh = 1;
    param.b_vfr_input = 0;
    param.b_repeat_headers = 1;
    param.b_annexb = 1;
    param.analyse.b_ssim = 1;
    param.rc.i_rc_method = X264_RC_CRF;
    param.rc.f_rf_constant = 23;

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
    /* Encode frames */
    for( ;; i_frame++ )
    {
        /* Read input frame */
        if( fread( pic.img.plane[0], 1, luma_size, stdin ) != luma_size )
            break;
        if( fread( pic.img.plane[1], 1, chroma_size, stdin ) != chroma_size )
            break;
        if( fread( pic.img.plane[2], 1, chroma_size, stdin ) != chroma_size )
            break;

        pic.i_pts = i_frame;
        if(i_frame == 450)
        {
            free(qpmap);
            qpmap = get_qpmap(width, height, 0.75, 5);
        }
        pic.prop.quant_offsets = qpmap;
        i_frame_size = x264_encoder_encode( h, &nal, &i_nal, &pic, &pic_out );
        fprintf(stderr, "Frame Index: %d, Size: %d, SSIM: %f\n", i_frame, i_frame_size, pic_out.prop.f_ssim);
        if( i_frame_size < 0 )
            goto fail;
        else if( i_frame_size )
        {
            if( !fwrite( nal->p_payload, i_frame_size, 1, stdout ) )
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
            if( !fwrite( nal->p_payload, i_frame_size, 1, stdout ) )
                goto fail;
        }
    }

    x264_encoder_close( h );
    x264_picture_clean( &pic );
    free(qpmap);
    return 0;

#undef fail
fail3:
    x264_encoder_close( h );
fail2:
    x264_picture_clean( &pic );
fail:
    return -1;
}
