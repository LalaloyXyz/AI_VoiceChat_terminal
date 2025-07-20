import io
import time
import threading
import numpy as np
import sounddevice as sd

# Language detection
try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    print("❌ Install langdetect: pip install langdetect")

# Google TTS for Thai
try:
    from gtts import gTTS
    import pygame
    GOOGLE_TTS_AVAILABLE = True
    pygame.mixer.init()  # Pre-initialize mixer for faster playback
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    print("❌ Install Google TTS: pip install gtts pygame")

# Coqui TTS (VCTK multispeaker model) for English
try:
    from TTS.api import TTS
    tts = TTS(model_name="tts_models/en/vctk/vits")
    LOCAL_TTS_AVAILABLE = True
except Exception as e:
    tts = None
    LOCAL_TTS_AVAILABLE = False
    print(f"❌ Coqui TTS load failed: {e}")

# Choose a female speaker from VCTK (check tts.speakers for options)
SPEAKER = "p225"

def detect_language(text: str) -> str:
    if not LANGDETECT_AVAILABLE:
        print("⚠️ Language detection unavailable, defaulting to English.")
        return "en"
    try:
        return detect(text)
    except Exception:
        return "en"

def play_pygame(fp):
    pygame.mixer.music.load(fp)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.wait(50)  # Reduced wait for faster response

def speak_google_tts(text: str, lang: str = "th"):
    if not GOOGLE_TTS_AVAILABLE:
        print("Google TTS not available.")
        return
    try:
        gtts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        gtts.write_to_fp(fp)
        fp.seek(0)
        t = threading.Thread(target=play_pygame, args=(fp,))
        t.start()
        t.join()  # Wait for playback to finish
    except Exception as e:
        print(f"Google TTS Error: {e}")

def speak_local_tts(text: str, speaker: str = SPEAKER):
    if not LOCAL_TTS_AVAILABLE:
        print("Local TTS not available.")
        return
    try:
        print(f"🗣️ Speaking with speaker '{speaker}'")
        wav = tts.tts(text=text, speaker=speaker)
        sr = tts.synthesizer.output_sample_rate
        t = threading.Thread(target=sd.play, args=(wav, sr))
        t.start()
        t.join()  # Wait for playback to finish
    except Exception as e:
        print(f"Local TTS Error: {e}")

def speak(text: str):
    lang = detect_language(text)
    print(f"🔊 Detected language: {lang.upper()} | Text: {text[:50]}...")
    if lang.startswith("th"):
        speak_google_tts(text, lang="th")
    elif lang.startswith("en"):
        speak_local_tts(text, speaker=SPEAKER)
    else:
        print(f"⚠️ Language '{lang}' unsupported. No TTS available for this language.")
        # Do not fallback to English TTS

def list_speakers():
    if LOCAL_TTS_AVAILABLE:
        print("🗣️ Available speakers:")
        for s in tts.speakers:
            print(" -", s)

if __name__ == "__main__":
    list_speakers()
    speak("Hello, how are you?")
    speak("สวัสดี ยินดีที่ได้รู้จัก")
