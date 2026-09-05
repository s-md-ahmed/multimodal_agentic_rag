import fitz
import os

def parse_pdf(pdf_path: str, output_dir: str):
    """
    Rasterizes PDF pages into PNG images and saves them directly into the target session directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap()
        # Use 1-based indexing so page_1.png aligns with Gemini tool page queries
        image_path = os.path.join(output_dir, f"page_{page.number + 1}.png")
        pix.save(image_path)
        
    doc.close()
    print(f"[+] Successfully converted {len(doc)} pages to images in {output_dir}")
    return output_dir
