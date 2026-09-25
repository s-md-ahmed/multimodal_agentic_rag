# Multimodal RAG Assistant

A full-stack, production-ready Retrieval-Augmented Generation (RAG) application that bypasses traditional text-extraction limits by using multimodal vision models to read and reason over PDF documents. 

**Live Demo:** [https://multimodal-agentic-rag-3-hoe1.onrender.com/](https://multimodal-agentic-rag-3-hoe1.onrender.com/)  
*(Note: Hosted on a free-tier instance, so please allow a few seconds for the server to spin up on an initial request.)*

---

## The Modern Document Reality (Why Multimodal RAG?)
Real-world enterprise documents (financial reports, research papers, architectural specs, and invoices) are fundamentally **visual**. Traditional RAG pipelines rely on text-extraction and vector chunking, which completely destroy spatial layouts, data tables, and charts. This project adopts a **multimodal-first architecture**—treating document pages as rich visual artifacts rather than flat text strings—allowing an autonomous agent to inspect layouts, read charts natively, and reason over documents the exact way a human engineer would.

---

## System Architecture & Workflow
Traditional text-based RAG pipelines often break when encountering complex layouts, multi-column text, data tables, or charts. This application solves that by converting PDFs into high-resolution images and letting an intelligent agent visually inspect them.
flowchart TD

subgraph group_client["Client Experience"]
  node_frontend_ui["Web Chat UI<br/>[index.html]"]
  node_frontend_flow["Client Chat Flow<br/>[script.js]"]
  node_answer["Grounded Answer<br/>[script.js]"]
end

subgraph group_api["API and Sessions"]
  node_fastapi["FastAPI Endpoints<br/>[main.py]"]
  node_session_registry[("Session Registry<br/>[main.py]")]
  node_session_files[("Session Files<br/>[main.py]")]
end

subgraph group_ingest["Document Ingestion"]
  node_pdf_parser["PDF Rasterizer<br/>[parser.py]"]
  node_page_images[("Page Images<br/>[parser.py]")]
  node_page_manifest[("Page Manifest<br/>[parser.py]")]
end

subgraph group_agent["Agent and Vision"]
  node_agent_factory["Chat Agent<br/>[rag_engine.py]"]
  node_manifest_tool["Page List Tool<br/>[rag_engine.py]"]
  node_vision_tool["Page Query Tool<br/>[rag_engine.py]"]
end

node_user(("PDF User"))
node_gemini["Gemini Models"]

node_user -->|"uses"| node_frontend_ui
node_frontend_ui -->|"loads scripts"| node_frontend_flow
node_frontend_flow -->|"uploads PDF"| node_fastapi
node_frontend_flow -->|"sends prompts"| node_fastapi
node_fastapi -->|"stores upload"| node_session_files
node_fastapi -->|"parses PDF"| node_pdf_parser
node_pdf_parser -->|"writes images"| node_page_images
node_pdf_parser -->|"writes manifest"| node_page_manifest
node_fastapi -->|"creates session"| node_session_registry
node_fastapi -->|"reads session"| node_session_registry
node_fastapi -->|"creates agent"| node_agent_factory
node_agent_factory -->|"creates chat"| node_gemini
node_gemini -->|"calls tool"| node_manifest_tool
node_manifest_tool -->|"reads manifest"| node_page_manifest
node_gemini -->|"calls tool"| node_vision_tool
node_vision_tool -->|"reads page"| node_page_images
node_vision_tool -->|"requests vision"| node_gemini
node_agent_factory -->|"returns answer"| node_fastapi
node_fastapi -->|"returns response"| node_frontend_flow
node_frontend_flow -->|"renders answer"| node_answer

click node_frontend_ui "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/frontend/index.html"
click node_frontend_flow "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/frontend/script.js"
click node_fastapi "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/main.py"
click node_session_registry "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/main.py"
click node_session_files "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/main.py"
click node_pdf_parser "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/services/parser.py"
click node_page_images "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/services/parser.py"
click node_page_manifest "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/services/parser.py"
click node_agent_factory "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/services/rag_engine.py"
click node_manifest_tool "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/services/rag_engine.py"
click node_vision_tool "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/backend/services/rag_engine.py"
click node_answer "https://github.com/s-md-ahmed/multimodal_agentic_rag/blob/main/frontend/script.js"

classDef toneNeutral fill:#f8fafc,stroke:#334155,stroke-width:1.5px,color:#0f172a
classDef toneBlue fill:#dbeafe,stroke:#2563eb,stroke-width:1.5px,color:#172554
classDef toneAmber fill:#fef3c7,stroke:#d97706,stroke-width:1.5px,color:#78350f
classDef toneMint fill:#dcfce7,stroke:#16a34a,stroke-width:1.5px,color:#14532d
classDef toneRose fill:#ffe4e6,stroke:#e11d48,stroke-width:1.5px,color:#881337
classDef toneIndigo fill:#e0e7ff,stroke:#4f46e5,stroke-width:1.5px,color:#312e81
classDef toneTeal fill:#ccfbf1,stroke:#0f766e,stroke-width:1.5px,color:#134e4a
class node_frontend_ui,node_frontend_flow,node_answer,node_user toneBlue
class node_fastapi,node_session_registry,node_session_files toneAmber
class node_pdf_parser,node_page_images,node_page_manifest toneMint
class node_agent_factory,node_manifest_tool,node_vision_tool toneRose
class node_gemini toneIndigo


### Why This Architecture? (Design Decisions & Trade-offs)
* **Why Visual RAG over Traditional Vector Embeddings?**
  * *The Problem:* Traditional RAG chops PDFs into raw text chunks and embeds them into a vector database. When documents contain data tables, charts, or multi-column layouts, text extraction scrambles the reading order, completely breaking table rows and visual data.
  * *The Solution:* Rasterizing pages into high-resolution JPEGs and letting a multimodal LLM read them directly preserves 100% of the spatial and structural layout.

* **Why a Structural JSON Manifest Instead of Blind Multi-Page Scanning?**
  * *The Problem:* Passing all page images of a PDF to an LLM simultaneously blows past token limits and incurs massive latency and cost.
  * *The Solution:* The parser generates a lightweight `manifest.json` containing text previews and `has_images` flags[cite: 1]. The agent calls `list_available_pages` first, allowing it to act like a smart index lookup and target *only* the exact page needed[cite: 1].

* **Why Strict Tool Limits (`maximum_remote_calls=2`)?**
  * *The Problem:* Autonomous agents left unchecked can fall into infinite tool-calling loops, repeatedly querying the same pages and burning through rate limits.
  * *The Solution:* Enforcing a hard ceiling on remote tool calls guarantees deterministic completion and prevents runaway execution costs[cite: 1].

* **Why Client-Side BYOK (Bring Your Own Key) via Request Headers?**
  * *The Problem:* Hardconfiguring API keys or storing user keys in a database introduces massive security liabilities and violates privacy best practices.
  * *The Solution:* Keys are passed securely via custom HTTP headers (`X-Gemini-Api-Key`), injected directly into runtime closures for that specific session, and never touched by persistent server storage.

---

## Core Features
* **Multimodal Visual RAG:** Rasterizes PDF pages into images so the model can visually interpret layout, formatting, and tables.
* **Dynamic Tool-Use Agent:** Utilizes custom Python function bindings (`list_available_pages` and `query_pdf_page`) to give the LLM workspace navigation capabilities[cite: 1].
* **Bring Your Own Key (BYOK) Security:** Client-side API keys are passed securely via custom headers and injected into runtime closures, preventing hardcoded secrets on the server.
* **Resilient Error Handling:** Gracefully manages rate limits and server states with clean UI feedback.
* **Cloud Deployment Ready:** Fully containerized via Docker and deployed on Render.

---

## Tech Stack
* **Backend:** FastAPI, Uvicorn, PyMuPDF (fitz), Python-Dotenv, Pydantic[cite: 1]
* **AI / ML:** Google GenAI SDK (`google-genai`), Pillow (PIL)[cite: 1]
* **Frontend:** Vanilla HTML5, CSS3, Modern JavaScript (Fetch API)[cite: 1]
* **Infrastructure:** Docker (`python:3.12-slim`), Render[cite: 1]

---

## Project Structure
```text
├── backend/
│   ├── main.py             # FastAPI entrypoint, routing, session mgmt & dynamic agent creation[cite: 1]
│   └── services/
│       ├── parser.py       # Handles PDF-to-image conversion using PyMuPDF[cite: 1]
│       └── rag_engine.py   # Core agent logic, tools definition, and Gemini API bindings[cite: 1]
├── frontend/
│   ├── index.html          # UI shell containing API key bar, upload panel, and chat interface[cite: 1]
│   ├── style.css           # Modern dark-mode styling[cite: 1]
│   └── script.js           # Client-side state handling, file uploads, and chat loop[cite: 1]
├── requirements.txt        # Python package dependencies
└── Dockerfile              # Container configuration file
