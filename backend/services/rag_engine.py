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

    def list_available_pages() -> list[str]:
        """Lists all rendered page image files available for this document."""
        if not os.path.exists(session_dir):
            return []
        files = sorted(os.listdir(session_dir))
        return [f for f in files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

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
        "You are a precise PDF analysis assistant.\n\n"
        "STRICT GUARDRAILS & RULES:\n"
        "1. Do NOT loop or call tools multiple times. Execute at most 1 tool call per turn.\n"
        "2. Base your answer ONLY on the content present inside the uploaded PDF document.\n"
        "3. If the user's query or topic is not mentioned, relevant, or found anywhere in the document, "
        "explicitly state: 'I don't know based on the provided document.' Do NOT guess or hallucinate.\n"
        "4. Provide your final answer immediately after inspecting the document."
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
