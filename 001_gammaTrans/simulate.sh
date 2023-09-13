HEXAGON_SDK_TOOLS=${HEXAGON_SDK_ROOT}/tools/HEXAGON_Tools/8.3.07/Tools/bin
RUN_HEXAGON_SIM=${HEXAGON_SDK_TOOLS}/hexagon-sim
${RUN_HEXAGON_SIM} --mv65 --simulated_returnval --dsp_clock 800  --usefs hexagon_Release_dynamic_toolv83_v65 hexagon_Release_dynamic_toolv83_v65/imgpipe_q -- 
