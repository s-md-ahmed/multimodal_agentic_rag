from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from services.rag_engine import agent_chat, set_active_session_dir
from services.parser import parse_pdf
import os
import tempfile
import uuid
import time
import traceback
from google.genai.errors import ServerError, ClientError

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_SESSION = {"dir": os.path.join(tempfile.gettempdir(), "multimodal_rag_temp")}

@app.post("/chat-with-pdf")
async def chat_with_pdf(prompt: str = Form(None), file: UploadFile = File(None)):
    try:
        if file is not None:
            session_id = str(uuid.uuid4())
            temp_dir = os.path.join(tempfile.gettempdir(), f"multimodal_rag_{session_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            CURRENT_SESSION["dir"] = temp_dir
            set_active_session_dir(temp_dir)

            pdf_path = os.path.join(temp_dir, file.filename)
            
            # Stream/write the file safely in chunks to prevent memory locking/hanging
            contents = await file.read()
            with open(pdf_path, "wb") as f:
                f.write(contents)
            
            # Parse the PDF into images
            parse_pdf(pdf_path, temp_dir)
            return {"response": "PDF uploaded and parsed successfully."}

        if not prompt:
            return {"response": "No prompt provided."}

        set_active_session_dir(CURRENT_SESSION["dir"])

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
                        print(f"--- API busy/rate-limited (Attempt {attempt + 1}), retrying in {delay}s... ---")
                        time.sleep(delay)
                        delay *= 2 
                        continue
                raise api_err

        return {"response": response.text}
        
    except Exception as e:
        print("--- BACKEND ERROR TRACEBACK ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Automatically picks up Render's PORT environment variable, defaults to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)