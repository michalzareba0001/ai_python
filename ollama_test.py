import requests
import os
from PyQt6.QtWidgets import (
    QApplication,
    QLineEdit,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit, 
    QDoubleSpinBox,
    QSpinBox,
    QLabel
)
import os.path
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

gmail_api_key = os.getenv("GMAIL_API_KEY")

conversation_history = []
MAX_TURNS = 20
SYSTEM_MESSAGE = {
    "role": "system",
    "content": "Jesteś pomocnym asystentem użytkownika. Odpowiadasz na pytania i wykonujesz zadania na podstawie informacji, które posiadasz. Jeżeli nie znasz odpowiedzi, powiedz to jasno. Nie wymyślaj odpowiedzi na pytania, których nie rozumiesz."
}

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]

def get_gmail_date_query(day="today"):
    timezone = ZoneInfo("Europe/Warsaw")
    now = datetime.now(timezone)

    if day == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

    elif day == "yesterday":
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = today_start - timedelta(days=1)
        end = today_start

    else:
        raise ValueError("Nieznany filtr daty. Użyj: today albo yesterday.")

    start_timestamp = int(start.timestamp())
    end_timestamp = int(end.timestamp())

    return f"after:{start_timestamp} before:{end_timestamp}"


def get_gmail_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            raise RuntimeError("Brak poprawnego token.json. Najpierw uruchom gmail_test.py i zaloguj się do Gmaila.")

    service = build("gmail", "v1", credentials=creds)

    return service


def get_latest_emails(max_results=50, day=None):
    service = get_gmail_service()
    
    gmail_query = None
    
    if day:
        gmail_query = get_gmail_date_query(day)
        

    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results,
        q=gmail_query
    ).execute()

    messages = result.get("messages", [])

    emails = []

    for message in messages:
        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

        headers = msg["payload"].get("headers", [])

        email_data = {
            "id": msg["id"],
            "snippet": msg.get("snippet", ""),
            "from": "",
            "subject": "",
            "date": ""
        }

        for header in headers:
            name = header["name"].lower()

            if name == "from":
                email_data["from"] = header["value"]

            elif name == "subject":
                email_data["subject"] = header["value"]

            elif name == "date":
                email_data["date"] = header["value"]

        emails.append(email_data)

    return emails


def format_emails_for_llm(emails):
    if not emails:
        return "Brak wiadomości w skrzynce odbiorczej."

    formatted_emails = []

    for index, email in enumerate(emails, start=1):
        formatted_emails.append(
            f"""MAIL {index}
            Od: {email["from"]}
            Temat: {email["subject"]}
            Data: {email["date"]}
            Fragment: {email["snippet"]}"""
        )

    return "\n\n".join(formatted_emails)


def should_use_gmail(user_prompt):
    prompt = user_prompt.lower()

    gmail_keywords = [
        "mail",
        "gmail",
        "email",
        "e-mail",
        "wiadomość",
        "wiadomości",
        "poczta",
        "skrzynka",
        "inbox"
    ]

    return any(keyword in prompt for keyword in gmail_keywords)

def on_button_click():
    global conversation_history

    user_prompt = question.text().strip()
    temperature = temperature_input.value()
    top_p = top_p_input.value()

    if not user_prompt:
        answer.setPlainText("Wpisz najpierw pytanie.")
        return

    button.setEnabled(False)
    button.setText("Czekam na odpowiedź...")
    answer.setPlainText("Wysyłam zapytanie...")

    try:
        messages_to_send = [SYSTEM_MESSAGE] + conversation_history[-MAX_TURNS * 2:]

        if should_use_gmail(user_prompt):
            answer.setPlainText("Pobieram ostatnie maile z Gmaila...")

            emails = get_latest_emails(max_results=10)
            gmail_context = format_emails_for_llm(emails)

            prompt_for_model = f"""
                Użytkownik zadał pytanie:

                {user_prompt}

                Poniżej są ostatnie wiadomości z Gmaila. Odpowiedz na pytanie użytkownika wyłącznie na podstawie tych danych. Jeżeli czegoś nie da się ustalić z wiadomości, napisz to jasno.

                DANE Z GMAILA:

                {gmail_context}
            """
        else:
            prompt_for_model = user_prompt

        messages_to_send.append({
            "role": "user",
            "content": prompt_for_model
        })

        answer.setPlainText("Wysyłam dane do lokalnego modelu...")

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "dolphin3:latest",
                "messages": messages_to_send,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": 50
                }
            },
            timeout=600
        )

        response.raise_for_status()

        data = response.json()
        assistant_message = data["message"]["content"]

        conversation_history.append({
            "role": "user",
            "content": user_prompt
        })

        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        conversation_history[:] = conversation_history[-MAX_TURNS * 2:]

        answer.setPlainText(assistant_message)

    except Exception as e:
        answer.setPlainText(f"Wystąpił błąd:\n\n{e}")

    finally:
        button.setEnabled(True)
        button.setText("Get Response")
        print(conversation_history)


app = QApplication([])

window = QWidget()
window.setWindowTitle("OpenAI API Test")
window.resize(600, 400)
layout = QVBoxLayout()
question = QLineEdit()
question.setPlaceholderText("Wpisz pytanie...")
button = QPushButton("Get Response")
answer = QTextEdit()
answer.setReadOnly(True)
temperature_input = QDoubleSpinBox()
temperature_input.setRange(0, 2)
temperature_input.setSingleStep(0.1)
temperature_input.setValue(0.7)
top_p_input = QDoubleSpinBox()
top_p_input.setRange(0, 1)
top_p_input.setSingleStep(0.1)
top_p_input.setValue(1.0)

button.clicked.connect(on_button_click)
question.returnPressed.connect(on_button_click)


layout.addWidget(question)
layout.addWidget(QLabel("Temperature:"))
layout.addWidget(temperature_input)
layout.addWidget(QLabel("Top Propobability (top_p):"))
layout.addWidget(top_p_input)
layout.addWidget(button)
layout.addWidget(answer)
window.setLayout(layout)
window.show()
app.exec()