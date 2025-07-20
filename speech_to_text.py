import speech_recognition as sr
import os
import contextlib
import time
from datetime import datetime

@contextlib.contextmanager
def suppress_alsa_errors():
    with open(os.devnull, 'w') as fnull:
        stderr = os.dup(2)
        os.dup2(fnull.fileno(), 2)
        try:
            yield
        finally:
            os.dup2(stderr, 2)
            os.close(stderr)

class AutoSpeechRecognizer:
    def __init__(self):
        self.r = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.stopper = None
        self.languages = [
            ("th-TH",),
            ("en-US",)
        ]
        self.language_success = {}
        self.last_successful_language = None
        print("Calibrating microphone...")
        with suppress_alsa_errors():
            with self.microphone as source:
                self.r.adjust_for_ambient_noise(source, duration=1)
        self.r.energy_threshold = 4000
        self.r.dynamic_energy_threshold = True
        self.r.pause_threshold = 0.8
        self.r.phrase_threshold = 0.3
        self.r.non_speaking_duration = 0.5

    def get_optimized_language_order(self):
        """Return languages sorted by recent success and usage."""
        languages = self.languages.copy()
        if self.last_successful_language:
            languages = [lang for lang in languages if lang[0] != self.last_successful_language[0]]
            languages.insert(0, self.last_successful_language)
        languages.sort(key=lambda x: self.language_success.get(x[0], 0), reverse=True)
        return languages

    def recognize_speech(self, audio):
        """Recognize speech in multiple languages, prioritizing recent successes."""
        for (lang_code,) in self.get_optimized_language_order():
            try:
                text = self.r.recognize_google(audio, language=lang_code)
                self.language_success[lang_code] = self.language_success.get(lang_code, 0) + 1
                self.last_successful_language = (lang_code,)
                return text
            except sr.UnknownValueError:
                continue
        return None

    def background_callback(self, recognizer, audio):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Processing speech...")
        text = self.recognize_speech(audio)
        if text:
            print(f"[{timestamp}] : {text}")
        else:
            print(f"[{timestamp}] Could not recognize speech in any language")
        print("-" * 40)

    def start_listening(self):
        """Start background listening using listen_in_background."""
        if not self.is_listening:
            self.is_listening = True
            with suppress_alsa_errors():
                self.stopper = self.r.listen_in_background(
                    self.microphone, self.background_callback,
                    phrase_time_limit=3
                )
            print("Auto-listening started! Speak anytime...")
            print("=" * 60)
            return True
        return False

    def stop_listening(self):
        """Stop background listening."""
        self.is_listening = False
        if self.stopper:
            self.stopper(wait_for_stop=False)
        print("Speech recognition stopped")

    def run(self):
        """Main run loop. Keeps the program alive until interrupted."""
        try:
            self.start_listening()
            while self.is_listening:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt detected")
            self.stop_listening()
        except Exception as e:
            print(f"Fatal error: {e}")
            self.stop_listening()

def main():
    recognizer = AutoSpeechRecognizer()
    print("Fully Automatic Multi-Language Speech Recognition")
    try:
        recognizer.run()
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        print("Thank you for using Multi-Language Speech Recognition!")

if __name__ == "__main__":
    main()