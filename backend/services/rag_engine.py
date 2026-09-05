import os
from google import genai
from google.genai import types
from PIL import Image

def create_session_agent(api_key: str, session_dir: str):
    """
    Dynamically creates a Gemini chat agent bound strictly to a specific
    session directory without using global variable state.
    """
    client = genai.Client(api_key=api_key)

    def list_available_pages() -> list[str]:
        """Lists all available PDF page image files in the local session directory."""
        print(f"\n[AGENT CHECKING SESSION DIRECTORY: {session_dir}]\n")
        if not os.path.exists(session_dir):
            return []
        files = [f for f in os.listdir(session_dir) if f.endswith(".png")]
        return sorted(files)

    def query_pdf_with_gemini(query: str, page_number: int) -> str:
        """Searches a specific page of the PDF document by its page number."""
        print(f"\n[AGENT CHOSE PAGE {page_number}] -> Running query: '{query}'\n")
        image_path = os.path.join(session_dir, f"page_{page_number}.png")
        
        if not os.path.exists(image_path):
            error_msg = f"Error: Page {page_number} does not exist in the directory."
            print(f"[-] {error_msg}")
            return error_msg

        # Load completely into memory buffer to avoid lazy PIL handle locks
        with Image.open(image_path) as raw_img:
            img = raw_img.convert("RGB").copy()

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
