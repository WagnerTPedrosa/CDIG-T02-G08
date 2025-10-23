find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_MYWIFI gnuradio-mywifi)

FIND_PATH(
    GR_MYWIFI_INCLUDE_DIRS
    NAMES gnuradio/mywifi/api.h
    HINTS $ENV{MYWIFI_DIR}/include
        ${PC_MYWIFI_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_MYWIFI_LIBRARIES
    NAMES gnuradio-mywifi
    HINTS $ENV{MYWIFI_DIR}/lib
        ${PC_MYWIFI_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-mywifiTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_MYWIFI DEFAULT_MSG GR_MYWIFI_LIBRARIES GR_MYWIFI_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_MYWIFI_LIBRARIES GR_MYWIFI_INCLUDE_DIRS)
