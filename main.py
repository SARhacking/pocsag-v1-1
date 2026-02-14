#!/usr/bin/env python3
"""
POCSAG Paging Application

Command-line tool for encoding and transmitting POCSAG pager messages
over VHF amateur radio repeaters.
"""

import argparse
import sys
import numpy as np
from pocsag import POCSAGEncoder, POCSAGModulator, POCSAGDecoder

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False


def transmit_audio(audio_data: np.ndarray, sample_rate: int = 48000,
                  device_index: int = None) -> None:
    """Transmit audio through sound card"""
    if not PYAUDIO_AVAILABLE:
        print("PyAudio not available. Install with: pip install pyaudio")
        print("(Requires portaudio development libraries)")
        return

    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=pyaudio.paFloat32,
                       channels=1,
                       rate=sample_rate,
                       output=True,
                       output_device_index=device_index)

        print("Transmitting audio... (Press Ctrl+C to stop)")
        stream.write(audio_data.tobytes())
        stream.stop_stream()

    except KeyboardInterrupt:
        print("\nTransmission interrupted")
    except Exception as e:
        print(f"Audio transmission error: {e}")
    finally:
        if 'stream' in locals():
            stream.close()
        p.terminate()


def list_audio_devices() -> None:
    """List available audio output devices"""
    if not PYAUDIO_AVAILABLE:
        print("PyAudio not available. Install with: pip install pyaudio")
        return

    p = pyaudio.PyAudio()
    print("Available audio output devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxOutputChannels'] > 0:
            print(f"{i}: {info['name']}")
    p.terminate()


def main():
    parser = argparse.ArgumentParser(description="POCSAG Paging Application")
    parser.add_argument('-a', '--address', type=int, default=123456,
                       help='Pager RIC (Radio Identity Code)')
    parser.add_argument('-m', '--message', type=str, required=True,
                       help='Message to send')
    parser.add_argument('-b', '--baud', type=int, default=1200,
                       choices=[512, 1200, 2400], help='Baud rate')
    parser.add_argument('-s', '--sample-rate', type=int, default=48000,
                       help='Audio sample rate')
    parser.add_argument('-d', '--deviation', type=float, default=4500.0,
                       help='FSK deviation in Hz')
    parser.add_argument('-c', '--ctcss', type=float, default=None,
                       help='CTCSS tone frequency for repeater')
    parser.add_argument('-o', '--output-device', type=int, default=None,
                       help='Audio output device index')
    parser.add_argument('--list-devices', action='store_true',
                       help='List audio devices and exit')
    parser.add_argument('--test', action='store_true',
                       help='Test encoding/decoding without transmission')
    parser.add_argument('--save-wav', type=str, default=None,
                       help='Save audio to WAV file instead of transmitting')

    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    # Encode message
    print(f"Encoding message '{args.message}' for RIC {args.address}")
    encoder = POCSAGEncoder()
    encoded_data = encoder.encode_message(args.address, args.message)
    print(f"Encoded {len(encoded_data)} bytes")

    # Convert to bits
    modulator = POCSAGModulator()
    bits = modulator.bits_from_bytes(encoded_data)

    # Generate FSK audio
    print(f"Generating FSK audio at {args.baud} baud, {args.sample_rate} Hz sample rate")
    audio = modulator.generate_fsk(bits, args.baud, args.deviation, args.sample_rate)

    # Add CTCSS if specified
    if args.ctcss:
        print(f"Adding CTCSS tone at {args.ctcss} Hz")
        audio = modulator.add_ctcss(audio, args.ctcss, args.sample_rate)

    if args.test:
        # Test decode
        print("Testing decode...")
        decoder = POCSAGDecoder()
        result = decoder.decode_bits(bits)
        if result:
            print(f"Decoded: {result}")
        else:
            print("Decoding failed")
        return

    if args.save_wav:
        # Save to WAV file
        import wave
        print(f"Saving to {args.save_wav}")
        with wave.open(args.save_wav, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(args.sample_rate)
            wav_file.writeframes((audio * 32767).astype(np.int16).tobytes())
        print("WAV file saved")
        return

    # Transmit
    print("WARNING: Ensure your radio is properly configured and legal to transmit!")
    print("Connect audio output to radio's modulation input")
    input("Press Enter to transmit (or Ctrl+C to cancel)...")

    transmit_audio(audio, args.sample_rate, args.output_device)


if __name__ == "__main__":
    main()