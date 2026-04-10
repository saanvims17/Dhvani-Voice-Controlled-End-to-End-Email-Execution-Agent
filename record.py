# record.py 

import sounddevice as sd
import scipy.io.wavfile as wav
import tempfile
import os

SAMPLE_RATE = 16000


def record_voice(seconds: int = 5) -> str:
    """
    Records audio from microphone and saves to a temp WAV file.
    Returns the file path.
    """

    print(f"\n🎙️ Listening for {seconds} seconds...")

    audio = sd.rec(
        int(seconds * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
    )
    sd.wait()

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    wav.write(path, SAMPLE_RATE, audio)

    print("✅ Recording complete")
    return path