import os
from PIL import Image
from google import genai
from google.genai import types

def create_session_agent(api_key: str, session_dir: str, chat_history: list = None):
    """
    Creates a Gemini client and initializes a chat session configured with 
    automatic function calling for inspecting PDF page images.
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
        Inspects a specific page image from the PDF using visual AI to answer 
        questions about visual elements, text content, tables, or diagrams.
        """
        image_path = os.path.join(session_dir, page_filename)
        if not os.path.exists(image_path):
            return f"Error: Image {page_filename} does not exist."

        try:
            with Image.open(image_path) as img:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=[img, f"Analyze this page image and answer: {query}"]
                )
                return response.text if response.text else "No content detected on page."
        except Exception as e:
            return f"Failed to read image: {str(e)}"

    sys_instruction = (
        "You analyze PDF documents using provided tools. "
        "Inspect a maximum of 3 relevant pages using query_pdf_page. "
        "Always conclude with a clear, direct summary response for the user."
    )

    chat = client.chats.create(
        model="gemini-3.6-flash",
        history=chat_history or [],
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            tools=[list_available_pages, query_pdf_page],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=5
            )
        )
    )
    
    return chat
