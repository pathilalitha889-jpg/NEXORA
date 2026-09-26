
import os
from datetime import datetime
from typing import TypedDict, Optional

from dotenv import load_dotenv
from openai import OpenAI
from langgraph.graph import StateGraph, START, END

import tools


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

try:
    client = OpenAI()
except Exception:
    client = None


# =========================================================
# AGENT STATE
# =========================================================

class AgentState(TypedDict, total=False):
    command: str
    action: str
    result: str
    file_path: Optional[str]
    permission_granted: bool
    google_access_token: Optional[str]


# =========================================================
# HELPERS
# =========================================================

def use_ai() -> bool:
    return client is not None


def local_classify(command: str) -> str:

    text = command.lower().strip()

    if any(word in text for word in [
        "schedule", "meeting", "appointment", "book a meeting"
    ]):
        return "MEETING"

    if any(word in text for word in [
        "add a task", "add task", "create a task", "new task",
        "remind me to"
    ]):
        return "ADD_TASK"

    if any(word in text for word in [
        "show my tasks", "show tasks", "list my tasks",
        "what are my tasks"
    ]):
        return "SHOW_TASK"

    if any(word in text for word in [
        "show my meetings", "show meetings", "list my meetings",
        "what meetings do i have"
    ]):
        return "SHOW_MEETING"

    if any(word in text for word in [
        "send an email", "send email", "email",
        "mail"
    ]):
        return "SEND_EMAIL"

    if any(word in text for word in [
        "remember", "do you remember", "what do you remember",
        "save this memory"
    ]):
        return "MEMORY"

    if any(word in text for word in [
        "document", "pdf", "docx", "jdbc", "rag",
        "uploaded file"
    ]):
        return "RAG"

    return "OTHER"


def ask_permission(action: str, state: AgentState) -> bool:

    # Web UI explicitly grants permission
    if state.get("permission_granted", False):
        return True

    # Terminal mode
    if os.getenv("NEXORA_UI") != "1":

        print(f"\nPermission required for: {action}")

        choice = input(
            "Do you want to allow this action? (yes/no): "
        )

        return choice.lower().strip() == "yes"

    return False


# =========================================================
# ANALYZE REQUEST
# =========================================================
def analyze_request(state):

    command = state.get(
        "command",
        ""
    ).strip()

    if not command:

        return {
            "action": "OTHER",
            "result": "Please enter a command."
        }

    print("\nAnalyzing request...")

    prompt = f"""
You are NEXORA's intelligent intent router.

Your job is to understand the USER'S MEANING and select the correct tool.

IMPORTANT:
- Do NOT depend on exact keywords.
- Understand natural language, paraphrasing, slang, short sentences,
  polite requests, indirect requests, and different sentence structures.
- The same intent can be expressed in many different ways.
- Focus on what the user wants NEXORA to DO.
- Do not return OTHER when the request clearly matches one of the supported tools.

Choose exactly ONE:

MEETING
ADD_TASK
SHOW_MEETING
SHOW_TASK
SEND_EMAIL
MEMORY
RAG
OTHER

INTENT DEFINITIONS:

MEETING:
The user wants to schedule, arrange, book, set, create,
plan, or organize a meeting or appointment.

ADD_TASK:
The user wants to add something to their task list,
create a task, remember something as a task,
track something they need to do, or asks NEXORA to keep
something as a future task.

SHOW_MEETING:
The user wants to see, list, check, or know their meetings.

SHOW_TASK:
The user wants to see, list, check, or know their tasks.

SEND_EMAIL:
The user wants NEXORA to send, compose, write, or deliver
an email/message through Gmail.

MEMORY:
The user wants NEXORA to remember/save/store personal information,
OR the user is asking what NEXORA remembers about them.

RAG:
The user is asking a question that should be answered using
the uploaded PDF/document.

OTHER:
Only use this when the request does not match any supported tool.

EXAMPLES:

"I have to study Java tomorrow"
-> ADD_TASK

"Make sure I prepare Java tomorrow"
-> ADD_TASK

"I need to finish my assignment"
-> ADD_TASK

"Could you put this on my task list?"
-> ADD_TASK

"What do I need to do?"
-> SHOW_TASK

"What have I saved as tasks?"
-> SHOW_TASK

"I have a meeting with Ravi tomorrow at 10"
-> MEETING

"Can you arrange a meeting with Ravi for tomorrow?"
-> MEETING

"Put Ravi on my calendar for 10 AM tomorrow"
-> MEETING

"What meetings do I have?"
-> SHOW_MEETING

"Do I have anything scheduled?"
-> SHOW_MEETING

"Tell Ravi that I will be late"
-> SEND_EMAIL

"Please send Ravi an email saying I am late"
-> SEND_EMAIL

"Can you mail this person?"
-> SEND_EMAIL

"Keep in mind that I am learning Java"
-> MEMORY

"Please remember my interview is Monday"
-> MEMORY

"What do you remember about me?"
-> MEMORY

"Do you know what I am learning?"
-> MEMORY

"What did I ask you to remember?"
-> MEMORY

"What does the uploaded document say about JDBC?"
-> RAG

"Explain batch updates from the PDF"
-> RAG

"Can you answer this from my document?"
-> RAG

USER REQUEST:
{command}

Return ONLY the action name.
"""

    try:

        response = client.responses.create(
            model="gpt-5.6-luna",
            input=prompt
        )

        action = (
            response.output_text
            .strip()
            .upper()
        )

        valid_actions = {
            "MEETING",
            "ADD_TASK",
            "SHOW_MEETING",
            "SHOW_TASK",
            "SEND_EMAIL",
            "MEMORY",
            "RAG",
            "OTHER"
        }

        if action not in valid_actions:

            # Retry once with a stricter classification request
            retry = client.responses.create(
                model="gpt-5.6-luna",
                input=f"""
Classify this user request by INTENT.

Possible actions:
MEETING
ADD_TASK
SHOW_MEETING
SHOW_TASK
SEND_EMAIL
MEMORY
RAG
OTHER

Understand the meaning, not exact words.

USER REQUEST:
{command}

Return ONLY one action name.
"""
            )

            action = (
                retry.output_text
                .strip()
                .upper()
            )

        if action not in valid_actions:

            action = "OTHER"

        print(
            "NEXORA understood:",
            action
        )

        return {
            "action": action
        }

    except Exception as e:

        print(
            "AI classification error:",
            e
        )

        return {
            "action": "OTHER",
            "result": "Unable to understand the request."
        }

# =========================================================
# MEETING NODE
# =========================================================

def meeting_node(state: AgentState):

    command = state.get("command", "").strip()

    person = ""
    date = ""
    time = ""

    # -----------------------------------------
    # AI extraction
    # -----------------------------------------

    if use_ai():

        try:

            details = client.responses.create(

                model="gpt-5.6-luna",

                input=f"""
Today is {datetime.now().strftime('%Y-%m-%d')}.

Extract the meeting details from this request:

{command}

Convert relative dates such as tomorrow, today and next Monday
into YYYY-MM-DD.

Convert time into 24-hour HH:MM format.

Return exactly:

PERSON: name
DATE: YYYY-MM-DD
TIME: HH:MM
"""
            )

            lines = details.output_text.strip().splitlines()

            for line in lines:

                upper_line = line.upper()

                if upper_line.startswith("PERSON:"):
                    person = line.split(":", 1)[1].strip()

                elif upper_line.startswith("DATE:"):
                    date = line.split(":", 1)[1].strip()

                elif upper_line.startswith("TIME:"):
                    time = line.split(":", 1)[1].strip()

        except Exception as e:

            print("Meeting AI extraction failed:", e)

    # -----------------------------------------
    # Basic local fallback extraction
    # -----------------------------------------

    if not person:

        words = command.split()

        if "with" in [w.lower() for w in words]:

            try:
                index = [
                    w.lower() for w in words
                ].index("with")

                if index + 1 < len(words):
                    person = words[index + 1]

            except Exception:
                pass

    if not person:
        person = "Unknown"

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    if not time:
        time = "10:00"

    print("\nMeeting Details:")
    print("Person:", person)
    print("Date:", date)
    print("Time:", time)

    # -----------------------------------------
    # Permission
    # -----------------------------------------

    allowed = ask_permission(
        f"Create a Google Calendar meeting with {person}",
        state
    )

    if not allowed:

        if os.getenv("NEXORA_UI") == "1":

            return {
                "result": "PERMISSION_REQUIRED"
            }

        return {
            "result": "Meeting cancelled by user."
        }

    print("Permission granted.")

    try:

        tools.save_meeting(
            person,
            date,
            time
        )

        link = tools.create_calendar_event(
            person,
            date,
            time,
            state.get("google_access_token")
        )

        print("\nGoogle Calendar Event Created!")
        print("Calendar Link:", link)

        return {
            "result": link
        }

    except Exception as e:

        print("Calendar error:", e)

        return {
            "result": f"Calendar error: {e}"
        }


# =========================================================
# ADD TASK NODE
# =========================================================

def task_node(state: AgentState):

    command = state.get("command", "").strip()

    task = command

    if use_ai():

        try:

            task_response = client.responses.create(

                model="gpt-5.6-luna",

                input=f"""
Extract only the task from this request:

{command}

Return only the task text.
"""
            )

            task = task_response.output_text.strip()

        except Exception as e:

            print("Task AI extraction failed:", e)

    tools.add_task(task)

    print("\nTask Added!")
    print("Task:", task)

    return {
        "result": f"Task Added: {task}"
    }


# =========================================================
# SHOW TASK NODE
# =========================================================

def show_task_node(state: AgentState):

    tasks = tools.get_tasks()

    print("\nYour Tasks:")

    if tasks:

        for task in tasks:
            print(task)

    else:

        print("No tasks found.")

    return {
        "result": str(tasks)
    }


# =========================================================
# SHOW MEETING NODE
# =========================================================

def show_meeting_node(state: AgentState):

    meetings = tools.get_meetings()

    print("\nYour Meetings:")

    if meetings:

        for meeting in meetings:
            print(meeting)

    else:

        print("No meetings found.")

    return {
        "result": str(meetings)
    }


# =========================================================
# MEMORY NODE
# =========================================================

def memory_node(state: AgentState):

    command = state.get("command", "").strip()

    memory_action = ""

    if use_ai():

        try:

            memory_type = client.responses.create(

                model="gpt-5.6-luna",

                input=f"""
Determine whether the user wants to SAVE or RETRIEVE memory.

User request:
{command}

Return exactly one:

SAVE
RETRIEVE
"""
            )

            memory_action = (
                memory_type.output_text
                .strip()
                .upper()
            )

        except Exception as e:

            print("Memory AI classification failed:", e)

    # Local fallback
    if memory_action not in ["SAVE", "RETRIEVE"]:

        text = command.lower()

        if any(word in text for word in [
            "remember",
            "save this memory"
        ]):

            memory_action = "SAVE"

        else:

            memory_action = "RETRIEVE"

    # -----------------------------------------
    # SAVE
    # -----------------------------------------

    if memory_action == "SAVE":

        information = command

        if use_ai():

            try:

                memory_response = client.responses.create(

                    model="gpt-5.6-luna",

                    input=f"""
Extract the important information the user wants NEXORA
to remember.

User request:
{command}

Return only the information to remember.
"""
                )

                information = memory_response.output_text.strip()

            except Exception as e:

                print("Memory extraction failed:", e)

        tools.save_memory(information)

        return {
            "result": f"Memory saved: {information}"
        }

    # -----------------------------------------
    # RETRIEVE
    # -----------------------------------------

    memories = tools.get_memories()

    if memories:

        return {
            "result": str(memories)
        }

    return {
        "result": "No memories found."
    }


# =========================================================
# RAG NODE
# =========================================================

def rag_node(state: AgentState):

    command = state.get("command", "").strip()

    try:

        relevant_text = tools.search_document(command)

    except Exception as e:

        print("Document search error:", e)

        return {
            "result": f"Document search error: {e}"
        }

    if not relevant_text:

        return {
            "result": "No relevant information found."
        }

    if not use_ai():

        return {
            "result": relevant_text
        }

    try:

        response = client.responses.create(

            model="gpt-5.6-luna",

            input=f"""
You are NEXORA.

Answer the user's question using the document content below.

DOCUMENT CONTENT:
{relevant_text}

USER QUESTION:
{command}

Give a clear and direct answer.
"""
        )

        answer = response.output_text.strip()

        return {
            "result": answer
        }

    except Exception as e:

        print("RAG AI error:", e)

        return {
            "result": relevant_text
        }


# =========================================================
# EMAIL NODE
# =========================================================

def email_node(state: AgentState):

    command = state.get("command", "").strip()

    recipient = ""
    message = ""

    # -----------------------------------------
    # AI extraction
    # -----------------------------------------

    if use_ai():

        try:

            details = client.responses.create(

                model="gpt-5.6-luna",

                input=f"""
Extract the email details from this request:

{command}

Return exactly:

RECIPIENT: email address
MESSAGE: message text
"""
            )

            lines = details.output_text.strip().splitlines()

            for line in lines:

                upper_line = line.upper()

                if upper_line.startswith("RECIPIENT:"):

                    recipient = (
                        line.split(":", 1)[1]
                        .strip()
                    )

                elif upper_line.startswith("MESSAGE:"):

                    message = (
                        line.split(":", 1)[1]
                        .strip()
                    )

        except Exception as e:

            print("Email AI extraction failed:", e)

    # -----------------------------------------
    # Local fallback extraction
    # -----------------------------------------

    if not recipient:

        parts = command.split()

        for part in parts:

            if "@" in part and "." in part:

                recipient = (
                    part
                    .strip(".,!?")
                )

                break

    if not message:

        lower_command = command.lower()

        if "saying" in lower_command:

            message = command.split(
                "saying",
                1
            )[1].strip()

        elif "saying" in command:

            message = command.split(
                "Saying",
                1
            )[1].strip()

        else:

            message = "Hello from NEXORA."

    # -----------------------------------------
    # Validation
    # -----------------------------------------

    if not recipient:

        return {
            "result": "Email address is missing."
        }

    if "@" not in recipient or "." not in recipient:

        return {
            "result": "Invalid email address."
        }

    if not message:

        return {
            "result": "Email message is missing."
        }

    print("\nEmail Details:")
    print("Recipient:", recipient)
    print("Message:", message)

    # -----------------------------------------
    # Permission
    # -----------------------------------------

    allowed = ask_permission(
        f"Send an email to {recipient}",
        state
    )

    if not allowed:

        if os.getenv("NEXORA_UI") == "1":

            return {
                "result": "PERMISSION_REQUIRED"
            }

        return {
            "result": "Email cancelled by user."
        }

    print("Permission granted.")

    try:

        result = tools.send_email(
            recipient,
            message,
            state.get("file_path"),
            state.get("google_access_token")
        )

        print("\n" + result)

        return {
            "result": result
        }

    except Exception as e:

        print("Email error:", e)

        return {
            "result": f"Email could not be sent: {e}"
        }


# =========================================================
# OTHER NODE
# =========================================================

def other_node(state: AgentState):

    return {
        "result": "Unknown request. Please try another command."
    }


# =========================================================
# ROUTING
# =========================================================

def route_request(state: AgentState):

    action = state.get("action", "OTHER")

    if action == "MEETING":
        return "meeting"

    elif action == "ADD_TASK":
        return "task"

    elif action == "SHOW_TASK":
        return "show_task"

    elif action == "SHOW_MEETING":
        return "show_meeting"

    elif action == "MEMORY":
        return "memory"

    elif action == "RAG":
        return "rag"

    elif action == "SEND_EMAIL":
        return "email"

    return "other"


# =========================================================
# LANGGRAPH
# =========================================================

graph = StateGraph(AgentState)

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
# TEST
# =========================================================

if __name__ == "__main__":

    result = app.invoke({

        "command": "show my tasks",

        "action": "",

        "result": "",

        "file_path": None,

        "permission_granted": False,

        "google_access_token": None
    })

    print("\nFinal Result:")
    print(
        result.get(
            "result",
            "No result."
        )
    )

