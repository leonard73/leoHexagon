#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "imgpipe.h"

uint64 imgpipe_imageCPY(unsigned char* inputArray, int inputArrayLen, unsigned char* outputArray, int outputArrayLen)
{
    uint64 ret=0;
    uint32 i=0;
    for(i=0;i<outputArrayLen;i++)
    {
        outputArray[i] = inputArray[i];
    }
    return ret;
}