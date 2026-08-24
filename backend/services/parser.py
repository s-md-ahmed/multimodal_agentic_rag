import fitz
import os

def parse_pdf(pdf_path: str, output_dir: str = None):
    if output_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(base_dir, "data", "temp")
        
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    for page in doc:
        pix = page.get_pixmap()
        image_path = os.path.join(output_dir, f"page_{page.number}.png")
        pix.save(image_path)
        
    print(f"[+] Successfully converted {len(doc)} pages to images in {output_dir}")
    return output_dir