import os
import tempfile
import uuid
import time
import shutil
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.genai.errors import ServerError, ClientError

from services.parser import parse_pdf
from services.rag_engine import create_session_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store mapped sessions: session_id -> {"dir": session_dir, "created_at": timestamp}
SESSION_STORE: dict[str, dict] = {}
SESSION_TTL_SECONDS = 3600  # 1 hour expiration for temporary disk cleanup


def cleanup_stale_sessions():
    """Removes temporary directories older than TTL to avoid filling container storage."""
    now = time.time()
    expired_ids = []
    for sid, data in SESSION_STORE.items():
        if now - data["created_at"] > SESSION_TTL_SECONDS:
            expired_ids.append(sid)

    for sid in expired_ids:
        data = SESSION_STORE.pop(sid, None)
        if data and os.path.exists(data["dir"]):
            try:
                shutil.rmtree(data["dir"])
                print(f"[CLEANUP] Removed expired session directory: {data['dir']}")
            except Exception as e:
                print(f"[CLEANUP ERROR] Failed to delete {data['dir']}: {e}")


@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    cleanup_stale_sessions()

    if not x_gemini_api_key:
        raise HTTPException(
            status_code=401,
            detail="Gemini API Key missing in headers."
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        session_id = str(uuid.uuid4())
        session_dir = tempfile.mkdtemp(prefix=f"rag_session_{session_id}_")

        pdf_path = os.path.join(session_dir, file.filename)
        contents = await file.read()
        with open(pdf_path, "wb") as f:
            f.write(contents)

        # Parse document synchronously into isolated session folder
        parse_pdf(pdf_path, session_dir)

        SESSION_STORE[session_id] = {
            "dir": session_dir,
            "created_at": time.time()
        }

        return {
            "session_id": session_id,
            "response": "PDF uploaded and parsed successfully."
        }

    except Exception as e:
        print("--- UPLOAD ERROR TRACEBACK ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat-with-pdf")
async def chat_with_pdf(
    prompt: str = Form(...),
    session_id: str = Form(...),
    x_gemini_api_key: Optional[str] = Header(None, alias="X-Gemini-API-Key")
):
    cleanup_stale_sessions()

    if not x_gemini_api_key:
        raise HTTPException(
            status_code=401,
            detail="Gemini API Key missing in headers."
        )

    session_data = SESSION_STORE.get(session_id)
    if not session_data or not os.path.exists(session_data["dir"]):
        raise HTTPException(
            status_code=404,
            detail="Active session expired or not found. Please upload your PDF again."
        )

    session_dir = session_data["dir"]

    try:
        agent_chat = create_session_agent(x_gemini_api_key, session_dir)

        max_retries = 3
        delay = 2
        response = None

        for attempt in range(max_retries):
            try:
                response = agent_chat.send_message(prompt)
                break
            except (ServerError, ClientError) as api_err:
                err_str = str(api_err)
                if "503" in err_str or "429" in err_str:
                    if attempt < max_retries - 1:
                        print(f"--- API Busy/Rate-Limited (Attempt {attempt + 1}), retrying in {delay}s... ---")
                        time.sleep(delay)
                        delay *= 2
                        continue
                raise api_err

        return {"response": response.text}

    except Exception as e:
        print("--- CHAT ERROR TRACEBACK ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Mount Frontend Assets
frontend_path = "/app/frontend" if os.path.exists("/app/frontend") else os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
