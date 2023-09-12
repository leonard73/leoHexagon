sudo apt install python2.7
rm -rf output/*.so
python2.7 elfsigner/elfsigner.py -t ${1}
adb wait-for-device root
adb wait-for-device remount
adb wait-for-device shell mkdir -p vendor/lib/rfsa/dsp/testsig
adb wait-for-device push output/*.so vendor/lib/rfsa/dsp/testsig/
adb wait-for-device reboot

################################################################################
## if you run step1_getSerial.sh successfully,
## you will see your device serial number , for example 

## adbd is already running as root
## remount succeeded
## ../androidBin/getserial: 1 file pushed. 1.4 MB/s (7456 bytes in 0.005s)
## Serial Num : 0x6829b494
##

##you need run :
##          sh step2_genSign.sh 0x6829b494
##################################################################################