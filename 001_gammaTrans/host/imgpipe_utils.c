/*==============================================================================
  Copyright (c) 2012-2014,2017 Qualcomm Technologies, Inc.
  All rights reserved. Qualcomm Proprietary and Confidential.
==============================================================================*/

#include "AEEStdErr.h"
#include "imgpipe.h"
#include "imgpipe_utils.h"
#include "rpcmem.h"
#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <dlfcn.h>
#include <unistd.h>
#include <string.h>

int nErr = 0; 
void do_cdsp_imgpipe_gamma(uint8_t * outArray,const uint8_t * inArray,int size,float gammaRatio)
{
  int nErr=0;
  //step1 init rpc lib
  rpcmem_init();
  //step2 prepare share memory and copy input array into shareMem_in
  uint8_t* shareMem_in  = 0,*shareMem_out = 0;
  float * shareMem_gammaRatio=0;
  int sz_in = size,sz_out = size;
  int heapid = RPCMEM_HEAP_ID_SYSTEM;
  #if defined(SLPI) || defined(MDSP)
  heapid = RPCMEM_HEAP_ID_CONTIG;
  #endif 
  if (0 == (shareMem_in = (uint8_t*)rpcmem_alloc(heapid, RPCMEM_DEFAULT_FLAGS, size))) 
  {
    printf("---Error: alloc shareMem_in failed\n");nErr=-1;
  }
  if (0 == (shareMem_out = (uint8_t*)rpcmem_alloc(heapid, RPCMEM_DEFAULT_FLAGS, size))) 
  {
    printf("---Error: alloc shareMem_out failed\n");nErr=-1;
  } 
  if (0 == (shareMem_gammaRatio = (float*)rpcmem_alloc(heapid, RPCMEM_DEFAULT_FLAGS, sizeof(float)))) 
  {
    printf("---Error: alloc shareMem_gammaRatio failed\n");nErr=-1;
  }   
  memcpy(shareMem_in,inArray,size);
  *shareMem_gammaRatio=gammaRatio;
  float rpc_gammaRatio=*shareMem_gammaRatio;
  //step3 dlopen cdsp lib
#ifdef __hexagon__
  nErr = imgpipe_gammaTrans(shareMem_in, sz_in,shareMem_out,sz_out,rpc_gammaRatio);
#else
  void* H = 0;
  int (*func_ptr)(unsigned char* shareMem_in, int sz_in, unsigned char* shareMem_out, int sz_out,float rpc_gammaRatio); 
  H = dlopen("libimgpipe.so", RTLD_NOW);
  if (!H) 
  {
    printf("---ERROR, Failed to load libimgpipe.so\n");nErr=-1;
  } 
  //step4 find function interface ptr
  func_ptr = (int (*)(unsigned char* , int , unsigned char* , int ,float ))dlsym(H, "imgpipe_gammaTrans");
  if (!func_ptr) 
  {
    printf("---ERROR, imgpipe_gammaTrans not found\n");nErr=-1;
  }
  //step5 call dsp function and copy shareMem_out to outArray
  if (0 != (nErr = (*func_ptr)(shareMem_in, sz_in,shareMem_out,sz_out,rpc_gammaRatio))) 
  {
    printf("---Error: compute on DSP failed, nErr = %d\n", nErr);
  }  
  dlclose(H);
#endif
  memcpy(outArray,shareMem_out,size);
  //step6 deinit shareMem_in shareMem_out and deinit rpcmem
  if (shareMem_in)          rpcmem_free(shareMem_in);
  if (shareMem_out)         rpcmem_free(shareMem_out);
  if (shareMem_gammaRatio)  rpcmem_free(shareMem_gammaRatio);
  rpcmem_deinit();
  
}