# transcribe.py

"""
Converts a WAV audio file to text using faster-whisper.
Run this file directly to test transcription.
"""

from faster_whisper import WhisperModel
import os

# Load the Whisper model once (small model = fast, good enough for commands)
# Options: "tiny", "base", "small", "medium", "large-v3"
_model = None


def get_model():
    """Lazy-load the Whisper model so it only loads once."""
    global _model
    if _model is None:
        print("⏳ Loading Whisper model (first time only)...")
        # cpu + int8 = fast, low memory usage
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        print("✅ Whisper model loaded.")
    return _model


def transcribe_audio(audio_path: str) -> str:
    """
    Converts audio file to text.

    Args:
        audio_path: Path to the WAV file

    Returns:
        Transcribed text string
    """
    model = get_model()

    # Run transcription
    segments, info = model.transcribe(audio_path, beam_size=5, language="en")

    # Join all segments into one string
    text = " ".join(segment.text.strip() for segment in segments)

    print(f"📝 Transcribed: {text}")
    return text.strip()


# Test this file directly
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python step2_transcribe.py path/to/audio.wav")
    else:
        result = transcribe_audio(sys.argv[1])
        print(f"Result: {result}")