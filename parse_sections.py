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


def find_headings(pages: List[str]) -> List[Tuple[str, str, int]]:
    # Heading pattern: 1, 1.2, 2.4.3, etc. followed by a title
    heading_re = re.compile(r"^(?P<sid>\d+(?:\.\d+)*)\s+(?P<title>[^\n]+)$", re.MULTILINE)
    findings: List[Tuple[str, str, int]] = []
    for idx, text in enumerate(pages):
        for m in heading_re.finditer(text):
            sid = m.group("sid").strip()
            title = m.group("title").strip()
            # Avoid lines where the title is likely a page number continuation
            if re.search(r"\b(19|20)\d{2}\b", title):
                continue
            findings.append((sid, title, idx + 1))  # 1-based page
    # Deduplicate by first occurrence of each section_id
    seen = set()
    unique: List[Tuple[str, str, int]] = []
    for sid, title, page in sorted(findings, key=lambda t: (list(map(int, t[0].split('.'))), t[2])):
        if sid in seen:
            continue
        seen.add(sid)
        unique.append((sid, title, page))
    return unique


def build_sections(pages: List[str], headings: List[Tuple[str, str, int]], doc_title: str) -> List[SectionEntry]:
    entries: List[SectionEntry] = []
    num_pages = len(pages)

    # Ensure headings are sorted by page and then by numeric section id depth
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

        # Concatenate page range as a coarse content slice
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


def main() -> None:
    pdf_path = "usb_pd_spec.pdf"
    reader = PdfReader(pdf_path)

    doc_title = "USB Power Delivery Specification"
    try:
        if reader.metadata and reader.metadata.title:
            doc_title = str(reader.metadata.title)
    except Exception:
        pass

    pages = extract_all_text(reader)
    headings = find_headings(pages)
    sections = build_sections(pages, headings, doc_title)

    with open("usb_pd_spec.jsonl", "w", encoding="utf-8") as f:
        for entry in sections:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")

    print(f"✅ Wrote {len(sections)} sections to usb_pd_spec.jsonl")


if __name__ == "__main__":
    main()

