import pyttsx3
import os
import time
from mutagen.wave import WAVE

def text_to_speech(text: str, lang: str, filename: str) -> None:
    """Convert text to speech."""
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[1].id)
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 0.9)
        engine.save_to_file(text, filename)
        engine.runAndWait()
    except Exception as e:
        print(f"An error occurred during text-to-speech conversion: {e}")

text = """Do you remember your first mobile phones? No internet, just calls and texts. Today, we stream, browse, work... And it all started with GSM and GPRS.
          Hello everyone. Today, I will talk about the evolution of mobile communication. This presentation was made with Professor Khalid Souissi and my classmates Lamrani Ahmed and Compaoré Moustapha. We will explain how GSM and GPRS changed the way we use mobile phones.
          Now, let’s talk about GSM. GSM means Global System for Mobile Communications. It is a second-generation mobile technology, or 2G. It started in Europe in the 1990s and became the standard for mobile phones around the world.”
            “GSM uses digital signals instead of analog. This makes communication more secure and clear. It allows users to make calls, send SMS, and use international roaming.”
            “The GSM network has three main parts:
            BSS: Base Station Subsystem – it connects phones to the network.
            NSS: Network Switching Subsystem – it manages calls and mobility.
            OSS: Operation Support Subsystem – it helps control and maintain the network.”
            “GSM was a big step forward. It made mobile phones more reliable and popular.”
"""

filename = 'output.wav'  # Utilisez .wav

text_to_speech(text, 'en', filename)

# Vérifiez que le fichier existe avant d'obtenir la durée
if os.path.exists(filename):
    duration = WAVE(filename).info.length
    print(f"Durée de l'audio : {duration:.2f} secondes")
    os.system(f'start {filename}')
    time.sleep(2 * duration + 1)
    os.remove(filename)
else:
    print(f"Le fichier {filename} n'a pas été créé.")