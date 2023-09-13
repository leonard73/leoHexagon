adb wait-for-device root
adb wait-for-device remount
adb wait-for-device shell mkdir -p /vendor/bin/
adb wait-for-device push android_Release_aarch64/ship/imgpipe /vendor/bin/
adb wait-for-device shell mkdir -p /vendor/lib/rfsa/dsp/sdk/
adb wait-for-device push android_Release_aarch64/ship/libimgpipe.so /vendor/lib64/
adb wait-for-device push hexagon_Release_dynamic_toolv83_v65/ship/libimgpipe_skel.so /vendor/lib/rfsa/dsp/sdk/
adb wait-for-device push scripts/sysMonApp /data/local/tmp/
adb wait-for-device shell /data/local/tmp/sysMonApp clocks set --coreClock $1 --busClock 100 --q6 cdsp
# adb wait-for-device shell export LD_LIBRARY_PATH="/vendor/lib64/;" /vendor/bin/imgpipe 1 1000
# adb wait-for-device push UNIT_TEST/frame_4440.bin /data/local/tmp/
adb wait-for-device shell export LD_LIBRARY_PATH=/vendor/lib64/:$LD_LIBRARY_PATH ADSP_LIBRARY_PATH="/vendor/lib/rfsa/dsp/sdk\;/vendor/lib/rfsa/dsp/testsig;" /vendor/bin/imgpipe