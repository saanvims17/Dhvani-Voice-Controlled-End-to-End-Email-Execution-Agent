# speak_script.py 

import pyttsx3


def speak(text: str):
    text = str(text).strip()
    if not text:
        return

    print(f"\n🔊 Dhvani says: {text}")

    engine = pyttsx3.init()
    engine.setProperty("rate", 150)
    engine.setProperty("volume", 0.9)
    engine.say(text)
    engine.runAndWait()
    engine.stop()