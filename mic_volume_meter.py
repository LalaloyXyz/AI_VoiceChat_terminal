import sounddevice as sd
import numpy as np
import time
import os

# Settings
duration = 0.1  # in seconds
sample_rate = 44100
bar_length = 50  # length of the volume bar

def get_mic_volume(indata):
    volume_norm = np.linalg.norm(indata) * 1
    return min(volume_norm, 1.0)  # clamp between 0 and 1

def print_volume_bar(volume):
    bar = "█" * int(volume * bar_length)
    spaces = " " * (bar_length - len(bar))
    # Move cursor to top and print volume bar
    print("\033[1;1H" + f"Mic Volume: [{bar}{spaces}] {volume:.2f}")
    # Flush to ensure immediate output
    print("\033[K", end="", flush=True)

def audio_callback(indata, frames, time_info, status):
    volume = get_mic_volume(indata)
    print_volume_bar(volume)

def show_volume_meter():
    try:
        with sd.InputStream(callback=audio_callback,
                            channels=1,
                            samplerate=sample_rate,
                            blocksize=int(sample_rate * duration)):
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")
