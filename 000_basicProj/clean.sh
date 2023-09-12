make tree_clean V=android_Release_aarch64 CDSP_FLAG=1 VERBOSE=1 || exit 1
make tree_clean V=hexagon_Release_dynamic_toolv83_v65 VERBOSE=1 || exit 1
rm -rf ./release
rm -rf ./android_Release_aarch64
rm -rf ./hexagon_Release_dynamic_toolv83_v65