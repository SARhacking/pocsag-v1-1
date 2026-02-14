# POCSAG Paging Application

A web-based application for encoding and transmitting POCSAG pager messages through VHF amateur radio repeaters.

## Features

- **Web Interface**: User-friendly web interface for message encoding
- **POCSAG Encoding**: Full implementation of POCSAG protocol with BCH error correction
- **FSK Modulation**: Generates audio signals for radio transmission
- **CTCSS Support**: Adds CTCSS tones for repeater access
- **Audio Output**: Direct transmission through sound card to radio or WAV file generation
- **Testing Tools**: Built-in encoder/decoder testing

## Installation

1. Install system dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip
# Optional: for audio transmission
sudo apt install python3-pyaudio
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Web Interface

Start the web server:
```bash
python app.py
```

Open your browser to `http://localhost:5000` and use the web form to:
- Enter pager RIC and message
- Configure transmission parameters
- Generate WAV files for download
- Transmit audio directly (requires PyAudio)
- Test encoding/decoding

### Command Line (Legacy)

The original command-line interface is still available:
```bash
python main.py -a 123456 -m "Hello World"
```

See below for full command-line options.

- `-a, --address`: Pager RIC (default: 123456)
- `-m, --message`: Message to send (required)
- `-b, --baud`: Baud rate (512, 1200, 2400; default: 1200)
- `-s, --sample-rate`: Audio sample rate (default: 48000)
- `-d, --deviation`: FSK deviation in Hz (default: 4500)
- `-c, --ctcss`: CTCSS tone frequency
- `-o, --output-device`: Audio output device index
- `--list-devices`: List available audio devices
- `--test`: Test encoding without transmission
- `--save-wav`: Save audio to WAV file

## Hardware Setup

1. **Radio Configuration**:
   - Set radio to VHF band (144-148 MHz for 2m)
   - Enable external audio input/modulation
   - Set modulation to wide/narrow FM as appropriate
   - Ensure proper power and antenna setup

2. **Audio Connection**:
   - Connect computer audio output to radio's mic/data input
   - Adjust audio levels to prevent overmodulation
   - Use shielded cables to reduce interference

3. **Repeater Access**:
   - Tune to repeater input frequency
   - Use appropriate CTCSS tone if required
   - Monitor repeater output for confirmation

## Testing

### Local Testing
```bash
# Generate test audio
python main.py -a 123456 -m "Test" --save-wav test.wav

# Decode with multimon-ng (if installed)
sox test.wav -t raw -esigned-integer -b16 -r 48000 - | \
multimon-ng -t raw -a POCSAG1200 -
```

### Radio Testing
1. Start with low power
2. Transmit test message
3. Listen on repeater output frequency
4. Verify message reception on pager

## Safety and Legal Notes

- **Amateur Radio License**: Ensure you have appropriate license for transmission
- **Frequency Compliance**: Only transmit on authorized frequencies
- **Power Limits**: Respect power restrictions for your license class
- **Repeater Courtesy**: Follow repeater usage guidelines
- **Emergency Channels**: Never interfere with emergency communications

## Architecture

- `pocsag.py`: Core POCSAG encoder, decoder, and modulator classes
- `app.py`: Web interface using Flask
- `main.py`: Legacy command-line interface and audio transmission
- `requirements.txt`: Python dependencies
- `templates/`: HTML templates for the web interface

## Protocol Details

- **Baud Rates**: 512, 1200, 2400 bps
- **Modulation**: 2-FSK with ±4.5 kHz deviation
- **Error Correction**: BCH (31,21,5) code
- **Message Format**: 7-bit ASCII with ETX termination

## Troubleshooting

### No Audio Output
- Check audio device selection with `--list-devices`
- Verify audio levels and connections
- Test with `--save-wav` to confirm signal generation

### Poor Reception
- Adjust radio modulation settings
- Check antenna and power setup
- Verify frequency and CTCSS settings
- Try different baud rates

### Decoding Issues
- Ensure correct baud rate matching
- Check for interference on frequency
- Verify pager RIC programming

## Development

The application is modular and extensible:
- Add new modulation schemes
- Implement additional error correction
- Add network interfaces for remote paging
- Integrate with SDR hardware

## References

- POCSAG specification (ITU-R M.584)
- GNU Radio documentation
- Amateur radio repeater directories

## POCSAG Protocol Understanding
POCSAG (Post Office Code Standardization Advisory Group) is a protocol for one-way paging systems. Key characteristics:
- Uses 2-FSK modulation (Frequency Shift Keying)
- Common baud rates: 512, 1200, 2400 bps
- Messages are encoded in batches of 16 codewords
- Each codeword is 32 bits (21 data + 10 CRC + 1 parity)
- Supports both numeric and alphanumeric messages
- Uses preamble for synchronization

## Hardware Requirements

### Minimum Setup
- **VHF Amateur Radio Transceiver**: Capable of transmitting on 144-148 MHz (2m band) or 430-440 MHz (70cm band)
  - Must have audio input for modulation (mic input or data port)
  - Examples: Baofeng UV-5R, Yaesu FT-60R, Kenwood TH-D74A
- **Computer**: Linux-based system (Ubuntu 20.04+ recommended)
  - Sound card or audio interface for modulation input
- **Antenna**: Appropriate for chosen frequency band
- **Power Supply**: For radio transceiver

### Advanced Setup (Recommended for Better Performance)
- **Software Defined Radio (SDR)**: HackRF One, LimeSDR, or similar TX-capable SDR
- **RF Amplifier**: Low-power amplifier for extended range (if needed)
- **GPS Disciplined Oscillator**: For frequency accuracy (optional)

## Software Libraries and Dependencies

### Core Python Libraries
- **pocsag** (PyPI): POCSAG message encoding library
  - Handles protocol encoding, CRC calculation, and message formatting
  - Install: `pip install pocsag`
- **numpy**: Numerical computations for signal processing
- **scipy**: Signal processing for FSK modulation generation
- **pyaudio**: Audio output for radio modulation
- **pyserial**: Radio control via serial/CAT interface (optional)

### Transmission Libraries
- **gnuradio** (GNU Radio): For SDR-based transmission
  - Provides FSK modulation blocks and SDR control
- **librpitx**: For Raspberry Pi-based transmission (alternative)
- **SoX**: Audio processing utilities

### Additional Tools
- **rtl-sdr**: For testing reception (optional)
- **gqrx**: SDR receiver for monitoring transmissions
- **multimon-ng**: POCSAG decoder for testing

## Implementation Architecture

### Core Components
1. **Message Encoder**: Convert text to POCSAG protocol format
2. **Modulation Generator**: Create FSK audio signal from bitstream
3. **Audio Output**: Send modulation to radio's audio input
4. **Radio Control**: PTT (Push-To-Talk) and frequency management
5. **Repeater Interface**: Handle CTCSS tones and repeater access

### Data Flow
```
Text Message → POCSAG Encoder → Bit Stream → FSK Modulator → Audio Signal → Radio → Repeater → Pager
```

## Step-by-Step Implementation Guide

### Phase 1: Environment Setup

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-numpy python3-scipy python3-pyaudio
   sudo apt install gnuradio gnuradio-dev
   sudo apt install sox rtl-sdr gqrx multimon-ng
   pip install pocsag
   ```

2. **Verify Hardware**
   - Connect radio to computer audio output
   - Test audio levels and PTT control
   - Verify radio frequency and modulation settings

### Phase 2: POCSAG Encoding

1. **Basic Message Encoding**
   ```python
   import pocsag

   # Create encoder
   encoder = pocsag.Encoder()

   # Encode message for address 123456 with function bits 3
   message = "HELLO WORLD"
   encoded_data = encoder.encode(123456, message, function_bits=3)

   # encoded_data contains the POCSAG bitstream
   ```

2. **Advanced Encoding Features**
   - Support for numeric messages
   - Multiple repeat transmissions
   - Custom baud rates (512/1200/2400)

### Phase 3: FSK Modulation Generation

1. **Generate FSK Audio**
   ```python
   import numpy as np
   from scipy import signal

   def generate_fsk(bits, baud_rate=1200, deviation=4500, sample_rate=48000):
       # Convert bits to symbols (-1, 1)
       symbols = 2 * np.array(list(bits)) - 1

       # Generate FSK signal
       t = np.arange(len(symbols) * sample_rate // baud_rate) / sample_rate
       phase = 2 * np.pi * deviation * np.cumsum(symbols) / baud_rate
       audio = np.sin(phase[:len(t)])

       return audio.astype(np.float32)
   ```

2. **Add CTCSS Tone (for repeaters)**
   ```python
   def add_ctcss(audio, ctcss_freq=67.0, sample_rate=48000):
       t = np.arange(len(audio)) / sample_rate
       ctcss = 0.1 * np.sin(2 * np.pi * ctcss_freq * t)
       return audio + ctcss
   ```

### Phase 4: Audio Transmission

1. **Audio Output Setup**
   ```python
   import pyaudio

   def transmit_audio(audio_data, sample_rate=48000):
       p = pyaudio.PyAudio()
       stream = p.open(format=pyaudio.paFloat32,
                      channels=1,
                      rate=sample_rate,
                      output=True)

       # Key PTT (if available)
       # transmit_ptt(True)

       stream.write(audio_data.tobytes())

       # Unkey PTT
       # transmit_ptt(False)

       stream.stop_stream()
       stream.close()
       p.terminate()
   ```

2. **Radio Control Integration**
   - Serial/CAT interface for frequency control
   - GPIO control for PTT on Raspberry Pi
   - Audio level adjustment

### Phase 5: Repeater Integration

1. **CTCSS Tone Generation**
   - Standard CTCSS frequencies: 67.0, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8, 97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8, 136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2, 192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3

2. **Repeater Access Sequence**
   - Generate CTCSS tone
   - Wait for repeater hang time
   - Transmit POCSAG signal
   - Allow repeater timeout

### Phase 6: SDR-Based Transmission (Alternative)

1. **GNU Radio Flowgraph**
   - File Source → Throttle → FSK Mod → Osmocom Sink
   - Configure for appropriate frequency and deviation

2. **Python GNU Radio Integration**
   ```python
   from gnuradio import gr, analog, blocks
   import osmosdr

   class PocsagTransmitter(gr.top_block):
       def __init__(self, frequency, audio_file):
           # Setup flowgraph for POCSAG transmission
           pass
   ```

### Phase 7: Testing and Validation

1. **Local Testing**
   - Use rtl-sdr to receive and decode transmissions
   - Verify message integrity with multimon-ng

2. **Repeater Testing**
   - Start with low power
   - Monitor repeater frequency for proper operation
   - Test with known pager addresses

3. **Performance Metrics**
   - Transmission success rate
   - Message decode accuracy
   - Repeater access reliability

## Configuration Management

### Configuration File Structure
```yaml
radio:
  frequency: 146.520e6  # Repeater input frequency
  ctcss: 67.0          # CTCSS tone frequency
  baud_rate: 1200
  deviation: 4500
  audio_device: "hw:0,0"

pocsag:
  default_address: 123456
  function_bits: 3
  repeat_count: 3
  preamble_length: 576

system:
  sample_rate: 48000
  ptt_delay: 0.5
  repeater_hang_time: 2.0
```

## Safety and Legal Considerations

1. **Amateur Radio Licensing**
   - Ensure proper amateur radio license for transmission
   - Operate within authorized frequency bands
   - Respect repeater access rules

2. **Transmission Etiquette**
   - Test transmissions at low power first
   - Avoid interfering with ongoing communications
   - Use appropriate timing between transmissions

3. **Power and Interference**
   - Start with minimum necessary power
   - Monitor for interference
   - Use proper antenna systems

## Future Enhancements

1. **Web Interface**: REST API for remote paging
2. **Database Integration**: Store messages and delivery status
3. **Multi-Channel Support**: Support multiple repeaters/frequencies
4. **Encryption**: Secure message transmission
5. **GPS Integration**: Location-based paging
6. **Network Protocols**: Integration with existing paging networks

## Troubleshooting Guide

### Common Issues
1. **No Audio Output**: Check audio device configuration
2. **Radio Not Transmitting**: Verify PTT control and audio levels
3. **Messages Not Received**: Check frequency, CTCSS, and modulation
4. **Repeater Not Responding**: Verify access tones and timing

### Debug Tools
- Oscilloscope for audio signal verification
- SDR receiver for RF signal analysis
- POCSAG decoder for message validation

## References

- ITU-R Recommendation M.584-2: POCSAG specification
- GNU Radio documentation
- rpitx project (https://github.com/F5OEO/rpitx)
- POCSAG encoder library (https://pypi.org/project/pocsag/)

This plan provides a comprehensive foundation for implementing a POCSAG paging system. The modular design allows for incremental development and testing at each phase.
