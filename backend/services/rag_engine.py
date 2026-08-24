import os
import tempfile
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types
try:
    from PIL import Image
except ImportError:
    from pillow import Image
load_dotenv()
client = genai.Client()

# Global variable to track the active session directory dynamically
_ACTIVE_SESSION_DIR = os.path.join(tempfile.gettempdir(), "multimodal_rag_temp")

def set_active_session_dir(path: str):
    """Updates the active session directory so tools look in the right place."""
    global _ACTIVE_SESSION_DIR
    _ACTIVE_SESSION_DIR = path

def get_temp_dir() -> str:
    return _ACTIVE_SESSION_DIR

def list_available_pages() -> list[str]:
    """Lists all available PDF page image files in the local directory so you know which pages to query.
    
    Returns:
        A sorted list of available PNG filenames in the temp directory.
    """
    folder_path = get_temp_dir()
    print(f"\n[AGENT CHECKING FOLDER DIRECTORY: {folder_path}]\n")
    
    if not os.path.exists(folder_path):
        return []
        
    files = [f for f in os.listdir(folder_path) if f.endswith(".png")]
    return sorted(files)

def query_pdf_with_gemini(query: str, page_number: int) -> str:
    """Searches a specific page of the PDF document by its page number to extract text, charts, or tables.
    
    Args:
        query: The specific question to ask about the content on that page.
        page_number: The exact integer page index (e.g., 0, 1, 2) corresponding to the page image file.
    """
    folder_path = get_temp_dir()
    print(f"\n[AGENT CHOSE PAGE {page_number}] -> Running query: '{query}'\n")
    
    image_path = os.path.join(folder_path, f"page_{page_number}.png")
    
    if not os.path.exists(image_path):
        error_msg = f"Error: Page {page_number} does not exist in the directory. Please use list_available_pages first to check valid pages."
        print(f"[-] {error_msg}")
        return error_msg
    
    img = Image.open(image_path)
    
    response = client.models.generate_content(
        model="gemini-3.6-flash", 
        contents=[img, query],
        config=types.GenerateContentConfig(tools=[]) 
    )
    return response.text

agent_chat = client.chats.create(
    model="gemini-3.6-flash",
    config=types.GenerateContentConfig(
        system_instruction = (
            "You are an intelligent multimodal RAG assistant. "
            "DO NOT call any tools or analyze pages automatically when a file is uploaded. "
            "Wait for the user to provide a specific question or instruction before running tools or searching pages. "
            "If the user asks a question whose answer is not present in the provided document, explicitly state: "
            "'I couldn't find information about that in the provided document,' and do not generate external or general knowledge."
        ),
        tools=[query_pdf_with_gemini, list_available_pages], 
        temperature=0.0
    )
)
