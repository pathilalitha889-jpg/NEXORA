import os
import re
import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime

from dotenv import load_dotenv

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


load_dotenv()


# =========================================================
# SETTINGS
# =========================================================

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events"
]


# =========================================================
# DATABASE
# =========================================================

def get_connection():

    conn = sqlite3.connect("nexora.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person TEXT,
            date TEXT,
            time TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            information TEXT
        )
    """)

    conn.commit()

    return conn


# =========================================================
# TASKS
# =========================================================

def add_task(task):

    conn = get_connection()

    conn.execute(
        "INSERT INTO tasks (task) VALUES (?)",
        (task,)
    )

    conn.commit()
    conn.close()

    return "Task Added!"


def get_tasks():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM tasks"
    )

    tasks = cursor.fetchall()

    conn.close()

    return tasks


# =========================================================
# MEETINGS
# =========================================================

def save_meeting(person, date, time):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO meetings (person, date, time)
        VALUES (?, ?, ?)
        """,
        (person, date, time)
    )

    conn.commit()
    conn.close()

    return "Meeting saved!"


def get_meetings():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM meetings"
    )

    meetings = cursor.fetchall()

    conn.close()

    return meetings


# =========================================================
# GOOGLE CALENDAR
# =========================================================

def get_calendar_service():

    creds = None

    if os.path.exists("token.json"):

        creds = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:

            creds.refresh(Request())

        else:

            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES
            )

            creds = flow.run_local_server(
                port=0
            )

        with open(
            "token.json",
            "w"
        ) as token:

            token.write(
                creds.to_json()
            )

    return build(
        "calendar",
        "v3",
        credentials=creds
    )


def create_calendar_event(person, date, time):

    service = get_calendar_service()

    event = {

        "summary":
            f"Meeting with {person}",

        "description":
            "Meeting scheduled by NEXORA AI Agent",

        "start": {

            "dateTime":
                f"{date}T{time}:00+05:30",

            "timeZone":
                "Asia/Kolkata"
        },

        "end": {

            "dateTime":
                f"{date}T{time}:00+05:30",

            "timeZone":
                "Asia/Kolkata"
        }
    }

    created_event = service.events().insert(

        calendarId="primary",

        body=event

    ).execute()

    return created_event.get(
        "htmlLink"
    )


# Keep old function name also working
def schedule_meeting(person, date, time):

    return create_calendar_event(
        person,
        date,
        time
    )


# =========================================================
# EMAIL
# =========================================================

def send_email(
    recipient,
    message,
    attachment_path=None
):

    if not EMAIL_ADDRESS:
        raise ValueError(
            "EMAIL_ADDRESS is missing in .env"
        )

    if not EMAIL_APP_PASSWORD:
        raise ValueError(
            "EMAIL_APP_PASSWORD is missing in .env"
        )

    email = EmailMessage()

    email["From"] = EMAIL_ADDRESS
    email["To"] = recipient
    email["Subject"] = "Message from NEXORA"

    email.set_content(message)

    # -----------------------------------------------------
    # ATTACHMENT
    # -----------------------------------------------------

    if attachment_path:

        if not os.path.exists(
            attachment_path
        ):

            raise FileNotFoundError(
                f"Attachment not found: {attachment_path}"
            )

        with open(
            attachment_path,
            "rb"
        ) as file:

            file_data = file.read()

        file_name = os.path.basename(
            attachment_path
        )

        import mimetypes

        mime_type, _ = mimetypes.guess_type(
            file_name
        )

        if mime_type:

            main_type, sub_type = mime_type.split(
                "/",
                1
            )

        else:

            main_type = "application"
            sub_type = "octet-stream"

        email.add_attachment(

            file_data,

            maintype=main_type,

            subtype=sub_type,

            filename=file_name
        )

    # -----------------------------------------------------
    # SEND
    # -----------------------------------------------------

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465
    ) as server:

        server.login(
            EMAIL_ADDRESS,
            EMAIL_APP_PASSWORD
        )

        server.send_message(
            email
        )

    if attachment_path:

        return (
            "Email sent successfully "
            f"with attachment: "
            f"{os.path.basename(attachment_path)}"
        )

    return "Email sent successfully!"


# =========================================================
# MEMORY
# =========================================================

def save_memory(information):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO memories (information)
        VALUES (?)
        """,
        (information,)
    )

    conn.commit()
    conn.close()

    return "Memory saved successfully!"


def get_memories():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT information FROM memories"
    )

    memories = cursor.fetchall()

    conn.close()

    return [
        memory[0]
        for memory in memories
    ]


# =========================================================
# DOCUMENT READER
# =========================================================

def read_document(file_path):

    if not file_path:

        return {
            "text": "",
            "pages": 0,
            "type": "unknown"
        }

    if not os.path.exists(
        file_path
    ):

        return {
            "text": "",
            "pages": 0,
            "type": "not_found"
        }

    extension = os.path.splitext(
        file_path
    )[1].lower()

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if extension == ".pdf":

        from pypdf import PdfReader

        reader = PdfReader(
            file_path
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            page_text = page.extract_text()

            if page_text:

                pages.append(
                    (
                        page_number,
                        page_text.strip()
                    )
                )

        text = "\n".join(
            page[1]
            for page in pages
        )

        return {
            "text": text,
            "pages": len(reader.pages),
            "type": "PDF",
            "page_data": pages
        }

    # -----------------------------------------------------
    # DOCX
    # -----------------------------------------------------

    if extension == ".docx":

        from docx import Document

        document = Document(
            file_path
        )

        paragraphs = []

        for paragraph in document.paragraphs:

            value = paragraph.text.strip()

            if value:

                paragraphs.append(
                    value
                )

        for table in document.tables:

            for row in table.rows:

                for cell in row.cells:

                    value = cell.text.strip()

                    if value:

                        paragraphs.append(
                            value
                        )

        text = "\n".join(
            paragraphs
        )

        return {
            "text": text,
            "pages": 0,
            "type": "DOCX",
            "page_data": []
        }

    # -----------------------------------------------------
    # TXT
    # -----------------------------------------------------

    if extension == ".txt":

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            text = file.read()

        return {
            "text": text,
            "pages": 0,
            "type": "TXT",
            "page_data": []
        }

    return {
        "text": "",
        "pages": 0,
        "type": "unsupported"
    }


# =========================================================
# DOCUMENT SECTIONS
# =========================================================

def create_sections(text):

    lines = [

        line.strip()

        for line in text.splitlines()

        if line.strip()
    ]

    sections = []

    current = ""

    for line in lines:

        is_heading = bool(
            re.match(
                r"^(chapter|section|unit|topic|question|write|explain|describe|define|what|how|list|program)\b",
                line,
                re.IGNORECASE
            )
        )

        if is_heading:

            if current:

                sections.append(
                    current.strip()
                )

            current = line

        else:

            if current:

                current += " " + line

            else:

                current = line

    if current:

        sections.append(
            current.strip()
        )

    if not sections:

        sections = [
            text[i:i + 1000]

            for i in range(
                0,
                len(text),
                1000
            )
        ]

    return sections


# =========================================================
# DOCUMENT SEARCH
# =========================================================

def search_document(
    question,
    file_path=None
):

    document = read_document(
        file_path
    )

    text = document["text"]

    if not text:

        return {
            "found": False,
            "message":
                "No readable information found."
        }

    sections = create_sections(
        text
    )

    stop_words = {

        "the", "a", "an",
        "is", "are", "was",
        "were", "to", "of",
        "in", "on", "for",
        "and", "or", "with",
        "using", "write",
        "program", "how",
        "what", "explain",
        "give", "me",
        "please", "from",
        "this", "that"
    }

    question_words = set(

        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            question.lower()
        )
    )

    question_words -= stop_words

    results = []

    for section in sections:

        section_words = set(

            re.findall(
                r"\b[a-zA-Z0-9]+\b",
                section.lower()
            )
        )

        common_words = (
            question_words
            & section_words
        )

        score = len(
            common_words
        )

        if score > 0:

            results.append(
                (
                    score,
                    section
                )
            )

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not results:

        return {
            "found": False,
            "message":
                "No relevant information found."
        }

    best_score, best_section = results[0]

    related = [
        section
        for score, section in results[1:4]
    ]

    return {

        "found": True,

        "best_match":
            best_section,

        "score":
            best_score,

        "related":
            related
    }


# =========================================================
# DOCUMENT SUMMARY
# =========================================================

def create_summary(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 30
    ]

    if not sentences:

        return (
            text[:500]
            if text
            else "No summary available."
        )

    # Select important sentences using
    # keyword frequency.

    words = re.findall(
        r"\b[a-zA-Z]{4,}\b",
        text.lower()
    )

    frequency = {}

    for word in words:

        frequency[word] = (
            frequency.get(word, 0) + 1
        )

    scored = []

    for sentence in sentences:

        sentence_words = re.findall(
            r"\b[a-zA-Z]{4,}\b",
            sentence.lower()
        )

        score = sum(
            frequency.get(word, 0)
            for word in sentence_words
        )

        scored.append(
            (
                score,
                sentence
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    selected = [
        sentence
        for _, sentence in scored[:5]
    ]

    return " ".join(
        selected
    )


# =========================================================
# KEY TOPICS
# =========================================================

def extract_topics(text):

    words = re.findall(
        r"\b[a-zA-Z]{4,}\b",
        text.lower()
    )

    stop_words = {

        "this", "that",
        "these", "those",
        "there", "their",
        "which", "where",
        "about", "would",
        "could", "should",
        "have", "has",
        "been", "were",
        "from", "with",
        "into", "using",
        "than", "then",
        "also", "more",
        "some", "such",
        "when", "what",
        "will", "your",
        "they", "them",
        "only", "each"
    }

    frequency = {}

    for word in words:

        if word in stop_words:
            continue

        frequency[word] = (
            frequency.get(word, 0) + 1
        )

    topics = sorted(
        frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        word
        for word, count in topics[:10]
    ]


# =========================================================
# KEY INSIGHTS
# =========================================================

def extract_insights(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    insights = []

    keywords = [

        "important",
        "key",
        "main",
        "advantage",
        "disadvantage",
        "benefit",
        "limitation",
        "used",
        "allows",
        "provides",
        "supports",
        "required",
        "must"
    ]

    for sentence in sentences:

        sentence = sentence.strip()

        if len(sentence) < 30:
            continue

        lower = sentence.lower()

        if any(
            keyword in lower
            for keyword in keywords
        ):

            insights.append(
                sentence
            )

        if len(insights) >= 5:
            break

    if not insights:

        insights = [
            sentence.strip()
            for sentence in sentences
            if len(sentence.strip()) > 40
        ][:5]

    return insights


# =========================================================
# POSSIBLE QUESTIONS
# =========================================================

def generate_questions(
    text,
    sections
):

    questions = []

    for section in sections:

        clean = section.strip()

        if len(clean) < 20:
            continue

        first_line = clean.split(
            "."
        )[0].strip()

        if len(first_line) > 15:

            questions.append(
                f"What is {first_line}?"
            )

        if len(questions) >= 5:
            break

    # Remove duplicates

    unique = []

    for question in questions:

        if question not in unique:

            unique.append(
                question
            )

    return unique[:5]


# =========================================================
# SMART DOCUMENT ANALYSIS
# =========================================================

def analyze_document(
    file_path
):

    document = read_document(
        file_path
    )

    text = document["text"]

    if not text:

        return {
            "error":
                "Unable to read the uploaded document."
        }

    words = re.findall(
        r"\b[\w'-]+\b",
        text
    )

    sections = create_sections(
        text
    )

    summary = create_summary(
        text
    )

    topics = extract_topics(
        text
    )

    insights = extract_insights(
        text
    )

    questions = generate_questions(
        text,
        sections
    )

    file_name = os.path.basename(
        file_path
    )

    result = []

    result.append(
        "📄 Document Analysis"
    )

    result.append(
        f"\nFile: {file_name}"
    )

    result.append(
        f"Type: {document['type']}"
    )

    if document["pages"]:

        result.append(
            f"Pages: {document['pages']}"
        )

    result.append(
        f"Words: {len(words)}"
    )

    result.append(
        f"Sections: {len(sections)}"
    )

    result.append(
        "\n📝 Summary\n"
        + summary
    )

    result.append(
        "\n🔑 Key Topics"
    )

    for topic in topics:

        result.append(
            f"• {topic}"
        )

    result.append(
        "\n💡 Key Insights"
    )

    for insight in insights:

        result.append(
            f"• {insight}"
        )

    result.append(
        "\n❓ Possible Questions"
    )

    for question in questions:

        result.append(
            f"• {question}"
        )

    return "\n".join(
        result
    )


# =========================================================
# RAG / DOCUMENT QUERY
# =========================================================

def ask_document(
    question,
    file_path=None
):

    if not file_path:

        return (
            "Please upload a PDF, DOCX or TXT "
            "file first."
        )

    if not os.path.exists(
        file_path
    ):

        return "Document not found."

    # -----------------------------------------------------
    # SMART ANALYSIS REQUEST
    # -----------------------------------------------------

    analysis_words = [

        "summarize",
        "summary",
        "analyze",
        "analysis",
        "overview",
        "key points",
        "important points",
        "topics",
        "insights",
        "questions",
        "what is this document"
    ]

    question_lower = question.lower()

    if any(
        word in question_lower
        for word in analysis_words
    ):

        return analyze_document(
            file_path
        )

    # -----------------------------------------------------
    # NORMAL DOCUMENT SEARCH
    # -----------------------------------------------------

    result = search_document(
        question,
        file_path
    )

    if not result.get(
        "found"
    ):

        return (
            "No relevant information "
            "found in the document."
        )

    output = []

    output.append(
        "📚 Relevant Information"
    )

    output.append(
        f"\n{result['best_match']}"
    )

    output.append(
        "\n🔗 Related Sections"
    )

    if result["related"]:

        for section in result["related"]:

            output.append(
                f"• {section}"
            )

    else:

        output.append(
            "• No related sections found."
        )

    return "\n".join(
        output
    )


# =========================================================
# OLD COMPATIBILITY FUNCTION
# =========================================================

def read_document_text(file_path):

    document = read_document(
        file_path
    )

    return document["text"]