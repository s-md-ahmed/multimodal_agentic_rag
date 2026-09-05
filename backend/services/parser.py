import fitz
import os
from .rag_engine import set_active_session_dir

def parse_pdf(pdf_path: str, output_dir: str = None):
    if output_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "data", "temp")
        
    os.makedirs(output_dir, exist_ok=True)
    set_active_session_dir(output_dir)
    
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap()
        image_path = os.path.join(output_dir, f"page_{page.number + 1}.png")
        # Save image bytes explicitly to release file handle before document closes
        pix.save(image_path)
        del pix  # Explicitly clear pixmap handle from memory
        
    doc.close()
    print(f"[+] Successfully converted {len(doc)} pages to images in {output_dir}")
    return output_dir
