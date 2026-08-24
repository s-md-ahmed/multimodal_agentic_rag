import os
import tempfile
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()
client = genai.Client()

_ACTIVE_SESSION_DIR = os.path.join(tempfile.gettempdir(), "multimodal_rag_temp")

def set_active_session_dir(path: str):
    global _ACTIVE_SESSION_DIR
    _ACTIVE_SESSION_DIR = path

def get_temp_dir() -> str:
    return _ACTIVE_SESSION_DIR

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
        error_msg = f"Error: Page {page_number} does not exist in the directory."
        print(f"[-] {error_msg}")
        return error_msg
    
    img = Image.open(image_path)
    
    response = client.models.generate_content(
        model="gemini-3.6-flash", 
        contents=[img, query],
        config=types.GenerateContentConfig(tools=[]),
        temperature=0.0,
        
    )
    return response.text

agent_chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction = (
            "You are an intelligent multimodal RAG assistant. "
            "MANDATORY RULE: You MUST call `list_available_pages()` first to see what pages exist, "
            "and then you MUST call `query_pdf_with_gemini(query, page_number)` to inspect the page images before answering any question about the document. "
            "Never guess or assume information is missing without checking the page images using the tools first. "
            "If after using the tools the answer is truly not present, explicitly state: "
            "'I couldn't find information about that in the provided document.'"
        ),
        tools=[query_pdf_with_gemini, list_available_pages], 
        temperature=0.0
    )
)
