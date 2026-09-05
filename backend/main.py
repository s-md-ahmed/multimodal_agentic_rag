import os
import tempfile
import uuid
import time
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from google.genai.errors import ServerError, ClientError

from services.parser import parse_pdf
from services.rag_engine import MultimodalRAGEngine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/chat-with-pdf")
async def chat_with_pdf(
    prompt: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    x_gemini_api_key: Optional[str] = Header(None),
    x_session_id: Optional[str] = Header(None)
):
    try:
        # 1. Enforce BYOK Security
        if not x_gemini_api_key:
            raise HTTPException(
                status_code=401,
                detail="Gemini API Key is missing. Please enter your key in the top settings bar."
            )

        # 2. Derive or assign thread-safe Session ID
        session_id = x_session_id or str(uuid.uuid4())
        session_dir = os.path.join(tempfile.gettempdir(), f"multimodal_rag_{session_id}")
        os.makedirs(session_dir, exist_ok=True)

        # 3. File Upload Step
        if file is not None:
            pdf_path = os.path.join(session_dir, file.filename)
            contents = await file.read()
            with open(pdf_path, "wb") as f:
                f.write(contents)

            # Rasterize PDF into PNG page frames within this session's folder
            parse_pdf(pdf_path, session_dir)
            
            return {
                "response": "PDF uploaded and parsed successfully.",
                "session_id": session_id
            }

        # 4. Chat / Query Step
        if not prompt:
            return {"response": "No prompt provided.", "session_id": session_id}

        # Instantiate isolated engine per request
        engine = MultimodalRAGEngine(session_dir=session_dir, api_key=x_gemini_api_key)

        # Exponential backoff retry logic for API resilience
        max_retries = 3
        delay = 2
        response_text = ""

        for attempt in range(max_retries):
            try:
                response_text = engine.run_query(prompt)
                break
            except (ServerError, ClientError) as api_err:
                err_str = str(api_err)
                if "503" in err_str or "429" in err_str:
                    if attempt < max_retries - 1:
                        print(f"--- API busy/rate-limited (Attempt {attempt + 1}), retrying in {delay}s... ---")
                        time.sleep(delay)
                        delay *= 2
                        continue
                raise api_err

        return {
            "response": response_text,
            "session_id": session_id
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print("--- BACKEND ERROR TRACEBACK ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Mount frontend assets
frontend_path = "/app/frontend" if os.path.exists("/app/frontend") else "frontend"
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
