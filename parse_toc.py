import json
import re
from dataclasses import asdict
from typing import List, Optional, Tuple

from pypdf import PdfReader
from base_models import TocEntry


DOC_TITLE_DEFAULT = "USB Power Delivery Specification"


def normalize_title(raw_title: str) -> str:
    """Normalize a title by removing dot leaders and excessive whitespace.
    
    Args:
        raw_title: The raw title string from the PDF
        
    Returns:
        Cleaned title string with dot leaders and extra whitespace removed
    """
    title = raw_title.strip()
    # Replace dot leaders (.....) and excessive whitespace
    title = re.sub(r"\.{2,}", " ", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip(" .")


def infer_parent_id(section_id: str) -> Optional[str]:
    """Infer the parent section ID from a given section ID.
    
    Args:
        section_id: The section ID (e.g., "2.1.2")
        
    Returns:
        Parent section ID (e.g., "2.1") or None if top-level
    """
    return ".".join(section_id.split(".")[:-1]) if "." in section_id else None


def find_toc_text(reader: PdfReader, max_scan_pages: int = 100) -> Tuple[str, int]:
    """Extract text from the first N pages as the likely ToC region.
    
    Args:
        reader: PDF reader object
        max_scan_pages: Maximum number of pages to scan for ToC
        
    Returns:
        Tuple of (concatenated text, total number of pages in PDF)
    """
    num_pages = len(reader.pages)
    max_scan_pages = min(max_scan_pages, num_pages)

    collected_text: List[str] = []
    for i in range(max_scan_pages):
        page_text = reader.pages[i].extract_text() or ""
        collected_text.append(page_text)
    return ("\n".join(collected_text), num_pages)


def parse_toc_entries(toc_text: str, num_pages: int, doc_title: str) -> List[TocEntry]:
    """Parse Table of Contents entries from extracted text.
    
    Args:
        toc_text: Text containing the table of contents
        num_pages: Total number of pages in the PDF
        doc_title: Title of the document
        
    Returns:
        List of TocEntry objects representing the parsed table of contents
    """
    # Match lines like: 2.1.3 Title .......... 54
    # Capture the last integer as page, ensure it is within the PDF page count.
    pattern = re.compile(
        r"^(?P<sid>\d+(?:\.\d+)*)\s+(?P<title>[^\n]+?)\s+(?P<page>\d{1,4})\s*$", 
        re.MULTILINE
    )
    entries: List[TocEntry] = []
    seen_section_ids = set()

    for match in pattern.finditer(toc_text):
        sec_id = match.group("sid").strip()
        raw_title = match.group("title")
        page_str = match.group("page")

        # Page sanity check
        page_num = int(page_str)
        if page_num < 1 or page_num > num_pages:
            continue

        title = normalize_title(raw_title)

        # Basic guardrails to avoid revision history rows, which often include dates
        if re.search(r"\b(19|20)\d{2}\b", title):
            continue

        level = sec_id.count(".") + 1
        parent_id = infer_parent_id(sec_id)

        if sec_id in seen_section_ids:
            continue
        seen_section_ids.add(sec_id)

        entries.append(
            TocEntry(
                doc_title=doc_title,
                section_id=sec_id,
                title=title,
                page=page_num,
                level=level,
                parent_id=parent_id,
                full_path=f"{sec_id} {title}",
                tags=[],
            )
        )

    return entries


def get_document_title(reader: PdfReader) -> str:
    """Extract document title from PDF metadata.
    
    Args:
        reader: PDF reader object
        
    Returns:
        Document title string, defaults to DOC_TITLE_DEFAULT if not found
    """
    doc_title = DOC_TITLE_DEFAULT
    try:
        if reader.metadata and reader.metadata.title:
            doc_title = str(reader.metadata.title)
    except Exception as e:
        # Log the error but continue with default title
        print(f"Warning: Could not extract document title: {e}")
    
    return doc_title


def main() -> None:
    """Main function to extract Table of Contents from PDF and save as JSONL.
    
    Reads the USB PD specification PDF, extracts the table of contents,
    parses it into structured entries, and saves the result to usb_pd_toc.jsonl.
    """
    pdf_path = "usb_pd_spec.pdf"
    reader = PdfReader(pdf_path)
    toc_text, num_pages = find_toc_text(reader, max_scan_pages=120)

    # Determine document title
    doc_title = get_document_title(reader)

    toc_entries = parse_toc_entries(toc_text, num_pages, doc_title)

    with open("usb_pd_toc.jsonl", "w", encoding="utf-8") as f:
        for entry in toc_entries:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    print(f"✅ Extracted {len(toc_entries)} TOC entries into usb_pd_toc.jsonl")


if __name__ == "__main__":
    main()
