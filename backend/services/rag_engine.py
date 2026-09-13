import os
from PIL import Image
from google import genai
from google.genai import types

def create_session_agent(api_key: str, session_dir: str, chat_history: list = None):
    """
    Creates a Gemini client and initializes a chat session configured with 
    strict tool limits and explicit guardrails for relevance.
    """
    client = genai.Client(api_key=api_key)

    def list_available_pages() -> str:
        """Returns a structural manifest of all pages, showing which pages contain images or text snippets."""
        manifest_path = os.path.join(session_dir, "manifest.json")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r") as f:
                return f.read()
        
        # Fallback if manifest doesn't exist
        files = sorted(os.listdir(session_dir))
        return str([f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))])

    def query_pdf_page(page_filename: str, query: str) -> str:
        """
        Inspects a specific page image from the PDF using visual AI.
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
                return response.text if response.text else "No relevant content found on this page."
        except Exception as e:
            return f"Failed to read image: {str(e)}"

    sys_instruction = (
        "You are an intelligent, generalized autonomous PDF analysis assistant.\n\n"
        "INSTRUCTIONS:\n"
        "1. Call `list_available_pages` first to review the document manifest (which shows page numbers, text previews, and `has_images` flags).\n"
        "2. Analyze the user's query:\n"
        "   - For targeted facts, pick the specific page indicated by the manifest.\n"
        "   - For global requests like finding images, look at the manifest flags (`has_images: true`) to immediately target the right pages on your next call.\n"
        "3. Use `query_pdf_page` to inspect the relevant page(s).\n"
        "4. Base your answer strictly on the inspected content.\n\n"
        "STRICT GUARDRAILS:\n"
        "- Do NOT guess or hallucinate.\n"
        "- Execute at most 2 tool calls per turn."
    )
    chat = client.chats.create(
        model="gemini-3.6-flash",
        history=chat_history or [],
        config=types.GenerateContentConfig(
            system_instruction=sys_instruction,
            tools=[list_available_pages, query_pdf_page],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                maximum_remote_calls=2  # Prevents tool looping
            )
        )
    )
    
    return chat 
