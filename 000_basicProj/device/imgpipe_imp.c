#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "imgpipe.h"
#ifdef USE_SIMD_OPT
#include "hexagon_types.h"
#include "hexagon_protos.h"
#include "hvx_hexagon_protos.h"
#include "HAP_compute_res.h"
typedef long HEXAGON_Vect1024_UN __attribute__((__vector_size__(128)))__attribute__((aligned(64)));
#define vmemu(A) *((HEXAGON_Vect1024_UN*)(A))
#define V_LENGTH 128 
#endif
uint64 imgpipe_imageCPY(unsigned char* inputArray, int inputArrayLen, unsigned char* outputArray, int outputArrayLen)
{
    uint64 ret=0;
    uint32 i=0;
    #ifndef USE_SIMD_OPT
    for(i=0;i<outputArrayLen;i++)
    {
        outputArray[i] = inputArray[i];
    }
    #else
    for(i=0;i<outputArrayLen;i+=V_LENGTH)
    {
        HVX_Vector v_load_u8x64,v_store_u8x64;
        v_load_u8x64             = vmemu(inputArray);
        v_store_u8x64            = v_load_u8x64;
        vmemu(outputArray)        = v_store_u8x64;
        inputArray               += V_LENGTH;
        outputArray              += V_LENGTH;
    }
    #endif
    return ret;
}