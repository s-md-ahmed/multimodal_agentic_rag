import fitz
import os

def parse_pdf(pdf_path: str, session_dir: str) -> str:
    """
    Parses a PDF into PNG images in an isolated session directory.
    Converts pixmap to raw bytes immediately so the doc handle closes safely.
    """
    os.makedirs(session_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap()
            
            # Save as PNG
            image_path = os.path.join(session_dir, f"page_{page_idx + 1}.png")
            pix.save(image_path)
    finally:
        doc.close()
        
    print(f"[+] Converted {len(doc)} pages to images in {session_dir}")
    return session_dir
