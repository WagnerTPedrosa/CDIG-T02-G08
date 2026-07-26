# WiFi OFDM Receiver

A complete IEEE 802.11a WiFi receiver implemented using GNU Radio and the ADALM-PLUTO SDR.

## Table of Contents

- [Digital Communications - T02-G08](#digital-communications---t02-g08)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
- [Key Features](#key-features)
  - [System Architecture](#system-architecture)
  - [Results](#results)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Running the Receiver](#running-the-receiver)
    - [GUI Controls](#gui-controls)
  - [Project Structure](#project-structure)
  - [Contributors](#contributors)

## Overview

This project implements a complete IEEE 802.11a WiFi receiver using GNU Radio and the ADALM-PLUTO SDR.

The receiver performs the entire physical-layer processing chain, from IQ sample acquisition to MAC frame decoding, enabling real-time WiFi packet reception and network analysis.

In addition to decoding WiFi traffic, the system includes:

- Automatic WiFi channel scanning
- Real-time network statistics
- Signal strength visualization
- Wireshark integration for packet inspection
- Interactive GNU Radio GUI controls

# Key Features

- **Full WiFi Receiver Chain**: Implements frame detection, synchronization (short/long), FFT-based OFDM demodulation, channel equalization, and MAC layer decoding
- **PlutoSDR Integration**: Live capture from ADALM-PLUTO
- **Automatic Channel Scanner**: Python snippet that automatically scans 45 WiFi channels to detect active networks
- **Live statistics:** Networks detected per channel and signal strength per channel graphs, channel activity, top channels by network count, and best channels by signal strength
- **Dynamic Controls**: Adjustable detection threshold, channel selection dropdown, and equalization algorithm


## System Architecture

The receiver uses the following signal processing chain:

1. **PlutoSDR Source:** IQ samples at 20 MS/s
2. **Decimating Finite Impulse Response (FIR):** Moving average + Decimation
3. **WiFi Sync Short:** Coarse synchronization using short preamble
4. **WiFi Sync Long:** Fine synchronization and channel estimation using long preamble
5. **Stream to Vector + FFT:** OFDM demodulation (64-point FFT)
6. **WiFi Frame Equalizer:** Channel equalization and SIGNAL field decoding
7. **WiFi Decode MAC:** MAC frame decoding
8. **WiFi Parse MAC:** SSID extraction and output
9. **WiFi Info Printer**: Custom Python block that prints the SSID and channel, and is responsible for the statistics
10. **Wireshark Connector:** Streams decoded packets from GNU Radio to Wireshark for live analysis (Uses a pipe that is created by a Python Snippet block)
11. **File Sink:** Writes the incoming data stream to a file 

<img src="images/gnuradio flow.png">

## Results
After running for some time with automatic sweep we got these results

<img src="images/UI results.png">
<img src="images/wireshark auto sweep.png">

## Installation

```bash
# Install GNU Radio and dependencies
sudo apt update
sudo apt install gnuradio python3-pyqt5

# Install PlutoSDR drivers
sudo apt install gr-iio libiio-utils

# Install gr-foo module
git clone https://github.com/bastibl/gr-foo
cd gr-foo
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig

# Install gr-ieee802-11 module
git clone https://github.com/bastibl/gr-ieee802-11.git
cd gr-ieee802-11
mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig

# Adjust max shared memory
sudo sysctl -w kernel.shmmax=2147483648

# Generate the PHY layer block
cd gr-ieee802-11/examples/
grcc wifi_phy_hier.grc
python3 wifi_phy_hier.py

# Test installation
cd gr-ieee802-11/examples/
grcc wifi_loopback.grc
python3 wifi_loopback.py

# If everything works as intended you should see some decoded packets on the console
```

## Usage

### Running the Receiver

1. **Connect the PlutoSDR** via USB

2. **Open the flowgraph in GNU Radio Companion:**
   ```bash
   gnuradio-companion projeto.grc
   ```
   
   or 

   ```bash
   grcc projeto.grc
   ```

3. **Execute the flowgraph:**
   - Run directly from terminal: `python3 projeto.py`

### GUI Controls

- **Threshold Slider:** Adjusts frame detection sensitivity (0.0 - 1.0, default: 0.8)
- **Channel Selector:** Dropdown menu with 45 WiFi channels
- **Equalization Algorithm:** Choose between different equalizer algorithms
- **Resume Sweep:** Used to resume the automatic sweep if the user manually chooses a specific channel


## Project Structure

```
CDIG-T02-G08/
├── projeto.grc              # GNU Radio Companion flowgraph
├── projeto.py               # Generated Python flowgraph
├── README.md                # This file
├── documentation/           # Technical documentation
│   ├── Frame Detection Analysis.md
│   ├── OFDM System design parameters.md
│   └── Blocks/              # Individual block documentation
```

## Contributors

- **Wagner Daniel Teixeira** - 201908556
- **Maria Leonor Pinto Guedes** - 202107691
