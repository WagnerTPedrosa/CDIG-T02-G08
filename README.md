
# Digital Communications Project - T02-G08

## Table of Contents

- [Digital Communications Project - T02-G08](#digital-communications-project---t02-g08)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Implemented OFDM Modules](#implemented-ofdm-modules)
  - [Installation and Build](#installation-and-build)
    - [Prerequisites](#prerequisites)
      - [System Requirements](#system-requirements)
      - [Install GNU Radio and Development Tools](#install-gnu-radio-and-development-tools)
      - [Python Dependencies](#python-dependencies)
    - [Compile and Install GNU Radio Module](#compile-and-install-gnu-radio-module)
  - [Usage](#usage)
    - [Modify Python Blocks](#modify-python-blocks)
    - [Add New Blocks](#add-new-blocks)
  - [Documentation](#documentation)
    - [Recompile after changes](#recompile-after-changes)
  - [Contributors](#contributors)

## Description

This project implements an OFDM (Orthogonal Frequency Division Multiplexing) WiFi system using GNU Radio. The system includes custom modules for synchronization, equalization, and decoding of WiFi signals.

## Implemented OFDM Modules

- **ofdm_sync_short**: Synchronization using short preamble
- **ofdm_sync_long**: Synchronization using long preamble  
- **ofdm_equalize_symbols**: OFDM symbol equalization
- **ofdm_decode_signal**: SIGNAL field decoding
- **ofdm_decode_mac**: MAC layer decoding
- **ofdm_parse_mac**: MAC frame parsing

## Installation and Build

### Prerequisites

#### System Requirements
- GNU Radio 3.8+
- CMake 3.8+
- Python 3.6+
- GCC/G++

#### Install GNU Radio and Development Tools

```bash
# Install GNU Radio
sudo apt-get update
sudo apt-get install gnuradio gnuradio-dev

# Install build tools
sudo apt-get install cmake build-essential git

# Install Python development packages
sudo apt-get install python3-dev python3-pip python3-numpy python3-scipy python3-matplotlib

# Install additional libraries
sudo apt-get install libitpp-dev libfftw3-dev 

# Install boost libraries (required for GNU Radio)
sudo apt-get install libboost-all-dev

# Install other dependencies
sudo apt-get install liblog4cpp5-dev libgmp-dev swig
```

#### Python Dependencies

```bash
# Install required Python packages
pip3 install numpy scipy matplotlib
```

### Compile and Install GNU Radio Module

```bash
# From project root directory
cd gr-mywifi
mkdir -p build && cd build
cmake ..
make
sudo make install
sudo ldconfig
```

## Usage

1. **Open GNU Radio Companion:**
   ```bash
   gnuradio-companion
   ```

2. **Load the flowgraph:**
   - Open the `projeto.grc` file in the project root

3. **Run the project:**
   - In GNU Radio Companion, click "Execute" (F6)
   - Or run directly: `python3 projeto.py`


### Modify Python Blocks

The blocks are implemented in `gr-mywifi/python/mywifi/`. After modifications:

```bash
cd gr-mywifi/build
make
sudo make install
```

### Add New Blocks

1. Create the Python file in `gr-mywifi/python/mywifi/`
2. Add GRC definition in `gr-mywifi/grc/`
3. Update `gr-mywifi/python/mywifi/CMakeLists.txt`
4. Recompile following instructions above

## Documentation

Technical documentation is located in the `documentation/` folder:

- **Frame Detection Analysis.md**: Frame detection analysis
- **OFDM Sync Short Block.md**: Short synchronization block documentation
- **OFDM System design parameters.md**: OFDM system design parameters

### Recompile after changes
```bash
cd gr-mywifi/build
make clean
make
sudo make install
sudo ldconfig
```

## Contributors

- Wagner Daniel Teixeira 201908556
- Maria Leonor Pinto Guedes 202107691
