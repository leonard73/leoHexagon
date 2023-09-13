adb wait-for-device push ../androidBin/sysMonApp /data/local/tmp/
adb wait-for-device shell chmod +x /data/local/tmp/sysMonApp
adb wait-for-device shell /data/local/tmp/sysMonApp clocks set --coreClock ${1} --busClock 100 --q6 cdsp
###############################
# ex sh step5_setFreq.sh 1200 -> 1.2 Ghz for cdsp
###############################

###############################
# eg:
# root@pan:~/workspace/gitlab/qualcommap/ReleaseForCustomer/native/cdspScripts# sh step5_setFreq.sh 1200
# ../androidBin/sysMonApp: 1 file pushed. 8.1 MB/s (91636 bytes in 0.011s)
# Domain Configured Compute DSP
# Calling cdsp set clocks function with following parameters:
# Core clock : 1200 MHz
# Q6 AXI clock : 100 MHz
# Successfully set the required clock configurations, Call the remove API once done...
# Example: sysMonApp clocks remove

# Running getstate command to query current clocks/votes:

# Domain Configured Compute DSP
# DSP Core clock :1190.40MHz
# SNOC Vote:0.00MHz
# MEMNOC Vote:226.00MHz
# GuestOS : Total Heap:1536.00KB
# Available Heap:743.07KB
# Max.Free Bin:708.14KB
# Measured SNOC (/clk/snoc) :240.00MHz
# Measured BIMC (/clk/bimc) :902.14MHz
# Measured CPU L3 clock :1440.00MHz
###############################