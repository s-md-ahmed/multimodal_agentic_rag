from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from services.rag_engine import set_active_session_dir, get_temp_dir
from services.parser import parse_pdf
from google import genai
from google.genai import types
from google.genai.errors import ServerError, ClientError
import os
import tempfile
import uuid
import time
import traceback
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_SESSION = {"dir": os.path.join(tempfile.gettempdir(), "multimodal_rag_temp")}

def create_user_agent_chat(api_key: str):
    """Dynamically creates a chat session bound to the user's specific API key."""
    client = genai.Client(api_key=api_key)
    
    # Define local tool closures bound to this client's active session directory
    def list_available_pages() -> list[str]:
        """Lists all available PDF page image files in the local directory."""
        folder_path = get_temp_dir()
        print(f"\n[AGENT CHECKING FOLDER DIRECTORY: {folder_path}]\n")
        if not os.path.exists(folder_path):
            return []
        files = [f for f in os.listdir(folder_path) if f.endswith(".png")]
        return sorted(files)

    def query_pdf_with_gemini(query: str, page_number: int) -> str:
        """Searches a specific page of the PDF document by its page number."""
        folder_path = get_temp_dir()
        print(f"\n[AGENT CHOSE PAGE {page_number}] -> Running query: '{query}'\n")
        image_path = os.path.join(folder_path, f"page_{page_number}.png")
        if not os.path.exists(image_path):
            return f"Error: Page {page_number} does not exist in the directory."
        
        from PIL import Image
        with Image.open(image_path) as raw_img:
            img = raw_img.convert("RGB")
            img.load()
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=[img, query],
            config=types.GenerateContentConfig(
                tools=[],
                temperature=0.0
            )
        )
        return response.text

    return client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a precise data-extraction tool. "
                "1. First, call `list_available_pages()` to see what pages exist. "
                "2. Then, choose the correct page number and call `query_pdf_with_gemini(query, page_number)` exactly once. "
                "Do not loop. Answer the question directly and stop. "
                "If the question cannot be answered using the provided document or pages, explicitly state that you don't know based on the document."
            ),
            tools=[list_available_pages, query_pdf_with_gemini], 
            temperature=0.0
        )
    )

@app.post("/chat-with-pdf")
async def chat_with_pdf(
    prompt: str = Form(None), 
    file: UploadFile = File(None),
    x_gemini_api_key: Optional[str] = Header(None)
):
    try:
        if not x_gemini_api_key:
            raise HTTPException(
                status_code=401, 
                detail="Gemini API Key is missing. Please enter your key in the top right settings bar."
            )

        if file is not None:
            session_id = str(uuid.uuid4())
            temp_dir = os.path.join(tempfile.gettempdir(), f"multimodal_rag_{session_id}")
            os.makedirs(temp_dir, exist_ok=True)
            
            CURRENT_SESSION["dir"] = temp_dir
            set_active_session_dir(temp_dir)

            pdf_path = os.path.join(temp_dir, file.filename)
            
            contents = await file.read()
            with open(pdf_path, "wb") as f:
                f.write(contents)
            
            parse_pdf(pdf_path, temp_dir)
            return {"response": "PDF uploaded and parsed successfully."}

        if not prompt:
            return {"response": "No prompt provided."}

        set_active_session_dir(CURRENT_SESSION["dir"])
        
        # Instantiate dynamic session using the user's provided key
        agent_chat = create_user_agent_chat(x_gemini_api_key)

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

frontend_path = "/app/frontend" if os.path.exists("/app/frontend") else "frontend"
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
