import json
from datetime import datetime

from pypdf import PdfReader


def extract_version_from_title(title: str) -> str:
    """Extract version information from document title."""
    if not title:
        return None
    
    # e.g., "USB Power Delivery Specification Revision 3.1, Version 1.2"
    import re
    pattern = r"(Rev(?:ision)?\s*[\w\.\-]+(?:\s*\w+)*)"
    m = re.search(pattern, title, re.IGNORECASE)
    return m.group(1) if m else None


def get_document_metadata(reader: PdfReader) -> tuple:
    """Extract document title and version from PDF metadata."""
    title = None
    version = None
    
    try:
        md = reader.metadata
        if md:
            title = str(md.title) if getattr(md, "title", None) else None
            if title:
                version = extract_version_from_title(title)
    except Exception as e:
        # Log the error but continue with default values
        print(f"Warning: Could not extract metadata: {e}")
    
    return title, version


def main() -> None:
    pdf_path = "usb_pd_spec.pdf"
    reader = PdfReader(pdf_path)

    title, version = get_document_metadata(reader)

    payload = {
        "doc_title": title or "USB Power Delivery Specification",
        "version": version,
        "pages": len(reader.pages),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_file": pdf_path,
    }

    with open("usb_pd_metadata.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print("✅ Wrote metadata to usb_pd_metadata.jsonl")


if __name__ == "__main__":
    main()
