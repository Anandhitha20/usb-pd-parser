import json
from datetime import datetime

from pypdf import PdfReader


def main() -> None:
    pdf_path = "usb_pd_spec.pdf"
    reader = PdfReader(pdf_path)

    title = None
    version = None
    try:
        md = reader.metadata
        if md:
            title = str(md.title) if getattr(md, "title", None) else None
            # Attempt to infer version from title
            if title:
                # e.g., "USB Power Delivery Specification Revision 3.1, Version 1.2"
                import re

                m = re.search(r"(Rev(?:ision)?\s*[\w\.\-]+(?:\s*\w+)*)", title, re.IGNORECASE)
                if m:
                    version = m.group(1)
    except Exception:
        pass

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

