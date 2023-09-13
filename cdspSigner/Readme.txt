#######################################################################################
Steps to install xvisio cdsp alogorithm libs on cdsp q6 (hexagon v65)  sdm710 sdm845
#######################################################################################
========================================================================
                    (0)  cd Scripts
========================================================================
                    (1)  sh step1_getSerial.sh
========================================================================
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!! PLEASE USE THE LOG FROM STEP1 TO BE THE PARAMETER OF STEP2 !!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!! PLEASE USE THE LOG FROM STEP1 TO BE THE PARAMETER OF STEP2 !!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
LOG LIKE:
## adbd is already running as root
## remount succeeded
## ../androidBin/getserial: 1 file pushed. 1.4 MB/s (7456 bytes in 0.005s)
## Serial Num : 0x6829b494
##

##you need run :
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!! PLEASE USE THE LOG FROM STEP1 TO BE THE PARAMETER OF STEP2 !!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!!!!!! PLEASE USE THE LOG FROM STEP1 TO BE THE PARAMETER OF STEP2 !!!!!!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
========================================================================
                    (2)  sh step2_genSign.sh 0x6829b494
========================================================================
Reading package lists... Done
Building dependency tree       
Reading state information... Done
python2.7 is already the newest version (2.7.17-1~18.04ubuntu1.6).
0 upgraded, 0 newly installed, 0 to remove and 208 not upgraded.
Logging to /home/pan/workspace/gitlab/qualcommap/ReleaseForCustomer/native/Scripts/output/Elfsigner_log.txt

        Attention:
        Use of this tool is conditioned upon your compliance with Qualcomm
        Technologies'(and its affiliates') license terms and conditions;
        including, without limitations, such terms and conditions addressing
        the use of such tools with open source software.

        Agree? [y/n]:
        y
Signing a file may take up to 3 minutes due to network connectivity. Please wait patiently.
------------------------------------------------------------
Signing complete! Output saved at /home/pan/workspace/gitlab/qualcommap/ReleaseForCustomer/native/Scripts/output/testsig-0x6829b494.so

remount succeeded
output/testsig-0x6829b494.so: 1 file pushed. 2.1 MB/s (24784 bytes in 0.011s)

=======================================================================
                (3)  sh step3_setFreq.sh 1200                     
=======================================================================

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
(1200 is the target frequency of MHZ you need to configure of CDSP Q6)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

 ../androidBin/sysMonApp: 1 file pushed. 11.8 MB/s (91636 bytes in 0.007s)
Domain Configured Compute DSP
Calling cdsp set clocks function with following parameters:
Core clock : 1200 MHz
Q6 AXI clock : 100 MHz
Successfully set the required clock configurations, Call the remove API once done...
Example: sysMonApp clocks remove

Running getstate command to query current clocks/votes:

Domain Configured Compute DSP
DSP Core clock :1190.40MHz
SNOC Vote:0.00MHz
MEMNOC Vote:226.00MHz
GuestOS : Total Heap:1536.00KB
Available Heap:743.48KB
Max.Free Bin:707.73KB
Measured SNOC (/clk/snoc) :240.00MHz
Measured BIMC (/clk/bimc) :902.35MHz
Measured CPU L3 clock :1440.01MHz