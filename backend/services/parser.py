import fitz
import os

def parse_pdf(pdf_path: str, session_dir: str) -> str:
    """
    Parses a PDF file into individual page PNG images inside an isolated session directory.
    Decouples raw rendering from fitz doc handles to prevent 'document closed' errors.
    """
    os.makedirs(session_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    try:
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap()
            
            # Convert to raw PNG bytes so PyMuPDF can safely close
            img_bytes = pix.tobytes("png")
            image_path = os.path.join(session_dir, f"page_{page_idx + 1}.png")
            
            with open(image_path, "wb") as f:
                f.write(img_bytes)
    finally:
        doc.close()
        
    print(f"[+] Successfully converted {len(doc)} pages to images in {session_dir}")
    return session_dir
