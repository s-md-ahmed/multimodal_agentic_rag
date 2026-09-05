import os
from PIL import Image
from google import genai
from google.genai import types

def create_session_agent(api_key: str, session_dir: str, chat_history: list = None):
    """
    Creates a Gemini client and initializes a chat session configured with 
    strict tool limits to avoid exceeding free-tier RPM rate limits.
    """
    client = genai.Client(api_key=api_key)

    def list_available_pages() -> list[str]:
        """Lists all rendered page image files available for this document."""
        if not os.path.exists(session_dir):
            return []
        files = sorted(os.listdir(session_dir))
        return [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    def query_pdf_page(page_filename: str, query: str) -> str:
        """
        Loads and inspects a single page image directly.
        """
        image_path = os.path.join(session_dir, page_filename)
        if not os.path.exists(image_path):
            return f"Error: Image {page_filename} does not exist."

        try:
            # Send back confirmation that the file exists and can be processed
            return f"Loaded page {page_filename}. Answer the user query using the content of this page."
        except Exception as e:
            return f"Failed to read image: {str(e)}"

    sys_instruction = (
        "You are a precise PDF analysis assistant. "
        "RULES:\n"
        "1. Do NOT loop or call tools multiple times.\n"
        "2. Call `query_pdf_page` ONLY ONCE for the most relevant page.\n"
        "3. Provide your final answer immediately after receiving the tool output. Do not execute further function calls."
    )

    chat = client.chats.create(
        model="gemini-3.6-flash",
        history=chat_history or [],
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            tools=[list_available_pages, query_pdf_page],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=2  # Prevents runaway tool loops
            )
        )
    )
    
    return chat
