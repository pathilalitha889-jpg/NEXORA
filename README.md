# 🤖 NEXORA — Intelligent Multi-Tool AI Agent

NEXORA is an intelligent multi-tool AI agent that understands natural-language requests and automatically routes them to the appropriate tool.

It combines task management, Google Calendar, Gmail, conversation memory, document intelligence, permission control, LangGraph-based workflow routing, and a Streamlit web interface into a single application.

---

## 🚀 Features

* 📅 **Smart Scheduling** — Create Google Calendar meetings using natural-language commands.
* 📧 **Email Automation** — Send Gmail messages with file attachments.
* ✅ **Task Management** — Add and retrieve tasks using natural-language commands.
* 🧠 **Conversation Memory** — Store and retrieve useful information from previous interactions.
* 📄 **Document Intelligence (RAG)** — Search and analyze PDF, DOCX, and TXT documents.
* 🔐 **Permission Control** — Request user confirmation before sensitive actions.
* 🔀 **LangGraph Agent** — Route requests through specialized processing nodes.
* 💻 **Professional Web UI** — Interactive Streamlit interface.
* 🔐 **Google Login** — Securely sign in to NEXORA using Google authentication.
* ⚡ **Local Document Analysis** — Analyze uploaded PDF, DOCX, and TXT files without requiring the OpenAI API.
* 🗄️ **SQLite Database** — Store tasks, meetings, and memories locally.
* 🛡️ **Local Fallback** — * Analyze uploaded PDF, DOCX, and TXT files without requiring the OpenAI API.

---

## 🏗️ Architecture

```text
                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │     NEXORA      │
                  │   AI Agent      │
                  └────────┬────────┘
                           │
                           ▼
                   Request Analysis
                           │
                           ▼
                    Action Routing
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       Calendar          Email            Tasks
          │                │                │
          └────────────────┼────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
       Memory             RAG           Database
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    Final Response
```

---

## 🛠️ Technology Stack

| Technology          | Purpose                                |
| ------------------- | -------------------------------------- |
| Python              | Core application logic                 |
| OpenAI API          | Natural-language request understanding |
| LangGraph           | Agent workflow and request routing     |
| SQLite              | Local data storage                     |
| Gmail SMTP          | Email automation                       |
| Google Calendar API | Meeting creation                       |
| Streamlit           | Web interface                          |
| python-docx         | DOCX document processing               |
| PyPDF               | PDF document processing                |

---

## 📁 Project Structure

```text
NEXORA/
│
├── agent.py
├── tools.py
├── web_ui.py
├── main.py
├── ai_test.py
├── calendar_test.py
│
├── questions.docx
├── README.md
├── .gitignore
│
├── .env
├── credentials.json
├── token.json
├── nexora.db
│
└── uploads/
```

### Important

The following files contain private or local data and must **not** be uploaded to GitHub:

```text
.env
credentials.json
token.json
nexora.db
uploads/
```

These files are protected through `.gitignore`.

---

## ⚙️ How NEXORA Works

The core workflow is:

```text
User Request
     │
     ▼
Request Analysis
     │
     ▼
Action Classification
     │
     ▼
LangGraph Routing
     │
     ├── Calendar
     ├── Email
     ├── Tasks
     ├── Memory
     └── RAG
     │
     ▼
Permission Check
     │
     ▼
Tool Execution
     │
     ▼
Final Response
```

NEXORA first attempts to use the OpenAI API for natural-language understanding.

When the OpenAI API is unavailable, the application can use a local rule-based fallback for supported commands such as email, meetings, tasks, memory, and document operations.

---

## 📅 Google Calendar

NEXORA can create real Google Calendar events from natural-language commands.

Example:

```text
Schedule a meeting with Ravi tomorrow at 10 AM
```

The request is processed as:

```text
User Request
     ↓
Meeting Detection
     ↓
Meeting Details Extraction
     ↓
Permission Request
     ↓
User selects Allow / Deny
     ↓
Google Calendar Event
```

A Google Calendar OAuth configuration is required for calendar integration.

---

## 📧 Gmail Email Automation

NEXORA can send Gmail messages and attachments through Gmail SMTP.

Example:

```text
Send an email to someone@example.com saying Hello from NEXORA
```

File attachments are also supported.

Example:

```text
Send an email to someone@example.com saying Here is my offer letter
```

The user can upload a document through the Streamlit interface and use it as an attachment.

---

## 🔐 Permission Control

Sensitive operations require user permission before execution.

Currently, permission control is used for:

* 📧 Sending emails
* 📅 Creating Google Calendar events

Example flow:

```text
User Request
     ↓
NEXORA understands the request
     ↓
Permission required
     ↓
┌───────────────┐
│ Allow / Deny  │
└───────────────┘
     ↓
Action executed
or
Action cancelled
```

This prevents sensitive actions from being performed without explicit user confirmation.

---

## ✅ Task Management

NEXORA supports natural-language task management using SQLite.

Example:

```text
Add a task to study Java
```

Tasks are stored in the local SQLite database.

Users can also retrieve their existing tasks using natural-language commands.

Example:

```text
Show my tasks
```

---

## 🧠 Conversation Memory

NEXORA provides a simple memory system for storing and retrieving useful information.

Example:

```text
Remember that I am learning Java
```

Later:

```text
Do you remember what I am learning?
```

Stored memories are saved in the SQLite database.

The memory system supports both:

```text
Save Memory
```

and

```text
Retrieve Memory
```

---

## 📄 Document Intelligence (RAG)

NEXORA includes local document processing and retrieval functionality.

Supported formats:

```text
PDF
DOCX
TXT
```

The document system can:

* Extract document text
* Search relevant sections
* Generate a local extractive summary
* Identify key topics
* Identify key insights
* Generate possible questions
* Retrieve relevant information from the uploaded document

Example:

```text
What does the uploaded document say about JDBC Batch Updates?
```

The system searches the uploaded document and returns the most relevant information.

### Document Analysis

For broader requests such as:

```text
Analyze this document
```

or:

```text
Give me a summary
```

NEXORA can provide:

```text
📄 Document Analysis

File information
     ↓
📝 Summary
     ↓
🔑 Key Topics
     ↓
💡 Key Insights
     ↓
❓ Possible Questions
```

The document processing component works locally and does not require Ollama.

---

## 🔀 LangGraph Agent

LangGraph is used to organize NEXORA's workflow into specialized processing nodes.

The agent can route requests to different nodes such as:

```text
Request
   ↓
Analyze
   ↓
Route
   ├── ADD_TASK
   ├── SHOW_TASK
   ├── MEETING
   ├── SHOW_MEETING
   ├── SEND_EMAIL
   ├── MEMORY
   ├── RAG
   └── OTHER
```

This modular design makes the system easier to extend with additional tools.

---

## 🗄️ SQLite Database

NEXORA uses SQLite for local persistent storage.

The database currently stores:

```text
Tasks
Meetings
Memories
```

The database file is local to the project and is intentionally excluded from GitHub.

---

## 💻 Web Interface

NEXORA includes a Streamlit-based web interface.

The interface provides:

* 🤖 NEXORA dashboard
* 📅 Calendar tool
* 📧 Gmail tool
* ✅ Task management
* 🧠 Memory
* 📚 Document upload and RAG
* 🔐 Allow / Deny permission controls
* 💬 Natural-language command input

Run the application with:

```powershell
python -m streamlit run web_ui.py
```

The Streamlit interface will open in the browser.

---

## 💬 Example Commands

### 📅 Calendar

```text
Schedule a meeting with Ravi tomorrow at 10 AM
```

### ✅ Tasks

```text
Add a task to study Java
```

```text
Show my tasks
```

### 📧 Email

```text
Send an email to someone@example.com saying Hello from NEXORA
```

### 🧠 Memory

```text
Remember that I am learning Java
```

```text
Do you remember what I am learning?
```

### 📄 Document Search

```text
What does the uploaded document say about JDBC?
```

### 📊 Document Analysis

```text
Analyze the uploaded document
```

---

## 🔑 Environment Variables

NEXORA uses environment variables for private configuration.

Create a `.env` file in the project directory.

Example structure:

```text
OPENAI_API_KEY=your_api_key
EMAIL_ADDRESS=your_email
EMAIL_APP_PASSWORD=your_app_password
```

### Security

Never upload the following to GitHub:

```text
.env
credentials.json
token.json
API keys
Email passwords
OAuth secrets
```

The project `.gitignore` is configured to exclude these files.

---

## 📦 Installation

Install the required Python packages:

```powershell
pip install openai python-dotenv
```

Install Google Calendar dependencies:

```powershell
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Install document processing dependencies:

```powershell
pip install pypdf python-docx
```

Install LangGraph:

```powershell
pip install langgraph
```

Install Streamlit:

```powershell
pip install streamlit
```

---

## ▶️ Running NEXORA

### Run the terminal version

```powershell
python main.py
```

### Run the web version

```powershell
python -m streamlit run web_ui.py
```

---

## 🔧 Configuration

### Google Calendar

Google Calendar integration requires:

1. A Google Cloud project
2. Google Calendar API enabled
3. OAuth client credentials
4. `credentials.json`
5. OAuth authorization

After successful authorization, a local `token.json` file is created for future access.

---

### Gmail

Gmail email automation requires:

1. A Gmail account
2. Email address configured in `.env`
3. Gmail App Password configured in `.env`

The actual password should never be stored directly in source code.

---

## 🛡️ Error Handling and Fallback

NEXORA is designed to continue basic functionality even when external services are unavailable.

For example:

```text
OpenAI API available
        ↓
AI-based request classification
```

If the API is unavailable:

```text
OpenAI unavailable
        ↓
Local rule-based classification
        ↓
Supported NEXORA action
```

This allows core commands to remain usable without depending completely on the external AI service.

---

## 🎯 Project Objective

The objective of NEXORA is to demonstrate how an intelligent agent can:

* Understand natural-language commands
* Automatically select appropriate tools
* Route requests through an agent workflow
* Request permission for sensitive operations
* Execute real-world actions
* Store information persistently
* Search and analyze uploaded documents
* Integrate multiple services into one application

NEXORA combines these capabilities into a single intelligent multi-tool agent.

---

## 🚀 Future Enhancements

Possible future improvements include:

* More advanced document retrieval
* Improved natural-language extraction
* More external tool integrations
* Better conversation context handling
* More advanced agent planning
* Improved validation and error handling
* Cloud deployment
* Additional UI features

---

## 👩‍💻 Project

**NEXORA — Intelligent Multi-Tool AI Agent**

Built using:

```text
Python
OpenAI
LangGraph
SQLite
Gmail
Google Calendar
RAG
Streamlit
```

---

## 📌 License

This project was developed as an academic/college project for learning and demonstration purposes.
