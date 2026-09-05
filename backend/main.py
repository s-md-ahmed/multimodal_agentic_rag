import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.parser import parse_pdf
from services.rag_engine import create_session_agent

app = FastAPI(title="PDF Vision RAG Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent in-memory session store: { session_id: { "dir": str, "history": list } }
SESSIONS = {}
UPLOAD_BASE_DIR = "/tmp/pdf_sessions"

class ChatResponse(BaseModel):
    response: str
    session_id: str

@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    x_gemini_api_key: str = Header(..., alias="X-Gemini-Api-Key")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    session_id = str(uuid.uuid4())
    session_dir = os.path.join(UPLOAD_BASE_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    temp_pdf_path = os.path.join(session_dir, "document.pdf")
    with open(temp_pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        pages = parse_pdf(temp_pdf_path, session_dir)
    except Exception as e:
        shutil.rmtree(session_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

    SESSIONS[session_id] = {
        "dir": session_dir,
        "history": []
    }

    return {
        "session_id": session_id,
        "message": f"Successfully processed {len(pages)} pages.",
        "pages": pages
    }

@app.post("/chat-with-pdf", response_model=ChatResponse)
async def chat_with_pdf(
    prompt: str = Form(...),
    session_id: str = Form(...),
    x_gemini_api_key: str = Header(..., alias="X-Gemini-Api-Key")
):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    session_data = SESSIONS[session_id]
    session_dir = session_data["dir"]
    chat_history = session_data["history"]

    try:
        chat = create_session_agent(
            api_key=x_gemini_api_key, 
            session_dir=session_dir,
            chat_history=chat_history
        )

        response = chat.send_message(prompt)

        # PREVENT EMPTY ANSWERS:
        # If max tool calls hit before narrative text generation, force a final response.
        if not response.text or not response.text.strip():
            force_text_response = chat.send_message(
                "Based on the tool calls and page inspections performed so far, "
                "provide a complete answer right now. Do NOT call any more tools."
            )
            final_text = force_text_response.text
        else:
            final_text = response.text

        # Persist updated conversation history
        session_data["history"] = chat.get_history()

        # Hard fallback safety check
        if not final_text or not final_text.strip():
            final_text = "Analysis completed, but no text could be generated from the selected pages."

        return ChatResponse(response=final_text, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")
