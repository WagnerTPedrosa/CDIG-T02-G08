find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_MY_BLOCKS gnuradio-my_blocks)

FIND_PATH(
    GR_MY_BLOCKS_INCLUDE_DIRS
    NAMES gnuradio/my_blocks/api.h
    HINTS $ENV{MY_BLOCKS_DIR}/include
        ${PC_MY_BLOCKS_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_MY_BLOCKS_LIBRARIES
    NAMES gnuradio-my_blocks
    HINTS $ENV{MY_BLOCKS_DIR}/lib
        ${PC_MY_BLOCKS_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-my_blocksTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_MY_BLOCKS DEFAULT_MSG GR_MY_BLOCKS_LIBRARIES GR_MY_BLOCKS_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_MY_BLOCKS_LIBRARIES GR_MY_BLOCKS_INCLUDE_DIRS)
