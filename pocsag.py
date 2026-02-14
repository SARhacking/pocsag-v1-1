#!/usr/bin/env python3
"""
POCSAG Encoder and Decoder for Amateur Radio Paging

This module provides functionality to encode and decode POCSAG pager messages
for transmission over VHF amateur radio repeaters.
"""

import struct
import numpy as np
from typing import List, Tuple, Optional

# POCSAG Constants
PREAMBLE_LENGTH = 72  # Minimum 576 bits
FRAME_LENGTH = 64  # 1 batch = 8 frames * 8 bytes
NUM_FRAMES = FRAME_LENGTH // 4  # 16 x 4 bytes = 64 bytes
PREAMBLE_FILL = 0xAA
FUNCTION_CODE = 0x03  # Alpha mode
FRAMESYNC_CODEWORD = 0x7CD215D8
IDLE_CODEWORD = 0x7A89C197
NUM_BITS_INT = 31
MAX_MSG_LENGTH = 40
DEFAULT_ADDRESS = 1234567
ADDRESS_MASK = 0xFFFFF800  # Valid data bits 1-21, 22-31 BCH, 32 parity
G_X = 0x769  # BCH polynomial


class POCSAGEncoder:
    """POCSAG message encoder"""

    @staticmethod
    def bit_reverse_8(b: int) -> int:
        """Reverse bits in a byte"""
        b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
        b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
        b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
        return b

    @staticmethod
    def calculate_bch_3121_sum(x: int) -> int:
        """Calculate BCH (31,21,5) checksum"""
        k = 21
        generator = G_X << k
        dividend = x & ADDRESS_MASK

        mask = 1 << NUM_BITS_INT
        for i in range(k):
            if dividend & mask:
                dividend ^= generator
            generator >>= 1
            mask >>= 1

        return x | dividend

    @staticmethod
    def calculate_even_parity(x: int) -> int:
        """Calculate even parity bit"""
        count = 0
        for i in range(1, NUM_BITS_INT):
            if x & (1 << i):
                count += 1
        parity = count % 2
        return x | parity

    @staticmethod
    def encode_address(address: int) -> int:
        """Encode pager address into POCSAG codeword"""
        # Remove least significant 3 bits (frame offset)
        addr = address >> 3
        addr &= 0x0007FFFF
        addr <<= 2

        # Add function bits
        addr |= FUNCTION_CODE
        addr <<= 11

        # Calculate BCH and parity
        addr = POCSAGEncoder.calculate_bch_3121_sum(addr)
        addr = POCSAGEncoder.calculate_even_parity(addr)

        addr = (addr >> 24) | ((addr >> 8) & 0xFF00) | ((addr << 8) & 0xFF0000) | (addr << 24)  # htonl
        addr &= 0xFFFFFFFF

        return addr

    @staticmethod
    def ascii_7bit_encoder(message: str) -> bytes:
        """Encode ASCII string to 7-bit format"""
        length = len(message)
        encoded_length = int((7/8) * length) + 1
        encoded = bytearray(encoded_length)

        shift = 1
        curr_idx = 0

        for char in message:
            tmp = POCSAGEncoder.bit_reverse_8(ord(char))
            tmp &= 0x00FE  # Remove 8th bit
            tmp >>= 1
            tmp <<= shift

            if curr_idx < len(encoded):
                encoded[curr_idx] |= (tmp & 0x00FF)
            if curr_idx > 0:
                encoded[curr_idx - 1] |= ((tmp & 0xFF00) >> 8)

            shift += 1
            if shift == 8:
                shift = 0
            else:
                curr_idx += 1

        return bytes(encoded[:encoded_length])

    @staticmethod
    def split_message_into_frames(ascii_7bit: bytes) -> List[int]:
        """Split 7-bit message into 20-bit frames with checksum and parity"""
        length = len(ascii_7bit)
        chunks = (length // 3) + 1
        batches = []

        curr = 0
        for i in range(chunks):
            batch = 0
            if length - curr >= 3:
                batch = struct.unpack('>I', ascii_7bit[curr:curr+3] + b'\x00')[0]
            else:
                remaining = ascii_7bit[curr:]
                batch = struct.unpack('>I', remaining + b'\x00' * (3 - len(remaining)))[0]

            batch = (batch >> 24) | ((batch >> 8) & 0xFF00) | ((batch << 8) & 0xFF0000) | (batch << 24)  # htonl equivalent

            if i % 2 == 0:
                if length - curr >= 3:
                    curr += 2
                batch &= 0xFFFFF000
                batch >>= 1
            else:
                if length - curr >= 3:
                    curr += 3
                batch &= 0x0FFFFF00
                batch <<= 3

            batch |= (1 << NUM_BITS_INT)  # Set MSB for message

            batch = POCSAGEncoder.calculate_bch_3121_sum(batch)
            batch = POCSAGEncoder.calculate_even_parity(batch)

            batch = (batch >> 24) | ((batch >> 8) & 0xFF00) | ((batch << 8) & 0xFF0000) | (batch << 24)  # htonl
            batch &= 0xFFFFFFFF  # Ensure 32-bit unsigned

            batches.append(batch)

        return batches

    @staticmethod
    def encode_message(address: int, message: str) -> bytes:
        """Encode complete POCSAG message"""
        # Preamble
        preamble = bytes([PREAMBLE_FILL] * PREAMBLE_LENGTH)

        # Frame offset
        frame_offset = address & 0x7

        # Encode address
        encoded_address = POCSAGEncoder.encode_address(address)

        # Encode message
        if not message:
            message_frames = [IDLE_CODEWORD]
        else:
            ascii_7bit = POCSAGEncoder.ascii_7bit_encoder(message + '\x03')  # ETX
            message_frames = POCSAGEncoder.split_message_into_frames(ascii_7bit)

        # Calculate total frames needed
        frames_left = frame_offset + len(message_frames)
        total_batches = (frames_left + NUM_FRAMES - 1) // NUM_FRAMES

        output = bytearray()
        output.extend(preamble)

        message_parts_done = 0
        codewords_done = 0

        for batch in range(total_batches):
            packet = bytearray(FRAME_LENGTH + 4)
            # Frame sync
            struct.pack_into('>I', packet, 0, FRAMESYNC_CODEWORD)
            index = 4

            # Fill with idles until frame offset
            for i in range(frame_offset):
                if codewords_done >= NUM_FRAMES:
                    break
                struct.pack_into('>I', packet, index, IDLE_CODEWORD)
                index += 4
                codewords_done += 2  # Two idles per frame?

            # Add address if first batch
            if batch == 0 and frame_offset < NUM_FRAMES:
                struct.pack_into('>I', packet, index, encoded_address)
                index += 4
                codewords_done += 1

            # Add message frames
            while message_parts_done < len(message_frames) and codewords_done < NUM_FRAMES:
                struct.pack_into('>I', packet, index, message_frames[message_parts_done])
                index += 4
                message_parts_done += 1
                codewords_done += 1

            # Fill rest with idles
            while codewords_done < NUM_FRAMES:
                struct.pack_into('>I', packet, index, IDLE_CODEWORD)
                index += 4
                codewords_done += 1

            output.extend(packet[:index])
            codewords_done = 0

        return bytes(output)


class POCSAGDecoder:
    """Simple POCSAG decoder for testing"""

    @staticmethod
    def decode_bits(bits: List[int]) -> Optional[Tuple[int, str]]:
        """Decode POCSAG bitstream (simplified)"""
        # This is a basic implementation - for production use multimon-ng
        # Look for frame sync
        sync_pos = -1
        for i in range(len(bits) - 32):
            codeword = 0
            for j in range(32):
                codeword |= bits[i + j] << (31 - j)
            if codeword == FRAMESYNC_CODEWORD:
                sync_pos = i + 32
                break

        if sync_pos == -1:
            return None

        # Decode frames (simplified - only handles basic messages)
        messages = []
        i = sync_pos
        while i < len(bits) - 32:
            codeword = 0
            for j in range(32):
                if i + j >= len(bits):
                    break
                codeword |= bits[i + j] << (31 - j)

            # Check if it's an address codeword (MSB = 0)
            if not (codeword & (1 << 31)):
                address = (codeword >> 13) & 0x7FFFF
                function = (codeword >> 11) & 0x3
                messages.append(f"Address: {address}, Function: {function}")
            # Message codeword (MSB = 1)
            else:
                # Extract 20-bit message data
                data = (codeword >> 11) & 0xFFFFF
                # Convert back to 7-bit ASCII (simplified)
                chars = []
                for shift in range(0, 20, 7):
                    char_bits = (data >> shift) & 0x7F
                    if char_bits:
                        chars.append(chr(char_bits))
                if chars:
                    messages.append("Message: " + ''.join(chars))

            i += 32

        return (0, ' | '.join(messages)) if messages else None


class POCSAGModulator:
    """FSK modulator for POCSAG signals"""

    @staticmethod
    def generate_fsk(bits: List[int], baud_rate: int = 1200,
                    deviation: float = 4500.0, sample_rate: int = 48000) -> np.ndarray:
        """Generate FSK audio from bitstream"""
        symbols = np.array([1 if b else -1 for b in bits])
        samples_per_symbol = sample_rate // baud_rate

        t = np.arange(len(symbols) * samples_per_symbol) / sample_rate
        phase = 2 * np.pi * deviation * np.cumsum(np.repeat(symbols, samples_per_symbol)) / baud_rate
        audio = np.sin(phase[:len(t)])

        return audio.astype(np.float32)

    @staticmethod
    def add_ctcss(audio: np.ndarray, ctcss_freq: float = 67.0,
                 sample_rate: int = 48000, level: float = 0.1) -> np.ndarray:
        """Add CTCSS tone for repeater access"""
        t = np.arange(len(audio)) / sample_rate
        ctcss = level * np.sin(2 * np.pi * ctcss_freq * t)
        return audio + ctcss

    @staticmethod
    def bits_from_bytes(data: bytes) -> List[int]:
        """Convert bytes to bit list (MSB first)"""
        bits = []
        for byte in data:
            for i in range(7, -1, -1):  # MSB first
                bits.append((byte >> i) & 1)
        return bits


if __name__ == "__main__":
    # Example usage
    encoder = POCSAGEncoder()
    modulator = POCSAGModulator()

    # Encode a message
    address = 123456
    message = "HELLO WORLD"
    encoded = encoder.encode_message(address, message)

    print(f"Encoded {len(encoded)} bytes")

    # Convert to bits and modulate
    bits = modulator.bits_from_bytes(encoded)
    audio = modulator.generate_fsk(bits)

    print(f"Generated {len(audio)} audio samples")

    # Save to file (for testing)
    import wave
    with wave.open('test_pocsag.wav', 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(48000)
        wav_file.writeframes((audio * 32767).astype(np.int16).tobytes())

    print("Saved to test_pocsag.wav")