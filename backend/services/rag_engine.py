import io
import os
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

class MultimodalRAGEngine:
    def __init__(self, session_dir: str, api_key: str | None = None):
        self.session_dir = Path(session_dir)
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()

    def _list_available_pages(self) -> list[str]:
        if not self.session_dir.exists():
            return []
        files = [f.name for f in self.session_dir.glob("page_*.png")]
        return sorted(files)

    def _query_pdf_page(self, query: str, page_number: int) -> str:
        image_path = self.session_dir / f"page_{page_number}.png"
        
        if not image_path.exists():
            return f"Error: Page {page_number} does not exist in the session directory."

        try:
            # Load pixel data entirely into RAM to prevent PyMuPDF/PIL lazy-handle crashes
            with Image.open(image_path) as raw_img:
                img = raw_img.convert("RGB")
                img.load()  # Force full buffer load

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[img, query],
                config=types.GenerateContentConfig()
            )
            return response.text or "No text generated."
        except Exception as e:
            return f"Execution error on page {page_number}: {str(e)}"

    def run_query(self, user_prompt: str) -> str:
        def list_available_pages() -> list[str]:
            return self._list_available_pages()

        def query_pdf_with_gemini(query: str, page_number: int) -> str:
            return self._query_pdf_page(query, page_number)

        chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a precise data-extraction tool. "
                    "1. First, call `list_available_pages()` to see what pages exist. "
                    "2. Then, choose the correct page number and call `query_pdf_with_gemini(query, page_number)` exactly once. "
                    "Do not loop. Answer the question directly and stop. "
                    "If the question cannot be answered using the provided document or pages, explicitly state that you don't know based on the document."
                ),
                tools=[list_available_pages, query_pdf_with_gemini]
            )
        )
        
        response = chat.send_message(user_prompt)
        return response.text
