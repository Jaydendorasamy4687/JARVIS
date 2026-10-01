import sys
import json
import os
import re
import base64
import hashlib
import imaplib
import email
from email.header import decode_header
import threading
import time
import webbrowser

# Audio Engine
import pyaudio

# GUI & Qt
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# Audio & Voice
import pyttsx3
import speech_recognition as sr

# Web & AI
from duckduckgo_search import DDGS
from openai import OpenAI

# Microsoft 365 Libraries
import docx
import openpyxl
from pptx import Presentation

# Spotify Integration
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Cryptography (AES-256-GCM Encryption)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Initialize OpenAI Client (Uses environment variable)
api_key = os.environ.get("OPENAI_API_KEY", "")
client = OpenAI(api_key=api_key) if api_key else None


# --------------------------------------------------------------
# 1. Iron Man J.A.R.V.I.S. Voice Engine Configuration
# --------------------------------------------------------------

def configure_jarvis_voice(tts_engine):
    """Tunes speech rate and voice selection to sound like J.A.R.V.I.S."""
    tts_engine.setProperty('rate', 165)
    tts_engine.setProperty('volume', 1.0)

    voices = tts_engine.getProperty('voices')
    selected_voice = None

    # Priority check for English/British male voice profiles
    for voice in voices:
        name_lower = voice.name.lower()
        if any(term in name_lower for term in
               ["george", "hazel", "david", "james", "uk", "english_gb", "great britain"]):
            selected_voice = voice.id
            break

    if not selected_voice and len(voices) > 0:
        selected_voice = voices[0].id

    if selected_voice:
        tts_engine.setProperty('voice', selected_voice)


# --------------------------------------------------------------
# 2. Local Execution Tools & Security Engine
# --------------------------------------------------------------

def encrypt_file_or_data(target_path_or_content: str, passphrase: str = "JARVIS_SECURE_KEY_2026") -> str:
    """
    Encrypts a code file, software app, or sensitive text using AES-256-GCM.
    Derives a 256-bit symmetric key using SHA-256 and appends a 12-byte random nonce.
    """
    try:
        # Derive 32-byte key from passphrase
        key = hashlib.sha256(passphrase.encode('utf-8')).digest()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit random nonce for GCM

        if os.path.exists(target_path_or_content):
            with open(target_path_or_content, 'rb') as f:
                data = f.read()
            ciphertext = aesgcm.encrypt(nonce, data, None)
            encrypted_payload = base64.b64encode(nonce + ciphertext).decode('ascii')

            out_file = target_path_or_content + ".enc"
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(encrypted_payload)
            return f"File '{target_path_or_content}' successfully encrypted with AES-256-GCM to '{out_file}'."
        else:
            data = target_path_or_content.encode('utf-8')
            ciphertext = aesgcm.encrypt(nonce, data, None)
            encrypted_payload = base64.b64encode(nonce + ciphertext).decode('ascii')
            return f"Data successfully encrypted (AES-256-GCM Payload):\n{encrypted_payload}"
    except Exception as e:
        return f"Encryption error: {str(e)}"


def decrypt_file_or_data(encrypted_file_or_payload: str, passphrase: str = "JARVIS_SECURE_KEY_2026") -> str:
    """Decrypts AES-256-GCM encrypted files or raw payload strings."""
    try:
        key = hashlib.sha256(passphrase.encode('utf-8')).digest()
        aesgcm = AESGCM(key)

        if os.path.exists(encrypted_file_or_payload):
            with open(encrypted_file_or_payload, 'r', encoding='utf-8') as f:
                raw_payload = f.read()
        else:
            raw_payload = encrypted_file_or_payload

        raw = base64.b64decode(raw_payload)
        nonce, ciphertext = raw[:12], raw[12:]
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)

        if os.path.exists(encrypted_file_or_payload) and encrypted_file_or_payload.endswith(".enc"):
            orig_name = encrypted_file_or_payload[:-4]
            with open(orig_name, 'wb') as f:
                f.write(decrypted_bytes)
            return f"Encrypted file restored successfully to '{orig_name}'."

        return f"Decrypted Data Output:\n{decrypted_bytes.decode('utf-8', errors='ignore')}"
    except Exception as e:
        return f"Decryption error (Invalid key or tampered data): {str(e)}"


def safe_search_web(query: str) -> str:
    """Searches the web for facts, developer docs, or local businesses."""
    try:
        raw_results = list(DDGS().text(query, max_results=5))
        verified = []
        for r in raw_results:
            verified.append({
                "title": r.get("title"),
                "snippet": r.get("body"),
                "url": r.get("href")
            })
        return json.dumps(verified) if verified else "No search results found."
    except Exception as e:
        return f"Web search error: {str(e)}"


def find_small_businesses_and_emails(industry: str, location: str = "Pietermaritzburg") -> str:
    """Finds local small businesses in Pietermaritzburg requiring websites and extracts contact emails."""
    query = f"small {industry} in {location} contact email website address"
    raw = safe_search_web(query)

    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails_found = re.findall(email_pattern, raw)

    result = {
        "search_results": json.loads(raw) if raw.startswith("[") else raw,
        "discovered_emails": list(set(emails_found))
    }
    return json.dumps(result)


def calculate_website_discount_and_pricing(base_price: float, discount_percentage: float = 0.0,
                                           tax_rate: float = 0.0) -> str:
    """Calculates website client pricing, discounts, sales reductions, tax subtotals, and savings breakdown."""
    try:
        discount_amount = base_price * (discount_percentage / 100.0)
        subtotal = base_price - discount_amount
        tax_amount = subtotal * (tax_rate / 100.0)
        final_total = subtotal + tax_amount

        breakdown = {
            "original_base_price": round(base_price, 2),
            "discount_percentage": discount_percentage,
            "discount_savings": round(discount_amount, 2),
            "subtotal_after_discount": round(subtotal, 2),
            "tax_applied": round(tax_amount, 2),
            "final_payable_total": round(final_total, 2)
        }
        return json.dumps(breakdown)
    except Exception as e:
        return f"Calculation error: {str(e)}"


def draft_client_email(recipient_name: str, business_name: str, proposal_details: str, price_quote: str) -> str:
    """Drafts formal client outreach email proposals for website services."""
    return f"""Subject: Website Development & Modernization Proposal for {business_name}

Dear {recipient_name},

I hope this email finds you well.

I recently reviewed {business_name} and identified key opportunities to optimize your digital presence. A fast, modern website will convert prospective leads and improve brand visibility.

Proposed Project Deliverables:
{proposal_details}

Pricing & Discount Structure:
{price_quote}

I would welcome the opportunity to connect and discuss how we can build a solution tailored specifically for {business_name}.

Best regards,
Web Development Services
"""


def check_incoming_emails(email_address: str, app_password: str, imap_server: str = "imap.gmail.com") -> str:
    """Connects via SSL IMAP to check inbox for website project inquiries."""
    if not email_address or not app_password:
        return "Email credentials missing. Please supply email address and password."
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_address, app_password)
        mail.select("inbox")

        status, messages = mail.search(None, '(UNSEEN SUBJECT "website")')
        email_ids = messages[0].split()

        if not email_ids:
            return "No new unseen website inquiries found in inbox."

        summary = []
        for e_id in email_ids[-3:]:
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for part in msg_data:
                if isinstance(part, tuple):
                    msg = email.message_from_bytes(part[1])
                    sub, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(sub, bytes):
                        sub = sub.decode(encoding if encoding else "utf-8")
                    from_addr = msg.get("From")
                    summary.append(f"From: {from_addr} | Subject: {sub}")

        mail.logout()
        return "Incoming website inquiries:\n" + "\n".join(summary)
    except Exception as e:
        return f"IMAP inbox check error: {str(e)}"


def play_music_spotify(song_or_playlist: str) -> str:
    """Triggers Spotify music playback via browser URI handler."""
    try:
        search_url = f"https://open.spotify.com/search/{song_or_playlist.replace(' ', '%20')}"
        webbrowser.open(search_url)
        return f"Opening Spotify search for '{song_or_playlist}'."
    except Exception as e:
        return f"Spotify launch error: {str(e)}"


def add_song_to_spotify_liked(song_name: str, artist_name: str = "") -> str:
    """Saves a song directly to Spotify Liked Songs via Spotipy API."""
    try:
        scope = "user-library-modify user-read-playback-state"
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        query = f"track:{song_name} artist:{artist_name}" if artist_name else song_name
        results = sp.search(q=query, limit=1, type="track")
        tracks = results.get("tracks", {}).get("items", [])

        if not tracks:
            return f"Could not locate '{song_name}' on Spotify."

        track_id = tracks[0]["id"]
        title = tracks[0]["name"]
        artist = tracks[0]["artists"][0]["name"]
        sp.current_user_saved_tracks_add(tracks=[track_id])
        return f"Successfully added '{title}' by {artist} to your Liked Songs."
    except Exception as e:
        return f"Spotify API error: {str(e)}"


def create_word_docx(filename: str, title: str, content: str) -> str:
    """Generates Microsoft Word (.docx) document."""
    try:
        doc = docx.Document()
        doc.add_heading(title, 0)
        for p in content.split("\n\n"):
            doc.add_paragraph(p)
        path = filename if filename.endswith(".docx") else f"{filename}.docx"
        doc.save(path)
        return f"Word document saved as '{path}'."
    except Exception as e:
        return f"Failed creating Word document: {str(e)}"


def create_excel_spreadsheet(filename: str, headers: str, data_rows: str) -> str:
    """Generates Microsoft Excel (.xlsx) spreadsheet."""
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Data"
        ws.append([h.strip() for h in headers.split(",")])

        if data_rows:
            for row in data_rows.split(";"):
                ws.append([cell.strip() for cell in row.split(",")])

        path = filename if filename.endswith(".xlsx") else f"{filename}.xlsx"
        wb.save(path)
        return f"Excel spreadsheet saved as '{path}'."
    except Exception as e:
        return f"Failed creating Excel file: {str(e)}"


def create_powerpoint_presentation(filename: str, title: str, slides_content: str) -> str:
    """Generates Microsoft PowerPoint (.pptx) presentation. Format slides separated by '||'."""
    try:
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = title
        slide.placeholders[1].text = "Generated by J.A.R.V.I.S."

        for slide_text in slides_content.split("||"):
            if not slide_text.strip():
                continue
            lines = slide_text.strip().split("\n")
            s = prs.slides.add_slide(prs.slide_layouts[1])
            s.shapes.title.text = lines[0]
            tf = s.placeholders[1].text_frame
            for line in lines[1:]:
                p = tf.add_paragraph()
                p.text = line

        path = filename if filename.endswith(".pptx") else f"{filename}.pptx"
        prs.save(path)
        return f"PowerPoint presentation saved as '{path}'."
    except Exception as e:
        return f"Failed creating PowerPoint presentation: {str(e)}"


def generate_code_file(filename: str, language: str, code_content: str) -> str:
    """Generates software source code in HTML, CSS, JS, Kotlin, or Python."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_content)
        return f"Source code file '{filename}' ({language}) created successfully."
    except Exception as e:
        return f"Failed creating source file: {str(e)}"


AVAILABLE_TOOLS = {
    "encrypt_file_or_data": encrypt_file_or_data,
    "decrypt_file_or_data": decrypt_file_or_data,
    "safe_search_web": safe_search_web,
    "find_small_businesses_and_emails": find_small_businesses_and_emails,
    "calculate_website_discount_and_pricing": calculate_website_discount_and_pricing,
    "draft_client_email": draft_client_email,
    "check_incoming_emails": check_incoming_emails,
    "play_music_spotify": play_music_spotify,
    "add_song_to_spotify_liked": add_song_to_spotify_liked,
    "create_word_docx": create_word_docx,
    "create_excel_spreadsheet": create_excel_spreadsheet,
    "create_powerpoint_presentation": create_powerpoint_presentation,
    "generate_code_file": generate_code_file
}

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "encrypt_file_or_data",
            "description": "Encrypts a file, app, website source code, or text using AES-256-GCM authenticated encryption.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_path_or_content": {"type": "string"},
                    "passphrase": {"type": "string"}
                },
                "required": ["target_path_or_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "decrypt_file_or_data",
            "description": "Decrypts an AES-256-GCM encrypted file or payload string back to original form.",
            "parameters": {
                "type": "object",
                "properties": {
                    "encrypted_file_or_payload": {"type": "string"},
                    "passphrase": {"type": "string"}
                },
                "required": ["encrypted_file_or_payload"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_small_businesses_and_emails",
            "description": "Locates local small businesses in Pietermaritzburg requiring websites and extracts contact emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "industry": {"type": "string"},
                    "location": {"type": "string"}
                },
                "required": ["industry"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_website_discount_and_pricing",
            "description": "Calculates website pricing quotes, discount percentages, savings, and tax subtotals.",
            "parameters": {
                "type": "object",
                "properties": {
                    "base_price": {"type": "number"},
                    "discount_percentage": {"type": "number"},
                    "tax_rate": {"type": "number"}
                },
                "required": ["base_price"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "draft_client_email",
            "description": "Drafts formal outreach proposal emails to prospective web development clients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient_name": {"type": "string"},
                    "business_name": {"type": "string"},
                    "proposal_details": {"type": "string"},
                    "price_quote": {"type": "string"}
                },
                "required": ["recipient_name", "business_name", "proposal_details", "price_quote"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_incoming_emails",
            "description": "Checks inbox for new incoming messages regarding website projects over IMAP.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_address": {"type": "string"},
                    "app_password": {"type": "string"}
                },
                "required": ["email_address", "app_password"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_music_spotify",
            "description": "Plays music or opens search on Spotify.",
            "parameters": {
                "type": "object",
                "properties": {"song_or_playlist": {"type": "string"}},
                "required": ["song_or_playlist"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_song_to_spotify_liked",
            "description": "Saves a track to Spotify Liked Songs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "song_name": {"type": "string"},
                    "artist_name": {"type": "string"}
                },
                "required": ["song_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_word_docx",
            "description": "Creates a Word (.docx) document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["filename", "title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_excel_spreadsheet",
            "description": "Creates an Excel (.xlsx) spreadsheet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "headers": {"type": "string"},
                    "data_rows": {"type": "string"}
                },
                "required": ["filename", "headers"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_powerpoint_presentation",
            "description": "Creates a PowerPoint (.pptx) presentation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "title": {"type": "string"},
                    "slides_content": {"type": "string"}
                },
                "required": ["filename", "title", "slides_content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_code_file",
            "description": "Generates source code in HTML, CSS, JavaScript, Kotlin, Jetpack Compose, or Python.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "language": {"type": "string"},
                    "code_content": {"type": "string"}
                },
                "required": ["filename", "language", "code_content"]
            }
        }
    }
]


# --------------------------------------------------------------
# 3. Holographic PyQt5 Circular HUD Interface
# --------------------------------------------------------------

class JarvisHUD(QWidget):
    speak_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("J.A.R.V.I.S. Core Interface")
        self.resize(600, 600)
        self.setStyleSheet("background-color: #030812;")

        self.angle = 0
        self.is_talking = False
        self.is_processing = False

        self.speak_signal.connect(self._handle_speech)

        self.tts = pyttsx3.init()
        configure_jarvis_voice(self.tts)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(33)

    def update_animation(self):
        speed = 7.0 if self.is_talking else (4.0 if self.is_processing else 1.5)
        self.angle = (self.angle + speed) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() // 2, self.height() // 2

        glow = QColor(0, 240, 255) if self.is_talking else (
            QColor(255, 170, 0) if self.is_processing else QColor(0, 140, 190, 160))

        # Outer Dash Circle
        pen = QPen(glow, 2, Qt.DashLine)
        painter.setPen(pen)
        painter.drawEllipse(cx - 180, cy - 180, 360, 360)

        # Rotating Arc Ring
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        pen = QPen(glow, 4)
        painter.setPen(pen)
        painter.drawArc(-130, -130, 260, 260, 0, 110 * 16)
        painter.drawArc(-130, -130, 260, 260, 180 * 16, 110 * 16)
        painter.restore()

        # Inner Ring
        pen = QPen(glow, 2)
        painter.setPen(pen)
        painter.drawEllipse(cx - 85, cy - 85, 170, 170)

        # Labels
        status = "TALKING" if self.is_talking else ("THINKING" if self.is_processing else "LISTENING")
        painter.setPen(QPen(QColor(0, 240, 255)))
        painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
        painter.drawText(cx - 70, cy - 15, 140, 30, Qt.AlignCenter, "J.A.R.V.I.S.")

        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QPen(glow))
        painter.drawText(cx - 70, cy + 12, 140, 20, Qt.AlignCenter, status)

    def speak(self, text: str):
        self.speak_signal.emit(text)

    def _handle_speech(self, text: str):
        def run_speech():
            self.is_talking = True
            print(f"\nJ.A.R.V.I.S.: {text}\n")
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception as e:
                print(f"TTS Speech Error: {e}")
            self.is_talking = False

        threading.Thread(target=run_speech, daemon=True).start()


# --------------------------------------------------------------
# 4. Voice Core & Continuous Processing Thread
# --------------------------------------------------------------

SYSTEM_PROMPT = """
You are J.A.R.V.I.S., an advanced AI assistant created to aid with software development, business outreach, encryption, document management, and audio playback.
System Guidelines:
1. Speak calmly, confidently, and professionally like J.A.R.V.I.S. from Iron Man.
2. Generate clean, production-ready source code files (HTML, CSS, JavaScript, Kotlin, Jetpack Compose, Python).
3. Search for small businesses in Pietermaritzburg, extract contact email addresses, calculate discounted sales quotes, and draft client outreach emails.
4. Protect software and files when requested by calling 'encrypt_file_or_data' (AES-256-GCM encryption).
5. Keep verbal spoken answers succinct, clear, and direct.
"""


def listen_continuously(recognizer: sr.Recognizer, microphone: sr.Microphone, hud: JarvisHUD):
    """Calibrates microphone ambient noise threshold and listens for speech continuously."""
    with microphone as source:
        print("[Calibrating microphone ambient noise...]")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        print("[Microphone active]")

    hud.speak("Systems operational and online. Voice interface ready, sir.")

    while True:
        if hud.is_talking:
            time.sleep(0.3)
            continue

        try:
            with microphone as source:
                print("\n[Listening...]")
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=12)

            hud.is_processing = True
            print("[Analyzing speech input...]")

            user_text = recognizer.recognize_google(audio)
            print(f"User: '{user_text}'")

            if any(term in user_text.lower() for term in ["shutdown", "power off", "exit jarvis"]):
                hud.speak("Powering down system core. Goodbye, sir.")
                time.sleep(2)
                QApplication.quit()
                break

            process_query(user_text, hud)

        except sr.WaitTimeoutError:
            hud.is_processing = False
            continue
        except sr.UnknownValueError:
            hud.is_processing = False
            continue
        except Exception as e:
            print(f"[Microphone Exception: {e}]")
            hud.is_processing = False
            time.sleep(1)


def process_query(user_prompt: str, hud: JarvisHUD):
    if not client:
        hud.speak("OpenAI API key missing. Please verify environment settings.")
        hud.is_processing = False
        return

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools_schema
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                fname = call.function.name
                args = json.loads(call.function.arguments)
                print(f"[Invoking Tool: {fname} with args {args}]")

                if fname in AVAILABLE_TOOLS:
                    output = AVAILABLE_TOOLS[fname](**args)
                else:
                    output = f"Tool '{fname}' not available."

                messages.append({"tool_call_id": call.id, "role": "tool", "name": fname, "content": str(output)})

            final_resp = client.chat.completions.create(model="gpt-4o", messages=messages)
            hud.is_processing = False
            hud.speak(final_resp.choices[0].message.content)
        else:
            hud.is_processing = False
            hud.speak(msg.content)

    except Exception as e:
        hud.is_processing = False
        hud.speak(f"An error occurred while executing that command: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    hud = JarvisHUD()
    hud.show()

    rec = sr.Recognizer()
    mic = sr.Microphone()

    listen_thread = threading.Thread(target=listen_continuously, args=(rec, mic, hud), daemon=True)
    listen_thread.start()

    sys.exit(app.exec_())