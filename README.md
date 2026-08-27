**Multimodal RAG Assistant**
A full-stack, production-ready Retrieval-Augmented Generation (RAG) application that bypasses traditional text-extraction limits by using multimodal vision models to read and reason over PDF documents.
Live Demo: https://multimodal-agentic-rag-3-hoe1.onrender.com/
(Note: Hosted on a free-tier instance, so please allow a few seconds for the server to spin up on initial request.)

**System Architecture & Workflow**
Traditional text-based RAG pipelines often break when encountering complex layouts, multi-column text, data tables, or charts. This application solves that by converting PDFs into high-resolution images and letting an intelligent agent visually inspect them.

<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/8fc29ac1-76c0-4f7e-b267-dcaffa9b439c" />

Core Features
•	Multimodal Visual RAG: Rasterizes PDF pages into images so the model can visually interpret layout, formatting, and tables.
•	Dynamic Tool-Use Agent: Utilizes custom Python function bindings (list_available_pages and query_pdf_with_gemini) to give the LLM workspace navigation capabilities.
•	Bring Your Own Key (BYOK) Security: Client-side API keys are passed securely via custom headers (X-Gemini-API-Key) and injected into runtime closures, preventing hardcoded secrets on the server.
•	Resilient Error Handling: Includes built-in exponential backoff retry logic to gracefully handle API rate limits (429) and server busy states (503).
•	Cloud Deployment Ready: Fully containerized via Docker and deployed on Render.
Tech Stack
•	Backend: FastAPI, Uvicorn, PyMuPDF (fitz), Python-Dotenv, Pydantic
•	AI / ML: Google GenAI SDK (google-genai), Pillow (PIL)
•	Frontend: Vanilla HTML5, CSS3, Modern JavaScript (Fetch API, LocalStorage)
•	Infrastructure: Docker (python:3.12-slim), Render

**Project Structure**
├── backend/
│   ├── main.py             # FastAPI entrypoint, routing, session mgmt & dynamic agent creation
│   └── services/
│       ├── parser.py       # Handles PDF-to-image conversion using PyMuPDF
│       └── rag_engine.py   # Core agent logic, tools definition, and Gemini API bindings
├── frontend/
│   ├── index.html          # UI shell containing API key bar, upload panel, and chat interface
│   ├── style.css           # Modern dark-mode styling
│   └── script.js           # Client-side state handling, file uploads, and chat loop
├── requirements.txt        # Python package dependencies
└── Dockerfile              # Container configuration file

