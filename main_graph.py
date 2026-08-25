"""
main.py  

Voice-controlled email assistant.
Each loop iteration runs one full LangGraph email session.
Say 'stop', 'exit', 'quit', 'bye', 'thank you', or 'goodbye' cto exit.
"""

from record import record_voice
from transcribe import transcribe_audio
from agent_graph import run_email_agent
from speak_script import speak

EXIT_WORDS = {"stop", "exit", "quit", "bye", "thank you", "goodbye"}


def _is_exit(text: str) -> bool:
    return text.lower().strip() in EXIT_WORDS


def run() -> None:
    print("\n" + "=" * 60)
    print("  Dhvani — Voice Email Assistant  (LangGraph edition)")
    print("  Say 'stop' or 'exit' to quit")
    print("=" * 60)

    while True:
        try:
            # The greeting + first listen happen INSIDE the graph now.
            # We just kick off a new graph run each iteration.
            run_email_agent()

        except KeyboardInterrupt:
            speak("Goodbye.")
            break
        except Exception as e:
            print(f"[main] Error: {e}")
            speak("Something went wrong. Let's try again.")
            continue

        # After the graph finishes, ask if the user wants to send another.
        speak("Would you like to send another email, or shall I stop?")
        try:
            path = record_voice(seconds=5)
            reply = transcribe_audio(path).strip()
        except Exception:
            reply = ""

        if _is_exit(reply) or not reply:
            speak("Goodbye.")
            break


if __name__ == "__main__":
    run()
