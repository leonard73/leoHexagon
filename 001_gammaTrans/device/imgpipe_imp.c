#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "imgpipe.h"
#ifdef USE_SIMD_OPT
#include "hexagon_types.h"
#include "hexagon_protos.h"
#include "hvx_hexagon_protos.h"
#include "HAP_compute_res.h"
#include "HAP_vtcm_mgr.h"
#include "HAP_farf.h"
#include "q6cache.h"
typedef long HEXAGON_Vect1024_UN __attribute__((__vector_size__(128)))__attribute__((aligned(64)));
#define vmemu(A) *((HEXAGON_Vect1024_UN*)(A))
#define V_LENGTH 128 
#endif
#if __HEXAGON_ARCH__ == 68
#define VTCM_ADDRESS 0xD8400000LL
#else
#define VTCM_ADDRESS 0xD8200000LL
#endif

uint64 imgpipe_gammaTrans(unsigned char* inputArray, int inputArrayLen, unsigned char* outputArray, int outputArrayLen, float gammaRatio)
{
    uint64 ret=0;
    uint32 i=0;
    #ifndef USE_SIMD_OPT
    //step1 build gamma lookup table
    uint8_t * gammaLutTable = (uint8_t *)memalign(128,256);
    for( i = 0; i < 256; i++)
    {
        gammaLutTable[i] =(uint8_t) round(pow(i/255.f, gammaRatio)*255.f);
    }
    //step2 do LUT TRANS
    for(i=0;i<outputArrayLen;i++)
    {
        outputArray[i] = gammaLutTable[inputArray[i]];
    }    
    free(gammaLutTable);
    #else
    //step1 build vector gamma lookup table 
    #ifndef __hexagon__  
    HVX_Vector * vtcmLine;  
    // vtcmLine = (HVX_Vector * )HAP_request_async_VTCM(256 * 1024, 1, 5000);
    vtcmLine = (HVX_Vector*)HAP_request_VTCM(256 * 1024, 0);
    HVX_Vector * v_table_0to127_p = vtcmLine, * v_table_128to255_P = vtcmLine+1;
    #else
    HVX_Vector v_table_0to127;
    HVX_Vector v_table_128to255;
    HVX_Vector * v_table_0to127_p = &v_table_0to127, * v_table_128to255_P = &v_table_128to255;
    #endif
    uint8_t * gammaLutTable = (uint8_t *)memalign(128,256);
    for( i = 0; i < 256; i++)
    {
        gammaLutTable[i] =(uint8_t) round(pow(i/255.f, gammaRatio)*255.f);
    }
    * v_table_0to127_p    = Q6_Vb_vshuff_Vb(vmemu(gammaLutTable));
    * v_table_128to255_P  = Q6_Vb_vshuff_Vb(vmemu(gammaLutTable+128));
    free(gammaLutTable);
    //step2 do vector LUT TRANS
    #ifndef __hexagon__  
    HVX_Vector *v_index=vtcmLine+2,*v_out1=vtcmLine+3,*v_out2=vtcmLine+4,*v_out3=vtcmLine+5,*v_out4=vtcmLine+6,*result_low=vtcmLine+7,*result_high=vtcmLine+8;
    #else
    HVX_Vector vectors[7];
    HVX_Vector *v_index=vectors+2,*v_out1=vectors+3,*v_out2=vectors+4,*v_out3=vectors+5,*v_out4=vectors+6,*result_low=vectors+7,*result_high=vectors+8;
    #endif
    for( i=0;i<outputArrayLen;i+=V_LENGTH)
    {
        *v_index = vmemu(inputArray);
        *v_out1=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_0to127_p,0);
        *v_out2=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_0to127_p,1);
        *v_out3=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_0to127_p,2);
        *v_out4=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_0to127_p,3);
        *result_low =Q6_V_vor_VV( Q6_V_vor_VV(*v_out1,*v_out2),Q6_V_vor_VV(*v_out3,*v_out4));
        *v_out1=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_128to255_P,4);
        *v_out2=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_128to255_P,5);
        *v_out3=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_128to255_P,6);
        *v_out4=Q6_Vb_vlut32_VbVbR(*v_index,* v_table_128to255_P,7);
        *result_high=Q6_V_vor_VV( Q6_V_vor_VV(*v_out1,*v_out2),Q6_V_vor_VV(*v_out3,*v_out4));
        vmemu(outputArray) = Q6_V_vor_VV(*result_low,*result_high);
        inputArray += V_LENGTH;
        outputArray+= V_LENGTH;
    }
    #ifndef __hexagon__  
    HAP_release_VTCM(vtcmLine);
    #endif 
    #endif
    return ret;
}