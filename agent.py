import os
import re
from datetime import datetime, timedelta
from typing import TypedDict

from dotenv import load_dotenv
from openai import OpenAI
import tools

from langgraph.graph import StateGraph, START, END


# =========================================================
# SETUP
# =========================================================

load_dotenv()

try:
    client = OpenAI()
except Exception:
    client = None

# =========================================================
# STATE
# =========================================================

class AgentState(TypedDict):
    command: str
    action: str
    result: str
    file_path: str
    permission_granted: bool


# =========================================================
# PERMISSION
# =========================================================

def ask_permission(
    action,
    permission_granted=False
):

    # Browser Allow already clicked
    if permission_granted:
        return True

    print(
        f"\nPermission required for: {action}"
    )

    # Streamlit UI
    if os.getenv("NEXORA_UI") == "1":
        return False

    # Terminal
    choice = input(
        "Do you want to allow this action? (yes/no): "
    )

    return choice.lower().strip() == "yes"


# =========================================================
# LOCAL CLASSIFICATION
# =========================================================

def local_classify(command):

    text = command.lower().strip()

    # EMAIL
    if (
        ("send" in text and
         ("email" in text or "mail" in text))
        or "email" in text
        or "mail" in text
    ):
        return "SEND_EMAIL"

    # MEETING
    if (
        "schedule" in text
        or "book a meeting" in text
        or "create a meeting" in text
        or "meeting with" in text
    ):
        return "MEETING"

    # SHOW MEETING
    if (
        "show my meeting" in text
        or "show meetings" in text
        or "list meetings" in text
        or "my meetings" in text
        or "what meetings" in text
    ):
        return "SHOW_MEETING"

    # SHOW TASK
    if (
        "show my task" in text
        or "show tasks" in text
        or "list tasks" in text
        or "my tasks" in text
        or "what are my tasks" in text
    ):
        return "SHOW_TASK"

    # MEMORY
    memory_phrases = [
        "remember this",
        "remember that",
        "remember:",
        "save this",
        "save that",
        "store this",
        "store that",
        "do you remember",
        "what do you remember",
        "what did i tell you",
        "what did i say",
        "show my memory",
        "show memories",
        "my memories",
        "retrieve memory",
        "retrieve memories",
        "recall"
    ]

    if any(
        phrase in text
        for phrase in memory_phrases
    ):
        return "MEMORY"

    # RAG / DOCUMENT
    rag_words = [
        "pdf",
        "document",
        "uploaded file",
        "uploaded document",
        "docx",
        "txt",
        "summarize",
        "summary",
        "analyze document",
        "analyze this document",
        "key topics",
        "key insights",
        "possible questions",
        "relevant information",
        "search document",
        "what does the document say",
        "what is this document about",
        "jdbc",
        "preparedstatement",
        "resultset",
        "batch update",
        "batch updates",
        "database connection"
    ]

    if any(
        word in text
        for word in rag_words
    ):
        return "RAG"

    # ADD TASK
    if (
        "add task" in text
        or "add a task" in text
        or "create task" in text
        or "create a task" in text
        or "new task" in text
        or "remind me" in text
    ):
        return "ADD_TASK"

    return "OTHER"


# =========================================================
# AI CLASSIFICATION
# =========================================================

def analyze_request(state):

    print("\nAnalyzing request...")

    command = state["command"]

    try:

        response = client.responses.create(

            model="gpt-5.6-luna",

            input=f"""
You are NEXORA, an intelligent multi-tool AI agent.

User request:
{command}

Classify the request as exactly one:

MEETING
ADD_TASK
SHOW_MEETING
SHOW_TASK
SEND_EMAIL
MEMORY
RAG
OTHER

Rules:

MEETING = schedule or book a meeting.

ADD_TASK = add a new task.

SHOW_MEETING = show saved meetings.

SHOW_TASK = show saved tasks.

SEND_EMAIL = send an email.

MEMORY = save or retrieve memories.

RAG = work with an uploaded PDF, DOCX or TXT document,
including searching, summarizing, analyzing, extracting
topics, insights or questions.

OTHER = anything else.

Return only the classification word.
"""
        )

        action = response.output_text.strip().upper()

        allowed = {
            "MEETING",
            "ADD_TASK",
            "SHOW_MEETING",
            "SHOW_TASK",
            "SEND_EMAIL",
            "MEMORY",
            "RAG",
            "OTHER"
        }

        if action not in allowed:
            raise ValueError(
                "Invalid AI classification"
            )

        print(
            "AI selected:",
            action
        )

        return {
            "action": action
        }

    except Exception:

        print(
            "⚠️ OpenAI unavailable. "
            "Using local fallback..."
        )

        action = local_classify(
            command
        )

        print(
            "Local fallback understood:",
            action
        )

        return {
            "action": action
        }


# =========================================================
# MEETING EXTRACTION
# =========================================================

def extract_meeting_locally(command):

    text = command.lower()

    person = "Unknown"

    match = re.search(
        r"(?:with|for)\s+([a-zA-Z]+)",
        text
    )

    if match:

        person = match.group(1).strip()

        person = person.capitalize()

    today = datetime.now().date()

    if "today" in text:

        date = today

    elif "tomorrow" in text:

        date = today + timedelta(days=1)

    else:

        match = re.search(
            r"\b(20\d{2}-\d{2}-\d{2})\b",
            text
        )

        if match:

            date = datetime.strptime(
                match.group(1),
                "%Y-%m-%d"
            ).date()

        else:

            date = today + timedelta(days=1)

    time = "10:00"

    match = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b",
        text
    )

    if match:

        hour = int(match.group(1))

        minute = (
            int(match.group(2))
            if match.group(2)
            else 0
        )

        period = match.group(3)

        if period == "pm" and hour != 12:
            hour += 12

        if period == "am" and hour == 12:
            hour = 0

        time = f"{hour:02d}:{minute:02d}"

    return (
        person,
        date.strftime("%Y-%m-%d"),
        time
    )


# =========================================================
# MEETING NODE
# =========================================================

def meeting_node(state):

    print(
        "Meeting tool selected."
    )

    command = state["command"]

    person, date, time = (
        extract_meeting_locally(command)
    )

    print("\nMeeting Details:")
    print("Person:", person)
    print("Date:", date)
    print("Time:", time)

    allowed = ask_permission(
        f"Create a Google Calendar meeting with {person}",
        state.get(
            "permission_granted",
            False
        )
    )

    if not allowed:

        if os.getenv("NEXORA_UI") == "1":

            return {
                "result":
                    "PERMISSION_REQUIRED"
            }

        return {
            "result":
                "Meeting cancelled by user."
        }

    print(
        "Permission granted."
    )

    tools.save_meeting(
        person,
        date,
        time
    )

    link = tools.create_calendar_event(
        person,
        date,
        time
    )

    print(
        "\nGoogle Calendar Event Created!"
    )

    print(
        "Calendar Link:",
        link
    )

    return {
        "result":
            f"Meeting created successfully!\n{link}"
    }


# =========================================================
# TASK EXTRACTION
# =========================================================

def extract_task_locally(command):

    text = command.strip()

    patterns = [

        r"add (?:a )?task (?:to )?(.*)",

        r"create (?:a )?task (?:to )?(.*)",

        r"new task[: ]+(.*)",

        r"remind me to (.*)"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            task = match.group(1).strip()

            if task:
                return task

    return text


# =========================================================
# TASK NODE
# =========================================================

def task_node(state):

    print(
        "Task tool selected."
    )

    task = extract_task_locally(
        state["command"]
    )

    tools.add_task(
        task
    )

    print(
        "\nTask Added!"
    )

    print(
        "Task:",
        task
    )

    return {
        "result":
            f"Task Added: {task}"
    }


# =========================================================
# SHOW TASK
# =========================================================

def show_task_node(state):

    print(
        "Show Task tool selected."
    )

    tasks = tools.get_tasks()

    if not tasks:

        return {
            "result":
                "No tasks found."
        }

    output = [
        "Your Tasks:"
    ]

    for task in tasks:

        output.append(
            f"{task[0]}. {task[1]}"
        )

    return {
        "result":
            "\n".join(output)
    }


# =========================================================
# SHOW MEETINGS
# =========================================================

def show_meeting_node(state):

    print(
        "Show Meeting tool selected."
    )

    meetings = tools.get_meetings()

    if not meetings:

        return {
            "result":
                "No meetings found."
        }

    output = [
        "Your Meetings:"
    ]

    for meeting in meetings:

        output.append(
            f"{meeting[0]}. "
            f"{meeting[1]} | "
            f"{meeting[2]} | "
            f"{meeting[3]}"
        )

    return {
        "result":
            "\n".join(output)
    }


# =========================================================
# MEMORY NODE
# =========================================================

def memory_node(state):

    print(
        "Memory tool selected."
    )

    command = state["command"]

    text = command.lower()

    retrieve_phrases = [

        "do you remember",
        "what do you remember",
        "what did i tell you",
        "what did i say",
        "show my memory",
        "show memories",
        "my memories",
        "retrieve memory",
        "retrieve memories",
        "recall"
    ]

    is_retrieve = any(
        phrase in text
        for phrase in retrieve_phrases
    )

    if is_retrieve:

        memories = tools.get_memories()

        if not memories:

            return {
                "result":
                    "No memories found."
            }

        output = [
            "NEXORA Memory:"
        ]

        for memory in memories:

            output.append(
                f"• {memory}"
            )

        return {
            "result":
                "\n".join(output)
        }

    information = command

    remove_phrases = [

        "remember this",
        "remember that",
        "remember:",
        "save this",
        "save that",
        "store this",
        "store that"
    ]

    for phrase in remove_phrases:

        if text.startswith(phrase):

            information = command[
                len(phrase):
            ].strip()

            break

    if not information:

        return {
            "result":
                "Nothing to remember."
        }

    tools.save_memory(
        information
    )

    return {
        "result":
            f"Memory saved: {information}"
    }


# =========================================================
# RAG NODE
# =========================================================

def rag_node(state):

    print(
        "RAG / Document tool selected."
    )

    command = state["command"]

    file_path = state.get(
        "file_path"
    )

    if not file_path:

        return {
            "result":
                "Please upload a PDF, DOCX or TXT file first."
        }

    if not os.path.exists(
        file_path
    ):

        return {
            "result":
                "Uploaded document was not found."
        }

    try:

        result = tools.ask_document(
            command,
            file_path
        )

        return {
            "result": result
        }

    except Exception as e:

        print(
            "RAG error:",
            e
        )

        return {
            "result":
                "Unable to analyze the uploaded document."
        }


# =========================================================
# EMAIL EXTRACTION
# =========================================================

def extract_email_locally(command):

    match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        command
    )

    if match:
        recipient = match.group(0)
    else:
        recipient = ""

    message = command

    patterns = [

        r"send an email to\s+[\w\.-]+@[\w\.-]+\.\w+",

        r"send email to\s+[\w\.-]+@[\w\.-]+\.\w+",

        r"send a mail to\s+[\w\.-]+@[\w\.-]+\.\w+",

        r"send mail to\s+[\w\.-]+@[\w\.-]+\.\w+"
    ]

    for pattern in patterns:

        message = re.sub(
            pattern,
            "",
            message,
            flags=re.IGNORECASE
        )

    message = re.sub(
        r"^(saying|message|that)\s*",
        "",
        message,
        flags=re.IGNORECASE
    )

    message = message.strip()

    if not message:

        message = "Hello from NEXORA."

    return (
        recipient,
        message
    )


# =========================================================
# EMAIL NODE
# =========================================================

def email_node(state):

    print(
        "Email tool selected."
    )

    command = state["command"]

    file_path = state.get(
        "file_path"
    )

    recipient, message = (
        extract_email_locally(command)
    )

    if not recipient:

        return {
            "result":
                "Please provide a valid email address."
        }

    print(
        "\nEmail Details:"
    )

    print(
        "Recipient:",
        recipient
    )

    print(
        "Message:",
        message
    )

    # Attachment
    if (
        file_path
        and os.path.exists(file_path)
    ):

        print(
            "Attachment:",
            os.path.basename(file_path)
        )

        permission_text = (
            f"Send an email to {recipient} "
            f"with attachment "
            f"{os.path.basename(file_path)}"
        )

    else:

        file_path = None

        permission_text = (
            f"Send an email to {recipient}"
        )

    # IMPORTANT:
    # Browser Allow sends permission_granted=True
    allowed = ask_permission(
        permission_text,
        state.get(
            "permission_granted",
            False
        )
    )

    if not allowed:

        if os.getenv("NEXORA_UI") == "1":

            return {
                "result":
                    "PERMISSION_REQUIRED"
            }

        return {
            "result":
                "Email cancelled by user."
        }

    print(
        "Permission granted."
    )

    try:

        result = tools.send_email(
            recipient,
            message,
            file_path
        )

        print(
            "\n" + result
        )

        return {
            "result": result
        }

    except Exception as e:

        print(
            "Email error:",
            e
        )

        return {
            "result":
                f"Email could not be sent: {e}"
        }


# =========================================================
# OTHER
# =========================================================

def other_node(state):

    return {
        "result":
            "I couldn't identify a matching NEXORA tool."
    }


# =========================================================
# ROUTING
# =========================================================

def route_request(state):

    action = state["action"]

    if action == "MEETING":
        return "meeting"

    if action == "ADD_TASK":
        return "task"

    if action == "SHOW_TASK":
        return "show_task"

    if action == "SHOW_MEETING":
        return "show_meeting"

    if action == "MEMORY":
        return "memory"

    if action == "RAG":
        return "rag"

    if action == "SEND_EMAIL":
        return "email"

    return "other"


# =========================================================
# LANGGRAPH
# =========================================================

graph = StateGraph(
    AgentState
)


graph.add_node(
    "analyze",
    analyze_request
)

graph.add_node(
    "meeting",
    meeting_node
)

graph.add_node(
    "task",
    task_node
)

graph.add_node(
    "show_task",
    show_task_node
)

graph.add_node(
    "show_meeting",
    show_meeting_node
)

graph.add_node(
    "memory",
    memory_node
)

graph.add_node(
    "rag",
    rag_node
)

graph.add_node(
    "email",
    email_node
)

graph.add_node(
    "other",
    other_node
)


graph.add_edge(
    START,
    "analyze"
)


graph.add_conditional_edges(

    "analyze",

    route_request,

    {
        "meeting": "meeting",
        "task": "task",
        "show_task": "show_task",
        "show_meeting": "show_meeting",
        "memory": "memory",
        "rag": "rag",
        "email": "email",
        "other": "other"
    }
)


graph.add_edge(
    "meeting",
    END
)

graph.add_edge(
    "task",
    END
)

graph.add_edge(
    "show_task",
    END
)

graph.add_edge(
    "show_meeting",
    END
)

graph.add_edge(
    "memory",
    END
)

graph.add_edge(
    "rag",
    END
)

graph.add_edge(
    "email",
    END
)

graph.add_edge(
    "other",
    END
)


app = graph.compile()


# =========================================================
# TERMINAL TEST
# =========================================================

if __name__ == "__main__":

    result = app.invoke({

        "command":
            "show my tasks",

        "action":
            "",

        "result":
            "",

        "file_path":
            "",

        "permission_granted":
            False
    })

    print(
        "\nFinal Result:"
    )

    print(
        result["result"]
    )