# Install script for directory: /home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for the subdirectory.
  include("/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/build/python/mywifi/bindings/cmake_install.cmake")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib/python3.12/dist-packages/gnuradio/mywifi" TYPE FILE FILES
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/__init__.py"
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/ofdm_parse_mac.py"
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/ofdm_sync_short.py"
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/ofdm_sync_long.py"
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/ofdm_equalize_symbols.py"
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/ofdm_decode_signal.py"
    "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/python/mywifi/ofdm_decode_mac.py"
    )
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/home/wagner/Desktop/FEUP/5_Ano/CDIG/projeto/gr-mywifi/build/python/mywifi/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
