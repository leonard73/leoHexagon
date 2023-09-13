make tree_clean V=android_Release_aarch64 CDSP_FLAG=1 VERBOSE=1 || exit 1
make tree V=android_Release_aarch64 CDSP_FLAG=1 VERBOSE=1 || exit 1
make tree_clean V=hexagon_Release_dynamic_toolv83_v65 VERBOSE=1 || exit 1
make tree V=hexagon_Release_dynamic_toolv83_v65 VERBOSE=1 || exit 1
rm -rf ./release
mkdir -p ./release
cp -f android_Release_aarch64/ship/*.so ./release/
cp -f hexagon_Release_dynamic_toolv83_v65/ship/*.so ./release/
cp -f hexagon_Release_dynamic_toolv83_v65/ship/*.so ./release/
cp -f host/*.h ./release/
cp -f host/imgpipe_host.c ./release/
cp -f scripts/* ./release/