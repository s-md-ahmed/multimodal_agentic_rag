import os
from pathlib import Path
from google import genai
from google.genai import types
from PIL import Image

class MultimodalRAGEngine:
    def __init__(self, session_dir: str, api_key: str | None = None):
        """
        Thread-safe RAG engine instance scoped exclusively to a single user session.
        """
        self.session_dir = Path(session_dir)
        # Use provided client key (BYOK) or fall back to system environment variables
        self.client = genai.Client(api_key=api_key) if api_key else genai.Client()

    def _list_available_pages(self) -> list[str]:
        """Lists available PDF page images isolated to this session directory."""
        if not self.session_dir.exists():
            return []
        files = [f.name for f in self.session_dir.glob("page_*.png")]
        return sorted(files)

    def _query_pdf_page(self, query: str, page_number: int) -> str:
        """Inspects a specific page image within this session directory using Gemini Vision."""
        image_path = self.session_dir / f"page_{page_number}.png"
        
        if not image_path.exists():
            return f"Error: Page {page_number} does not exist in the session directory."

        try:
            with Image.open(image_path) as img:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[img, query],
                    config=types.GenerateContentConfig()
                )
                return response.text or "No text generated."
        except Exception as e:
            return f"Execution error on page {page_number}: {str(e)}"

    def run_query(self, user_prompt: str) -> str:
        """Executes an isolated, single-request agentic tool-calling conversation."""
        
        # Local closures bind tool execution directly to 'self' (thread-safe)
        def list_available_pages() -> list[str]:
            """Lists all available PDF page image files in the local session directory."""
            return self._list_available_pages()

        def query_pdf_with_gemini(query: str, page_number: int) -> str:
            """Searches a specific page of the PDF document by its page number."""
            return self._query_pdf_page(query, page_number)

        # Chat session instantiated dynamically per request (prevents history bleed)
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
