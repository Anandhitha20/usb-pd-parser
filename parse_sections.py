import json
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

from pypdf import PdfReader


@dataclass
class SectionEntry:
    doc_title: str
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    content: str
    tags: List[str]


def extract_all_text(reader: PdfReader) -> List[str]:
    texts: List[str] = []
    for i in range(len(reader.pages)):
        texts.append(reader.pages[i].extract_text() or "")
    return texts


def find_actual_document_start(pages: List[str]) -> int:
    """Find where the actual document content starts (after revision history)."""
    # Look for patterns that indicate the start of actual content
    for i, text in enumerate(pages):
        # Look for chapter 1 or main content indicators
        if re.search(r"^1\s+[A-Z][a-z]+", text, re.MULTILINE):
            return i
        if re.search(r"Chapter\s+1", text, re.IGNORECASE):
            return i
        if re.search(r"^1\.1\s+[A-Z]", text, re.MULTILINE):
            return i
        # Also look for any numbered section
        if re.search(r"^\d+\.\d+\s+[A-Z]", text, re.MULTILINE):
            return i
        # Look for any content that looks like a section
        if re.search(r"^\d+\s+[A-Z]", text, re.MULTILINE):
            return i
    return 5  # Very early start to capture more content


def is_valid_section_title(title: str) -> bool:
    """Check if a title is a valid section title."""
    # Must be meaningful
    if len(title.strip()) < 1:  # Very permissive
        return False
    
    # Must not be revision history
    revision_patterns = [
        r"\b(19|20)\d{2}\b",
        r"Initial release",
        r"Including errata",
        r"Editorial changes",
        r"Revision Version",
        r"This version incorporates",
        r"ECNs?:",
        r"Page \d+",
        r"Universal Serial Bus.*Specification",
        r"Revision History",
        r"hex data",
        r"Table of Contents",
        r"List of Figures",
        r"List of Tables",
    ]
    
    for pattern in revision_patterns:
        if re.search(pattern, title, re.IGNORECASE):
            return False
    
    # Must be mostly alphabetic (very permissive)
    alpha_chars = sum(1 for c in title if c.isalpha())
    if alpha_chars < len(title) * 0.2:  # Very low threshold
        return False
    
    return True


def find_headings(pages: List[str]) -> List[Tuple[str, str, int]]:
    """Find actual document section headings with maximum coverage."""
    start_page = find_actual_document_start(pages)
    findings: List[Tuple[str, str, int]] = []
    
    # Look for actual document sections starting from the identified start page
    for idx, text in enumerate(pages[start_page:], start=start_page):
        # Pattern 1: Main chapters "1 Overview", "2 Introduction"
        chapter_pattern = re.compile(
            r"^(?P<sid>\d+)\s+(?P<title>[A-Z][a-zA-Z\s\-\(\)\.]+?)(?:\s+\d+)?$", 
            re.MULTILINE
        )
        for m in chapter_pattern.finditer(text):
            sid = m.group("sid").strip()
            title = m.group("title").strip()
            
            if is_valid_section_title(title):
                findings.append((sid, title, idx + 1))
        
        # Pattern 2: Subsections "1.1 Introduction", "2.3.4 Details"
        section_pattern = re.compile(
            r"^(?P<sid>\d+(?:\.\d+)+)\s+(?P<title>[A-Z][a-zA-Z\s\-\(\)\.]+?)(?:\s+\d+)?$", 
            re.MULTILINE
        )
        for m in section_pattern.finditer(text):
            sid = m.group("sid").strip()
            title = m.group("title").strip()
            
            if is_valid_section_title(title):
                findings.append((sid, title, idx + 1))
        
        # Pattern 3: More flexible pattern for subsections
        flexible_pattern = re.compile(
            r"^(?P<sid>\d+(?:\.\d+)*)\s+(?P<title>[A-Z][a-zA-Z\s\-\(\)\.]+?)(?:\s+\d+)?$", 
            re.MULTILINE
        )
        for m in flexible_pattern.finditer(text):
            sid = m.group("sid").strip()
            title = m.group("title").strip()
            
            # Skip if already found or invalid
            if any(f[0] == sid for f in findings):
                continue
            if not is_valid_section_title(title):
                continue
                
            findings.append((sid, title, idx + 1))
        
        # Pattern 4: Very flexible pattern for any numbered content
        very_flexible_pattern = re.compile(
            r"^(?P<sid>\d+(?:\.\d+)*)\s+(?P<title>[A-Z][^0-9\n]+?)(?:\s+\d+)?$", 
            re.MULTILINE
        )
        for m in very_flexible_pattern.finditer(text):
            sid = m.group("sid").strip()
            title = m.group("title").strip()
            
            # Skip if already found or invalid
            if any(f[0] == sid for f in findings):
                continue
            if not is_valid_section_title(title):
                continue
                
            findings.append((sid, title, idx + 1))
    
    # Deduplicate and sort
    seen = set()
    unique: List[Tuple[str, str, int]] = []
    for sid, title, page in sorted(
        findings, 
        key=lambda t: (list(map(int, t[0].split('.'))), t[2])
    ):
        if sid in seen:
            continue
        seen.add(sid)
        unique.append((sid, title, page))
    
    return unique


def create_page_based_sections(pages: List[str], doc_title: str) -> List[SectionEntry]:
    """Create sections based on pages to ensure maximum coverage."""
    entries: List[SectionEntry] = []
    
    # Start from page 5 to skip front matter
    for page_num in range(5, len(pages)):
        content = pages[page_num].strip()
        
        # Skip empty or very short pages
        if len(content) < 50:
            continue
            
        # Extract a title from the first line or create one
        lines = content.split('\n')
        title = "Page Content"
        
        # Try to find a meaningful title
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 10 and len(line) < 100:
                # Check if it looks like a title
                if re.match(r'^[A-Z][a-zA-Z\s\-\(\)\.]+$', line):
                    title = line
                    break
                elif re.match(r'^\d+\.\d+\s+[A-Z]', line):
                    title = line
                    break
        
        # Create a section ID based on page number
        section_id = f"page_{page_num + 1}"
        
        entries.append(
            SectionEntry(
                doc_title=doc_title,
                section_id=section_id,
                title=title,
                page=page_num + 1,
                level=1,
                parent_id=None,
                full_path=f"{section_id} {title}",
                content=content,
                tags=["page_content"],
            )
        )
    
    return entries


def build_sections(pages: List[str], headings: List[Tuple[str, str, int]], 
                  doc_title: str) -> List[SectionEntry]:
    entries: List[SectionEntry] = []
    num_pages = len(pages)

    # Sort headings by page and section ID
    def numeric_key(sid: str) -> Tuple[int, ...]:
        return tuple(int(p) for p in sid.split("."))

    headings_sorted = sorted(headings, key=lambda h: (h[2], numeric_key(h[0])))

    for idx, (sid, title, page_start) in enumerate(headings_sorted):
        if idx + 1 < len(headings_sorted):
            next_page = headings_sorted[idx + 1][2]
            page_end = max(page_start, next_page - 1)
        else:
            page_end = num_pages

        # Clip to valid bounds
        page_start = max(1, min(page_start, num_pages))
        page_end = max(1, min(page_end, num_pages))

        # Get content for this section
        content_pages = pages[page_start - 1 : page_end]
        content = ("\n\n".join(content_pages)).strip()

        level = sid.count(".") + 1
        parent_id = ".".join(sid.split(".")[:-1]) if "." in sid else None

        entries.append(
            SectionEntry(
                doc_title=doc_title,
                section_id=sid,
                title=title,
                page=page_start,
                level=level,
                parent_id=parent_id,
                full_path=f"{sid} {title}",
                content=content,
                tags=[],
            )
        )
    return entries


def get_document_title(reader: PdfReader) -> str:
    """Extract document title from PDF metadata."""
    doc_title = "USB Power Delivery Specification"
    try:
        if reader.metadata and reader.metadata.title:
            doc_title = str(reader.metadata.title)
    except Exception as e:
        # Log the error but continue with default title
        print(f"Warning: Could not extract document title: {e}")
    
    return doc_title


def main() -> None:
    pdf_path = "usb_pd_spec.pdf"
    reader = PdfReader(pdf_path)

    doc_title = get_document_title(reader)

    pages = extract_all_text(reader)
    
    # Try structured approach first for better ToC alignment
    headings = find_headings(pages)
    structured_sections = build_sections(pages, headings, doc_title)
    
    # Only use page-based approach if structured approach gives very few sections
    if len(structured_sections) < 100:  # Threshold for minimum structured sections
        page_based_sections = create_page_based_sections(pages, doc_title)
        
        # Use the approach that gives more coverage but prioritize structured
        if len(page_based_sections) > len(structured_sections) * 2:
            sections = page_based_sections
            print(f"Using page-based approach: {len(sections)} sections")
        else:
            sections = structured_sections
            print(f"Using structured approach: {len(sections)} sections")
    else:
        sections = structured_sections
        print(f"Using structured approach: {len(sections)} sections")

    with open("usb_pd_spec.jsonl", "w", encoding="utf-8") as f:
        for entry in sections:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    print(f"✅ Wrote {len(sections)} sections to usb_pd_spec.jsonl")


if __name__ == "__main__":
    main()

