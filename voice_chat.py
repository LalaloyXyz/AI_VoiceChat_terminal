import speech_recognition as sr
import os
import contextlib
import time
from datetime import datetime
from chat_bot import ask_chat
from text_to_speech import speak
import re
from mic_volume_meter import show_volume_meter
import threading
import pyfiglet

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
        self.conversation_history = []  # Add this line
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
        """Recognize speech in multiple languages, prioritizing recent successes. Returns (text, lang_code) or (None, None)."""
        for (lang_code,) in self.get_optimized_language_order():
            try:
                text = self.r.recognize_google(audio, language=lang_code)
                self.language_success[lang_code] = self.language_success.get(lang_code, 0) + 1
                self.last_successful_language = (lang_code,)
                return text, lang_code
            except sr.UnknownValueError:
                continue
        return None, None

    def background_callback(self, recognizer, audio):
        timestamp = datetime.now().strftime("%H:%M:%S")
        text, lang_code = self.recognize_speech(audio)
        if text:
            print(f"[{timestamp}]")
            print(f"User: ", end="", flush=True)
            for word in text.split():
                print(word + " ", end="", flush=True)
                time.sleep(0.2)
            print()
            self.conversation_history.append(("User", text))
            print("AI: ", end="", flush=True)
            ai_response = ""
            sentence_buffer = ""
            sentence_end_re = re.compile(r"([.!?\u0E2F\u0E46]+)")  # Thai and English sentence end
            for part in ask_chat(self.conversation_history):
                print(part, end="", flush=True)
                ai_response += part
                sentence_buffer += part
                # Check for sentence-ending punctuation
                sentences = []
                while True:
                    match = sentence_end_re.search(sentence_buffer)
                    if not match:
                        break
                    end_idx = match.end()
                    sentences.append(sentence_buffer[:end_idx])
                    sentence_buffer = sentence_buffer[end_idx:]
                for sentence in sentences:
                    if sentence.strip():
                        speak(sentence.strip())
                        time.sleep(0.3 + 0.2 * (len(sentence.split()) // 7))  # Add a natural pause
            # Speak any remaining buffer (in case last chunk doesn't end with punctuation)
            if sentence_buffer.strip():
                speak(sentence_buffer.strip())
            print()
            self.conversation_history.append(("AI", ai_response))
            print("-" * 60)
            # Save conversation to file
            try:
                with open("conversation_log.txt", "a", encoding="utf-8") as f:
                    for role, msg in self.conversation_history[-2:]:
                        f.write(f"{role}: {msg}\n")
            except Exception as e:
                print(f"[Log error: {e}]")

    def start_listening(self):
        """Start background listening using listen_in_background."""
        if not self.is_listening:
            self.is_listening = True
            with suppress_alsa_errors():
                self.stopper = self.r.listen_in_background(
                    self.microphone, self.background_callback
                )
            print("-" * 60)
            return True
        return False

    def stop_listening(self):
        """Stop background listening."""
        self.is_listening = False
        if self.stopper:
            self.stopper(wait_for_stop=False)

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
    os.system("clear")
    #threading.Thread(target=show_volume_meter, daemon=True).start()
    recognizer = AutoSpeechRecognizer()
    ascii_art = pyfiglet.figlet_format("lookchill !", font="standard")
    lines = ascii_art.splitlines()

    # A list of blue-ish colors in ANSI 256 color codes
    colors = [21, 27, 33, 39, 45, 51]  

    for i, line in enumerate(lines):
        color_code = colors[i % len(colors)]
        print(f"\033[38;5;{color_code}m{line}\033[0m")

    try:
        recognizer.run()
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        print("Thank you for using Multi-Language Speech Recognition!")

if __name__ == "__main__":
    main()