android_cc:=$(HEXAGON_SDK_ROOT)/tools/android-ndk-r19c/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android23-clang 
demoSrc:=$(PWD)/imgpipe_host.c
ccflags:=-static-libstdc++ -fsigned-char -fuse-ld=gold  -w -O3 -llog -landroid -ldl
ccflags+=-I$(PWD) -L$(PWD)/. -limgpipe_utils -limgpipe
android_exe:=cdspDemo
build:
	$(android_cc) $(demoSrc) $(ccflags) -o $(android_exe)
run:
	adb push *_skel.so /vendor/lib/rfsa/dsp/sdk/
	adb push *.so /data/local/tmp/
	adb push $(android_exe) /data/local/tmp/
	adb shell chmod +x data/local/tmp/$(android_exe)
	adb wait-for-device shell export LD_LIBRARY_PATH=/vendor/lib64/:/data/local/tmp ADSP_LIBRARY_PATH="/vendor/lib/rfsa/dsp/sdk\;/vendor/lib/rfsa/dsp/testsig;" /data/local/tmp/$(android_exe)
clean:
	rm -rf $(android_exe)
