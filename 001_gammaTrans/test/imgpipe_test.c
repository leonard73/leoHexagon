/*==============================================================================
  Copyright (c) 2012-2013 Qualcomm Technologies, Inc.
  All rights reserved. Qualcomm Proprietary and Confidential.
==============================================================================*/

#include <stdio.h>
#include "verify.h"
#include "imgpipe.h"
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
    int ret=0;
    ret = imgpipe_test(1, 128);
    printf("run imgpipe_test local ok\n");
    ret = imgpipe_test(0, 128);
    printf("run imgpipe_test cdsp ok\n");
//    int nPass =  0;

//    VERIFY(0 == (nErr = vslamProj_test(1, 64)));
//    nPass++;
//    VERIFY(0 == (nErr = vslamProj_test(0, 64)));
//    nPass++;

// bail:
//    printf("############################################################\n");
//    printf("Summary Report \n");
//    printf("############################################################\n");
//    printf("Pass: %d\n", nPass);
//    printf("Undetermined: 0\n");
//    printf("Fail: %d\n", 2 - nPass);
//    printf("Did not run: 0\n");

   return nErr;
}
