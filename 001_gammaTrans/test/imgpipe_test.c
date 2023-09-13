/*==============================================================================
  Copyright (c) 2012-2013 Qualcomm Technologies, Inc.
  All rights reserved. Qualcomm Proprietary and Confidential.
==============================================================================*/

#include <stdio.h>
#include "verify.h"
#include "imgpipe.h"
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include "../host/imgpipe_utils.h"
#ifndef CALC_EXPORT
#define CALC_EXPORT
#endif /*CALC_EXPORT*/

#if defined(_WIN32) && !defined(_ARM_)
#include "ptl_remote_invoke.h"
CALC_EXPORT int init(pfn_getSymbol GetSymbol)
{
   return remote_invoke_stub_init(GetSymbol);
}
#endif

CALC_EXPORT int main(void)
{
   int nErr  =  0;
   printf("Here is imgpipe_test.c for simulation only\n");
    //now test void do_cdsp_imgpipe_cpy
    //step1 create input image 
    struct timeval ts_start,ts_end;
    const int test_times=1;
    const int inputImgSz = 640*480,outputImgSz = 640*480;
    uint8_t * inputImgBuffer  = (uint8_t*)malloc(inputImgSz);
    uint8_t * outputImgBuffer = (uint8_t*)malloc(outputImgSz);
    memset(inputImgBuffer,0x3c,inputImgSz);
    gettimeofday(&ts_start,NULL);
    for(int j=0;j<test_times;j++)
    {
        do_cdsp_imgpipe_gamma(outputImgBuffer,inputImgBuffer,inputImgSz,2.0);
    }
    gettimeofday(&ts_end,NULL);
    //check results
    int check_ok=0;
    for(int k=0;k<outputImgSz;k++)
    {
        if(outputImgBuffer[k]==inputImgBuffer[k]) 
        {
            check_ok++;
        }
        // printf("out=%d;input=%d\n",outputImgBuffer[k],inputImgBuffer[k]);
    }
    printf("check_ok=%d\n",check_ok);
    if(check_ok==outputImgSz)
    {
        printf("check result successfully !\n");
    }else
    {
        printf("failt to check result !\n");
    }
    printf("do_cdsp_imgpipe_cpy %d bytes runs %ld Us in average %d test times\n",
    inputImgSz,((ts_end.tv_sec-ts_start.tv_sec)*1000000+(ts_end.tv_usec-ts_start.tv_usec))/test_times,test_times);\
    free(inputImgBuffer);
    free(outputImgBuffer);
   return nErr;
}
