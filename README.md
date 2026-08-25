# Dhvani-Voice-Controlled-End-to-End-Email-Execution-Agent
Dhvani is a fully voice-controlled email assistant that lets you compose, edit, and send emails using natural speech, entirely hands-free. It intelligently finds the right contact, drafts emails using AI, reads them back for confirmation, and sends them seamlessly, all from your terminal. 

*BEST PART, It completes the entire workflow within 2 minutes*

**Complete working DEMO of Dhvani:** https://drive.google.com/drive/folders/18pp01rziYekyIabpfDsnuT3YSdyPEIeo 


<img width="497" height="170" alt="Screenshot 2026-04-08 at 5 50 06 PM" src="https://github.com/user-attachments/assets/fce15362-6dee-4301-8507-b561d5d8243d" />

---
**How it works**

<img width="497" height="566" alt="Screenshot 2026-04-08 at 5 49 03 PM" src="https://github.com/user-attachments/assets/2d0e640c-de32-4e9e-8c66-c73cc662b12a" />

It uses faster-whisper for speech-to-text, Ollama / Mistral for email drafting and editing, Microsoft Graph API for sending via your Outlook account, and LangGraph to orchestrate the end-to-end conversation flow as a typed state machine.

--- 

### Project structure

Speech-to-text/

│

├── **agent_graph.py**      # LangGraph state machine — the brain of Dhvani

├── **main.py**             # Entry point; runs the graph in a loop until "stop"

│

├── **email_tools.py**      # draft_email(), edit_email(), send_email() via Graph API

├── **people_search.py**    # search Outlook contacts 

├── **ms_auth.py**          # MSAL device-flow auth; caches token in token_cache.bin

│

├── **record.py**           # Records mic input → temp WAV file (sounddevice)

├── **transcribe.py**       # WAV → text (faster-whisper, lazy-loaded)

├── **speak_script.py**     # Text → speech (pyttsx3)

├── **token_cache.bin**     # Auto-created after first login (gitignore this)

├── **.env**                # Secrets 

│

└── **requirements.txt**

--- 

**Requirements**
Dependency	Purpose

- Python 3.10 – 3.13	Runtime 

- Ollama, Local LLM server for Mistral

- A Microsoft 365 account	Sending email + reading Outlook contacts, A registered Azure app	OAuth credentials for Graph API

- PortAudio	Required by sounddevice for mic access

Python version note: LangChain / LangGraph currently ship Pydantic v1 shims that are incompatible with Python 3.14. Use Python 3.10, 3.11, 3.12, or 3.13.

--- 
**Setup** 

**Microsoft 365 (Outlook Integration)** 

1. Go to https://portal.azure.com  

2. Create a new app:  

   - Azure Active Directory → App registrations → New registration  

   - Choose **Personal Microsoft accounts** (or both for work accounts)

3. Copy:

   - `MS_CLIENT_ID` (Application ID)

   - `MS_TENANT_ID` (`consumers` for personal accounts)

4. Enable:

   - Authentication → **Allow public client flows = Yes**

5. Add API Permissions (Microsoft Graph → Delegated):

   - `User.Read`

   - `Contacts.Read`

   - `Mail.Send`

6. Grant admin consent (if required)

---

**Ollama (Local AI - Mistral)**

Install and run:

**macOS**

brew install ollama

**Linux**

curl -fsSL https://ollama.com/install.sh | sh

ollama pull mistral

ollama serve

---

### Voice command reference

**Starting a request**
Say anything that includes the words **mail or email** and a recipient after to:

**What you say**	                                    **What Dhvani does**

- "Send a mail to Priya telling I'll be late today"	    Finds Priya, drafts the message

- "Email to Rahul regarding the project update"	        Finds Rahul, drafts the message
  
- "Send an email to Saanvi letting her know the 	      Finds Saanvi, drafts the message

   meeting is cancelled"
  
**At the confirm step** 

**What you say**	                                    **Action** 

"Send" / "Yes" / "Confirm"                            Sends the email

"Edit"	                                              Listens for your edit instruction

"Cancel" / "Stop" / "No"	                            Cancels and discards the draft

**Edit instruction examples** 

After saying "edit", speak your instruction:

- "Make the tone more formal"

- "Change the meeting time to 11 AM"

- "Add that I will send the report by end of day"

- "Make it shorter"

Dhvani will revise the draft with Mistral and read it aloud again.

**Exiting**
Say any of these at the "send another email?" prompt to quit:

stop · exit · quit · bye · thank you · goodbye

Or press Ctrl+C at any time.

---

**Running the assistant**

Make sure Ollama is running (ollama serve) and your virtual environment is active: 

*Dhvani will greet you and start listening immediately. A typical session looks like this:*

============================================================

  Dhvani — Voice Email Assistant 
  
  Say 'stop' or 'exit' to quit
  
============================================================

🔊 Dhvani says: Hey, I'm Dhvani! Whom do you want me to mail, and regarding what?

🎙️ Listening for 8 seconds...

✅ Recording complete

📝 Transcribed: Send a mail to Nishanth telling let's meet on Monday at 10 AM.

🔊 Dhvani says: Searching for Nishanth.

🔊 Dhvani says: Found Nishanth Kumar.

🔊 Dhvani says: Drafting your email to Nishanth Kumar. One moment.

✍️ Drafting email with Mistral...

🔊 Dhvani says: Done! Here's what I came up with.

🔊 Dhvani says: I drafted an email to Nishanth Kumar.

🔊 Dhvani says: The subject is: Meeting on Monday.

🔊 Dhvani says: The body is. Hi Nishanth, I wanted to check if you're available
                 for a meeting on Monday at 10 AM. Please let me know. Thanks.
                 
🔊 Dhvani says: Should I send it, edit it, or cancel?

🎙️ Listening for 4 seconds...

📝 Transcribed: Send it.

📤 Sending email to Nishanth Kumar (nishanth@example.com)...

✅ Email sent successfully!

🔊 Dhvani says: Email sent successfully.

--- 

