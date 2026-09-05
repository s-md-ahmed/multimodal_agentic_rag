import pymupdf as fitz
import os

def parse_pdf(pdf_path: str, session_dir: str) -> list[str]:
    """
    Renders each page of the PDF into a JPEG image, saves it in session_dir,
    and returns a list of image filenames.
    """
    os.makedirs(session_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    image_paths = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        
        filename = f"page_{page_num + 1}.jpg"
        filepath = os.path.join(session_dir, filename)
        pix.save(filepath)
        image_paths.append(filename)

    doc.close()
    return image_paths
