#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <stdint.h>
#include <sys/time.h>
#include "imgpipe_utils.h"
int main(int argc, char* argv[])
{
    printf("Here is imgpipe_imp.c \n");
    int ret=0;
    ret = imgpipe_test(1, 128);
    printf("run imgpipe_test local ok\n");
    ret = imgpipe_test(0, 128);
    printf("run imgpipe_test cdsp ok\n");
    //now test void do_cdsp_imgpipe_cpy
    //step1 create input image 
    struct timeval ts_start,ts_end;
    const int test_times=1024;
    const int inputImgSz = 640*480,outputImgSz = 640*480;
    uint8_t * inputImgBuffer  = (uint8_t*)malloc(inputImgSz);
    uint8_t * outputImgBuffer = (uint8_t*)malloc(outputImgSz);
    memset(inputImgBuffer,0x3c,inputImgSz);
    gettimeofday(&ts_start,NULL);
    for(int j=0;j<test_times;j++)
    {
        do_cdsp_imgpipe_cpy(outputImgBuffer,inputImgBuffer,inputImgSz);
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
    printf("do_cdsp_imgpipe_cpy %d bytes runs %d Us in average %d test times\n",
    inputImgSz,((ts_end.tv_sec-ts_start.tv_sec)*1000000+(ts_end.tv_usec-ts_start.tv_usec))/test_times,test_times);\
    free(inputImgBuffer);
    free(outputImgBuffer);
}