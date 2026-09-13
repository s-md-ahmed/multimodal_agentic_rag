import pymupdf as fitz
import os
import json

def parse_pdf(pdf_path: str, session_dir: str) -> list[str]:
    """
    Renders each page of the PDF into a JPEG, saves a metadata manifest,
    and returns a list of image filenames.
    """
    os.makedirs(session_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []
    manifest = {}

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=110)
        
        filename = f"page_{page_num + 1}.jpg"
        filepath = os.path.join(session_dir, filename)
        pix.save(filepath)
        image_paths.append(filename)

        # Quick check for images or visual elements on this page
        images_on_page = page.get_images()
        manifest[filename] = {
            "page_number": page_num + 1,
            "has_images": len(images_on_page) > 0,
            "preview_text": page.get_text()[:100].strip().replace("\n", " ")
        }

    # Save manifest in session directory
    with open(os.path.join(session_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f)

    doc.close()
    return image_paths
