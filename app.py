#!/usr/bin/env python3
"""
POCSAG Web Application

Web interface for encoding and transmitting POCSAG pager messages
over VHF amateur radio repeaters.
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import os
import tempfile
import numpy as np
from pocsag import POCSAGEncoder, POCSAGModulator, POCSAGDecoder

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'pocsag_secret_key'  # For flash messages

def transmit_audio(audio_data: np.ndarray, sample_rate: int = 48000,
                  device_index: int = None) -> str:
    """Transmit audio through sound card and return status"""
    if not PYAUDIO_AVAILABLE:
        return "PyAudio not available. Install with: pip install pyaudio"

    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=pyaudio.paFloat32,
                       channels=1,
                       rate=sample_rate,
                       output=True,
                       output_device_index=device_index)

        stream.write(audio_data.tobytes())
        stream.stop_stream()
        status = "Audio transmitted successfully"

    except Exception as e:
        status = f"Audio transmission error: {e}"
    finally:
        if 'stream' in locals():
            stream.close()
        p.terminate()

    return status

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            address = int(request.form['address'])
            message = request.form['message']
            baud = int(request.form['baud'])
            sample_rate = int(request.form['sample_rate'])
            deviation = float(request.form['deviation'])
            ctcss = request.form.get('ctcss')
            ctcss = float(ctcss) if ctcss else None
            device_index = request.form.get('device_index')
            device_index = int(device_index) if device_index else None

            action = request.form['action']

            # Encode message
            encoder = POCSAGEncoder()
            encoded_data = encoder.encode_message(address, message)

            # Convert to bits
            modulator = POCSAGModulator()
            bits = modulator.bits_from_bytes(encoded_data)

            # Generate FSK audio
            audio = modulator.generate_fsk(bits, baud, deviation, sample_rate)

            # Add CTCSS if specified
            if ctcss:
                audio = modulator.add_ctcss(audio, ctcss, sample_rate)

            if action == 'generate_wav':
                # Save to temporary WAV file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                    import wave
                    with wave.open(tmp_file.name, 'wb') as wav_file:
                        wav_file.setnchannels(1)
                        wav_file.setsampwidth(2)
                        wav_file.setframerate(sample_rate)
                        wav_file.writeframes((audio * 32767).astype(np.int16).tobytes())
                    return send_file(tmp_file.name, as_attachment=True, download_name='pocsag_message.wav')

            elif action == 'transmit':
                if not PYAUDIO_AVAILABLE:
                    flash("PyAudio not available for transmission", "error")
                    return redirect(url_for('index'))

                status = transmit_audio(audio, sample_rate, device_index)
                flash(status, "info")
                return redirect(url_for('index'))

            elif action == 'test':
                # Test decode
                decoder = POCSAGDecoder()
                result = decoder.decode_bits(bits)
                if result:
                    flash(f"Decoded: {result[1]}", "success")
                else:
                    flash("Decoding failed", "error")
                return redirect(url_for('index'))

        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            return redirect(url_for('index'))

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)