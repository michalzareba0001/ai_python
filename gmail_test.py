import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


def get_gmail_service():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    return service


def get_latest_emails(max_results=5):
    service = get_gmail_service()

    result = service.users().messages().list(
        userId="me",
        labelIds=["INBOX"],
        maxResults=max_results
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

            if name == "subject":
                email_data["subject"] = header["value"]

            if name == "date":
                email_data["date"] = header["value"]

        emails.append(email_data)

    return emails


emails = get_latest_emails(5)

for email in emails:
    print("OD:", email["from"])
    print("TEMAT:", email["subject"])
    print("DATA:", email["date"])
    print("FRAGMENT:", email["snippet"])
    print("-" * 50)