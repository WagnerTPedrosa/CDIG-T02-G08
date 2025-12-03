CDIG

## Description

This project implements a complete **IEEE 802.11a WiFi receiver** using GNU Radio and the ADALM-PLUTO SDR (PlutoSDR). The system is capable of capturing, demodulating, and decoding WiFi frames on the 5 GHz band with automatic channel scanning functionality.

### Key Features

- **Full WiFi Receiver Chain**: Implements frame detection, synchronization (short/long), FFT-based OFDM demodulation, channel equalization, and MAC layer decoding
- **PlutoSDR Integration**: Live capture from ADALM-PLUTO with configurable gain (0-62 dB) and center frequency
- **Automatic Channel Scanner**: Custom GNU Radio OOT block that automatically scans 12 WiFi channels (36-64, 149-161) to detect active networks
- **Real-time Visualization**: Waterfall display and constellation diagrams
- **Dynamic Controls**: Adjustable detection threshold, gain control, channel selection dropdown, and equalization mode selector

## System Architecture

The receiver uses the following signal processing chain:

1. **PlutoSDR Source** → IQ samples at 20 MS/s
2. **Moving Average** → Frame detection
3. **WiFi Sync Short** → Coarse synchronization using short preamble
4. **WiFi Sync Long** → Fine synchronization and channel estimation using long preamble
5. **Stream to Vector + FFT** → OFDM demodulation (64-point FFT)
6. **WiFi Frame Equalizer** → Channel equalization and SIGNAL field decoding
7. **WiFi Decode MAC** → MAC frame decoding
8. **WiFi Parse MAC** → SSID extraction and output

The **Channel Scanner** block runs in parallel, automatically switching frequencies every 5 seconds and monitoring for detected SSIDs.

### Installation

```bash
# Install GNU Radio and dependencies
sudo apt-get update
sudo apt-get install gnuradio python3-pyqt5

# Install PlutoSDR drivers
sudo apt-get install gr-iio libiio-utils

# Install gr-ieee802-11 module
git clone https://github.com/bastibl/gr-ieee802-11.git
cd gr-ieee802-11
mkdir build && cd build
cmake ..
make
sudo make install
sudo ldconfig
```

## Compiling the Custom Channel Scanner Block

This project includes a custom **Out-of-Tree (OOT) module** called `gr-my_blocks` that provides the WiFi Channel Scanner block.

### Build and Install

```bash
# Navigate to the OOT module directory
cd gr-my_blocks

# Create build directory
mkdir -p build
cd build

# Configure with CMake
cmake ..

# Compile the module
make

# Install system-wide (requires sudo)
sudo make install

# Update library cache
sudo ldconfig
```

### Recompile After Modifications

If you modify the scanner code (`gr-my_blocks/python/my_blocks/channel_scanner.py`):

```bash
cd gr-my_blocks/build
make
sudo make install
sudo ldconfig
```

## Usage

### Running the Receiver

1. **Connect the PlutoSDR** via USB or Ethernet (default IP: `192.168.2.1`)

2. **Open the flowgraph in GNU Radio Companion:**
   ```bash
   gnuradio-companion projeto.grc
   ```

3. **Execute the flowgraph:**
   - Click the "Execute" button (▶️) or press **F6**
   - Or run directly from terminal: `python3 projeto.py`

### GUI Controls

- **Threshold Slider:** Adjusts frame detection sensitivity (0.0 - 1.0, default: 0.3)
- **Gain Control:** Sets PlutoSDR RF gain (0 - 62 dB, default: 62 dB for maximum sensitivity)
- **Channel Selector:** Dropdown menu with 12 WiFi channels (Ch 36 - Ch 161)
- **Equalization Mode:** Choose between different equalizer algorithms
- **Scanner Interval:** Time (in seconds) spent on each channel during automatic scanning

### Channel Scanner Operation

The scanner automatically:
1. Cycles through 12 5GHz WiFi channels (36, 40, 44, 48, 52, 56, 60, 64, 149, 153, 157, 161)
2. Listens for 5 seconds on each channel
3. Prints detected SSIDs to console: `✅ Channel 149: SSID "MikroTik-1FB42F"`
4. Continues scanning in an infinite loop

To stop scanning, close the flowgraph or press **Ctrl+C** in the terminal.

## Project Structure

```
CDIG-T02-G08/
├── projeto.grc              # GNU Radio Companion flowgraph
├── projeto.py               # Generated Python flowgraph
├── data.pcap                # Sample WiFi capture file
├── README.md                # This file
├── documentation/           # Technical documentation
│   ├── Frame Detection Analysis.md
│   ├── OFDM System design parameters.md
│   └── Blocks/              # Individual block documentation
└── gr-my_blocks/            # Custom OOT module
    ├── CMakeLists.txt
    ├── python/my_blocks/
    │   └── channel_scanner.py    # Scanner implementation
    └── grc/
        └── my_blocks_channel_scanner.block.yml
```

## Troubleshooting

### PlutoSDR Not Detected

```bash
# Check USB connection
iio_info -u usb:

# Check network connection (if using Ethernet)
iio_info -u ip:192.168.2.1

# Verify gain range
iio_attr -u ip:192.168.2.1 -c ad9361-phy voltage0 hardwaregain_available
```

### No Packets Detected

- Ensure threshold is set to 0.3 or lower
- Maximize gain (62 dB)
- Verify WiFi network is using 802.11a/n/ac (not ax)
- Try different channels using the dropdown selector
- Check PlutoSDR antenna connection

### Scanner Block Not Visible in GRC

```bash
# Reinstall the module
cd gr-my_blocks/build
sudo make install
sudo ldconfig

# Restart GNU Radio Companion
killall -9 gnuradio-companion
gnuradio-companion
```

## Contributors

- **Wagner Daniel Teixeira** - 201908556
- **Maria Leonor Pinto Guedes** - 202107691