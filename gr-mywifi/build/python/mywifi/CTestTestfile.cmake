# CMake generated Testfile for 
# Source directory: /home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi
# Build directory: /home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/build/python/mywifi
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(qa_ofdm_parse_mac "/usr/bin/sh" "qa_ofdm_parse_mac_test.sh")
set_tests_properties(qa_ofdm_parse_mac PROPERTIES  _BACKTRACE_TRIPLES "/usr/lib/x86_64-linux-gnu/cmake/gnuradio/GrTest.cmake;119;add_test;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;43;GR_ADD_TEST;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;0;")
add_test(qa_ofdm_sync_short "/usr/bin/sh" "qa_ofdm_sync_short_test.sh")
set_tests_properties(qa_ofdm_sync_short PROPERTIES  _BACKTRACE_TRIPLES "/usr/lib/x86_64-linux-gnu/cmake/gnuradio/GrTest.cmake;119;add_test;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;44;GR_ADD_TEST;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;0;")
add_test(qa_ofdm_sync_long "/usr/bin/sh" "qa_ofdm_sync_long_test.sh")
set_tests_properties(qa_ofdm_sync_long PROPERTIES  _BACKTRACE_TRIPLES "/usr/lib/x86_64-linux-gnu/cmake/gnuradio/GrTest.cmake;119;add_test;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;45;GR_ADD_TEST;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;0;")
add_test(qa_ofdm_equalize_symbols "/usr/bin/sh" "qa_ofdm_equalize_symbols_test.sh")
set_tests_properties(qa_ofdm_equalize_symbols PROPERTIES  _BACKTRACE_TRIPLES "/usr/lib/x86_64-linux-gnu/cmake/gnuradio/GrTest.cmake;119;add_test;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;46;GR_ADD_TEST;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;0;")
add_test(qa_ofdm_decode_signal "/usr/bin/sh" "qa_ofdm_decode_signal_test.sh")
set_tests_properties(qa_ofdm_decode_signal PROPERTIES  _BACKTRACE_TRIPLES "/usr/lib/x86_64-linux-gnu/cmake/gnuradio/GrTest.cmake;119;add_test;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;47;GR_ADD_TEST;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;0;")
add_test(qa_ofdm_decode_mac "/usr/bin/sh" "qa_ofdm_decode_mac_test.sh")
set_tests_properties(qa_ofdm_decode_mac PROPERTIES  _BACKTRACE_TRIPLES "/usr/lib/x86_64-linux-gnu/cmake/gnuradio/GrTest.cmake;119;add_test;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;48;GR_ADD_TEST;/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/CMakeLists.txt;0;")
subdirs("bindings")
