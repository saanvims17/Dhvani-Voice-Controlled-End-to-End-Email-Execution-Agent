"""
agent_graph.py

Dhvani — Voice Email Assistant (LangGraph version)
Replaces agent.py with a proper LangGraph state machine.

Graph nodes:
  listen_and_greet  → detect_intent → resolve_recipient
  → draft_email → confirm_loop → send_email | cancel

All other files (record.py, transcribe.py, email_tools.py,
people_search.py, speak_script.py, ms_auth.py) are unchanged.
"""

from __future__ import annotations

from typing import Literal, Optional
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END

from email_tools import draft_email, edit_email, send_email
from people_search import resolve_recipient as search_recipient
from record import record_voice
from speak_script import speak
from transcribe import transcribe_audio


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class EmailState(TypedDict, total=False):
    # set by listen_and_greet
    user_text: str

    # set by detect_intent
    recipient_name: str          # raw name extracted from speech
    email_context: str           # full spoken sentence used for drafting

    # set by resolve_recipient
    resolved_name: str
    resolved_email: str
    candidate_matches: list[dict]  # used when multiple contacts are found

    # set by draft_email
    draft: dict                  # {"subject": ..., "body": ...}

    # terminal status
    status: Literal["sent", "cancelled", "error", "no_intent", "no_recipient"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_meaningless(text: str) -> bool:
    cleaned = text.strip().replace(".", "").replace(",", "").replace("?", "")
    return not cleaned or len(cleaned) < 2


def _listen(seconds: int) -> str:
    path = record_voice(seconds=seconds)
    return transcribe_audio(path).strip()


def _speak_draft(state: EmailState) -> None:
    draft = state["draft"]
    speak(f"I drafted an email to {state['resolved_name']}.")
    speak(f"The subject is: {draft['subject']}.")
    speak("The body is.")
    for part in draft["body"].split("."):
        part = part.strip()
        if part:
            speak(part + ".")
    speak("Should I send it, edit it, or cancel?")


# ---------------------------------------------------------------------------
# Node: listen_and_greet
# ---------------------------------------------------------------------------

def listen_and_greet(state: EmailState) -> EmailState:
    """
    Greet the user, then record 8 seconds of speech and transcribe it.
    """
    speak("Hey, I'm Dhvani! Whom do you want me to mail, and regarding what?")
    user_text = _listen(seconds=8)
    print(f"[listen_and_greet] heard: {user_text!r}")
    return {"user_text": user_text}


# ---------------------------------------------------------------------------
# Node: detect_intent
# ---------------------------------------------------------------------------

def detect_intent(state: EmailState) -> EmailState:
    """
    Extract recipient name + full context from the transcribed sentence.
    Falls back gracefully when no email intent is found.
    """
    text = state.get("user_text", "")
    lowered = text.lower()

    if "email" not in lowered and "mail" not in lowered:
        speak("That doesn't sound like an email request. Please try again.")
        return {"status": "no_intent"}

    words = text.replace(",", " ").split()
    lowered_words = [w.lower() for w in words]

    recipient_name = ""
    if "to" in lowered_words:
        idx = lowered_words.index("to")
        if idx + 1 < len(words):
            recipient_name = words[idx + 1].strip(",. ")

    if not recipient_name:
        speak("I couldn't catch the recipient's name. Please try again.")
        return {"status": "no_recipient"}

    return {
        "recipient_name": recipient_name,
        "email_context": text,
    }


def _route_after_intent(state: EmailState) -> str:
    """
    Edge: after detect_intent, retry on failure or continue.
    """
    status = state.get("status", "")
    if status in ("no_intent", "no_recipient"):
        return "listen_and_greet"   # loop back to greeting
    return "resolve_recipient"


# ---------------------------------------------------------------------------
# Node: resolve_recipient
# ---------------------------------------------------------------------------

def resolve_recipient(state: EmailState) -> EmailState:
    """
    Look up the recipient in Outlook contacts / local fallback.
    If multiple matches, speak them and listen for the user's choice.
    """
    name = state["recipient_name"]
    speak(f"Searching for {name}.")

    matches = search_recipient(name)  # from people_search.py

    # No matches at all
    if not matches:
        speak(f"I couldn't find anyone named {name}.")
        return {"status": "no_recipient"}

    # Exactly one match with a usable email
    clean = [m for m in matches if m.get("email")]
    if len(clean) == 1:
        speak(f"Found {clean[0]['name']}.")
        return {
            "resolved_name": clean[0]["name"],
            "resolved_email": clean[0]["email"],
        }

    # Multiple matches — let the user pick
    speak(f"I found {len(clean)} matches.")
    for i, person in enumerate(clean[:5], start=1):
        label = f"Option {i}. {person['name']}"
        if person.get("email"):
            label += f". {person['email']}"
        speak(label)

    speak("Please say the option number.")
    choice_text = _listen(seconds=4).lower().strip()

    number_words = {
        "one": 1, "1": 1,
        "two": 2, "2": 2,
        "three": 3, "3": 3,
        "four": 4, "4": 4,
        "five": 5, "5": 5,
    }
    selected = number_words.get(choice_text)
    if selected and 1 <= selected <= len(clean):
        person = clean[selected - 1]
        speak(f"Got it. Using {person['name']}.")
        return {
            "resolved_name": person["name"],
            "resolved_email": person["email"],
        }

    speak("I couldn't understand the choice.")
    return {"status": "no_recipient"}


def _route_after_resolve(state: EmailState) -> str:
    if state.get("status") == "no_recipient":
        return END
    return "draft_email_node"


# ---------------------------------------------------------------------------
# Node: draft_email_node
# ---------------------------------------------------------------------------

def draft_email_node(state: EmailState) -> EmailState:
    """
    Ask Mistral to draft the email, then read it aloud.
    """
    speak(f"Drafting your email to {state['resolved_name']}. One moment.")
    draft = draft_email(state["email_context"], state["resolved_name"])
    speak("Done! Here's what I came up with.")
    return {"draft": draft}


# ---------------------------------------------------------------------------
# Node: confirm_loop
# ---------------------------------------------------------------------------

def confirm_loop(state: EmailState) -> EmailState:
    """
    Read the draft aloud and listen for: send / edit / cancel.
    On 'edit', revise the draft and loop (by returning status='edit').
    """
    _speak_draft(state)
    action = _listen(seconds=4).lower().strip()
    print(f"[confirm_loop] action heard: {action!r}")

    if _is_meaningless(action):
        speak("I didn't catch that. Please say send, edit, or cancel.")
        return {"status": "edit"}   # re-enter confirm_loop

    if any(w in action for w in ("send", "yes", "confirm", "go ahead")):
        return {"status": "sent"}

    if "edit" in action:
        speak("Tell me what to change.")
        instruction = _listen(seconds=6).strip()
        print(f"[confirm_loop] edit instruction: {instruction!r}")
        if _is_meaningless(instruction):
            speak("I didn't catch the edit. Please try again.")
            return {"status": "edit"}
        revised = edit_email(state["draft"], instruction)
        return {"draft": revised, "status": "edit"}

    if any(w in action for w in ("cancel", "stop", "no")):
        return {"status": "cancelled"}

    speak("Please say send, edit, or cancel.")
    return {"status": "edit"}


def _route_after_confirm(state: EmailState) -> str:
    status = state.get("status", "")
    if status == "sent":
        return "send_email_node"
    if status == "cancelled":
        return "cancel_node"
    return "confirm_loop"   # includes 'edit' — re-reads updated draft


# ---------------------------------------------------------------------------
# Node: send_email_node
# ---------------------------------------------------------------------------

def send_email_node(state: EmailState) -> EmailState:
    success = send_email(
        state["resolved_email"],
        state["resolved_name"],
        state["draft"]["subject"],
        state["draft"]["body"],
    )
    if success:
        speak("Email sent successfully.")
        return {"status": "sent"}
    speak("I couldn't send the email. Please try again later.")
    return {"status": "error"}


# ---------------------------------------------------------------------------
# Node: cancel_node
# ---------------------------------------------------------------------------

def cancel_node(state: EmailState) -> EmailState:
    speak("Okay, I've cancelled the email.")
    return {"status": "cancelled"}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    g = StateGraph(EmailState)

    g.add_node("listen_and_greet",  listen_and_greet)
    g.add_node("detect_intent",     detect_intent)
    g.add_node("resolve_recipient", resolve_recipient)
    g.add_node("draft_email_node",  draft_email_node)
    g.add_node("confirm_loop",      confirm_loop)
    g.add_node("send_email_node",   send_email_node)
    g.add_node("cancel_node",       cancel_node)

    g.set_entry_point("listen_and_greet")

    g.add_edge("listen_and_greet", "detect_intent")

    g.add_conditional_edges(
        "detect_intent",
        _route_after_intent,
        {
            "listen_and_greet":  "listen_and_greet",
            "resolve_recipient": "resolve_recipient",
        },
    )

    g.add_conditional_edges(
        "resolve_recipient",
        _route_after_resolve,
        {
            "draft_email_node": "draft_email_node",
            END: END,
        },
    )

    g.add_edge("draft_email_node", "confirm_loop")

    g.add_conditional_edges(
        "confirm_loop",
        _route_after_confirm,
        {
            "send_email_node": "send_email_node",
            "cancel_node":     "cancel_node",
            "confirm_loop":    "confirm_loop",
        },
    )

    g.add_edge("send_email_node", END)
    g.add_edge("cancel_node",     END)

    return g.compile()


# ---------------------------------------------------------------------------
# Public entry point (called from main.py)
# ---------------------------------------------------------------------------

email_graph = build_graph()


def run_email_agent() -> None:
    """
    Run one full email session.
    main.py calls this in a loop; each call is one email request.
    """
    final = email_graph.invoke({})
    print(f"[run_email_agent] final status: {final.get('status')}")