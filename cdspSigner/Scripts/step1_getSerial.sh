adb root
adb remount
adb push ../androidBin/getserial /data/local/tmp/
adb shell chmod +x /data/local/tmp/getserial
adb shell /data/local/tmp/getserial