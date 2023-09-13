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

int local_imgpipe_cpy(const uint8_t* input, uint8_t* output,int vecLen)
{
  int ii = 0;
  for (ii = 0; ii < vecLen; ++ii) {
    output[ii] = input[ii];
  }
  return 0;
}

int imgpipe_test(int runLocal, int num)
{
  uint8_t* shareMem_in  = 0;
  uint8_t* shareMem_out = 0;
  int len = 0;
  int ii;
  // int64 result = 0;

  rpcmem_init();

  len =  num;
  printf("\n---Allocate %d bytes from ION heap\n", len);

  int heapid = RPCMEM_HEAP_ID_SYSTEM;
  #if defined(SLPI) || defined(MDSP)
  heapid = RPCMEM_HEAP_ID_CONTIG;
  #endif 

  if (0 == (shareMem_in = (uint8_t*)rpcmem_alloc(heapid, RPCMEM_DEFAULT_FLAGS, len))) {
    printf("---Error: alloc failed\n");
	nErr = -1;
    goto bail;
  }
  if (0 == (shareMem_out = (uint8_t*)rpcmem_alloc(heapid, RPCMEM_DEFAULT_FLAGS, len))) {
    printf("---Error: alloc failed\n");
	nErr = -1;
    goto bail;
  }  
  printf("---Creating sequence of numbers from 0 to %d\n", num - 1);
  for (ii = 0; ii < num; ++ii) {
    shareMem_in[ii] = (ii)%255;
    shareMem_out[ii]=0;
  }

  if (runLocal) {
    printf("\n---Compute sum locally\n");
    if (0 != local_imgpipe_cpy(shareMem_in,shareMem_out,num)) {
      printf("Error: local compute failed\n");
	  nErr = -1;
      goto bail;
    }
  } else {
#ifdef __hexagon__
    printf("\n---Compute sum on the DSP\n");
    if (0 != imgpipe_imageCPY(shareMem_in, num,shareMem_out,num)) {
      printf("Error: compute on DSP failed\n");
	  nErr = -1;
      goto bail;
    }
#else 
  void* H = 0;
  int num2 = num;
  int (*func_ptr)(unsigned char* shareMem_in, int num, unsigned char* shareMem_out, int num2);
  int retry_count = 0;

retry:  
   H = dlopen("libimgpipe.so", RTLD_NOW);
   if (!H) {
      printf("---ERROR, Failed to load libimgpipe.so\n");
	  nErr = -1;
	  goto bail;
   }

   func_ptr = (int (*)(unsigned char* , int , unsigned char* , int  ))dlsym(H, "imgpipe_imageCPY");
   if (!func_ptr) {
      printf("---ERROR, imgpipe_imageCPY not found\n");
	  dlclose(H);
	  nErr = -1;
      goto bail;
   }

   printf("\n---Compute sum on the DSP\n");
   if (0 != (nErr = (*func_ptr)(shareMem_in, num,shareMem_out,num2))) {
      printf("---Error: compute on DSP failed, nErr = %d\n", nErr);
	  dlclose(H);
      if (nErr == AEE_ECONNRESET) {
        printf("---SSR happened. Retrying.... nErr = %d\n", nErr);
        sleep(5);
        retry_count++;
        if (retry_count < 10)
            goto retry; 
        else
            printf("---Retry attempt unsuccessful. Timing out....\n---DSP is not up after Sub-system restart...\n");
       }
	   goto bail;
   }  
   dlclose(H);
#endif
}
  //  printf("---Sum = %lld\n", result);
  //check 
  int i = 0;
  int isDiff=0;
  for(i=0;i<num;i++)
  {
    if( shareMem_out[i] != shareMem_in[i] )
    {
      isDiff=1;
      break;
    }
  }
  printf("isResults ok = %d\n",((isDiff==1) ? 0 : 1));
  //dbg
  for(i=0;i<num;i++)
  {
    printf("shareMem_in[%d]=%d; shareMem_out[%d]=%d\n",i,shareMem_in[i],i,shareMem_out[i]);
  }

bail:
  if (shareMem_in)
    rpcmem_free(shareMem_in);
  if (shareMem_out)
    rpcmem_free(shareMem_out);
  rpcmem_deinit();
  return nErr;
}
void do_cdsp_imgpipe_cpy(uint8_t * outArray,const uint8_t * inArray,int size)
{
  int nErr=0;
  //step1 init rpc lib
  rpcmem_init();
  //step2 prepare share memory and copy input array into shareMem_in
  uint8_t* shareMem_in  = 0,*shareMem_out = 0;
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
  memcpy(shareMem_in,inArray,size);
  //step3 dlopen cdsp lib
  void* H = 0;
  int (*func_ptr)(unsigned char* shareMem_in, int sz_in, unsigned char* shareMem_out, int sz_out); 
  H = dlopen("libimgpipe.so", RTLD_NOW);
  if (!H) 
  {
    printf("---ERROR, Failed to load libimgpipe.so\n");nErr=-1;
  } 
  //step4 find function interface ptr
  func_ptr = (int (*)(unsigned char* , int , unsigned char* , int  ))dlsym(H, "imgpipe_imageCPY");
  if (!func_ptr) 
  {
    printf("---ERROR, imgpipe_imageCPY not found\n");nErr=-1;
  }
  //step5 call dsp function and copy shareMem_out to outArray
  if (0 != (nErr = (*func_ptr)(shareMem_in, sz_in,shareMem_out,sz_out))) 
  {
    printf("---Error: compute on DSP failed, nErr = %d\n", nErr);
  }  
  memcpy(outArray,shareMem_out,size);
  //step6 deinit shareMem_in shareMem_out and deinit rpcmem
  if (shareMem_in)  rpcmem_free(shareMem_in);
  if (shareMem_out) rpcmem_free(shareMem_out);
  rpcmem_deinit();
  dlclose(H);
}