import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            "credentials.json", SCOPES
        )
        creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build("calendar", "v3", credentials=creds)

event = {
    "summary": "NEXORA Test Meeting",
    "description": "Meeting created by NEXORA AI Agent",
    "start": {
        "dateTime": "2026-09-19T10:00:00+05:30",
        "timeZone": "Asia/Kolkata",
    },
    "end": {
        "dateTime": "2026-09-19T11:00:00+05:30",
        "timeZone": "Asia/Kolkata",
    },
}

created_event = service.events().insert(
    calendarId="primary",
    body=event
).execute()

print("Meeting created successfully!")
print("Event:", created_event.get("htmlLink"))