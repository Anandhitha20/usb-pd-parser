import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

from jsonschema import Draft7Validator
from openpyxl import Workbook
from datetime import datetime
import re
from pypdf import PdfReader


@dataclass
class Counts:
    toc_total: int
    spec_total: int
    missing_in_spec: int
    extra_in_spec: int
    order_errors: int


def read_jsonl(path: str) -> List[dict]:
    rows: List[dict] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def validate_rows(rows: List[dict], schema_path: str) -> List[Tuple[int, str]]:
    schema = json.load(open(schema_path, "r", encoding="utf-8"))
    validator = Draft7Validator(schema)
    errors: List[Tuple[int, str]] = []
    for idx, row in enumerate(rows):
        for error in validator.iter_errors(row):
            errors.append((idx, error.message))
    return errors


def compare_toc_vs_spec(toc_rows: List[dict], spec_rows: List[dict]) -> Tuple[
    Counts, List[str], List[str], List[str]
]:
    toc_ids = [r["section_id"] for r in toc_rows]
    spec_ids = [r["section_id"] for r in spec_rows]

    toc_set = set(toc_ids)
    spec_set = set(spec_ids)

    missing = sorted(list(toc_set - spec_set))
    extra = sorted(list(spec_set - toc_set))

    # Order mismatches: compare common prefix order
    common = [sid for sid in toc_ids if sid in spec_set]
    spec_order_index: Dict[str, int] = {
        sid: i for i, sid in enumerate(spec_ids)
    }
    order_mismatches = []
    last_index = -1
    for sid in common:
        idx = spec_order_index[sid]
        if idx < last_index:
            order_mismatches.append(sid)
        last_index = idx

    counts = Counts(
        toc_total=len(toc_ids),
        spec_total=len(spec_ids),
        missing_in_spec=len(missing),
        extra_in_spec=len(extra),
        order_errors=len(order_mismatches),
    )
    return counts, missing, extra, order_mismatches


def group_sections_by_parent(section_ids: List[str]) -> Dict[str, List[str]]:
    """Group section IDs by their parent."""
    by_parent: Dict[str, List[str]] = {}
    for sid in section_ids:
        parent = ".".join(sid.split(".")[:-1]) if "." in sid else "<root>"
        by_parent.setdefault(parent, []).append(sid)
    return by_parent


def get_numeric_last_component(section_id: str) -> int:
    """Extract the numeric last component of a section ID."""
    try:
        return int(section_id.split(".")[-1])
    except ValueError:
        return -1


def find_missing_numbers_in_sequence(nums: List[int]) -> List[int]:
    """Find missing numbers in a sequence."""
    if not nums:
        return []
    expected = list(range(nums[0], nums[-1] + 1))
    return [n for n in expected if n not in nums]


def detect_gaps(section_ids: List[str]) -> List[Tuple[str, str]]:
    """Detect numeric gaps among siblings.
    
    Returns a list of (parent_id, gap_description) that specifies missing numbers,
    e.g., ("2.1", "missing: 2.1.3, 2.1.5")
    """
    by_parent = group_sections_by_parent(section_ids)
    gaps: List[Tuple[str, str]] = []

    for parent, children in by_parent.items():
        # Only consider same-depth children
        depth = len(children[0].split(".")) if children else 0
        same_depth = [c for c in children if len(c.split(".")) == depth]
        
        if len(same_depth) < 2:
            continue
            
        # Sort by numeric last component
        same_depth.sort(key=get_numeric_last_component)
        nums = [
            get_numeric_last_component(s) for s in same_depth 
            if get_numeric_last_component(s) >= 0
        ]
        
        if not nums:
            continue
            
        missing_nums = find_missing_numbers_in_sequence(nums)
        if missing_nums:
            missing_ids = [
                f"{parent}.{n}" if parent != "<root>" else str(n) 
                for n in missing_nums
            ]
            gaps.append((
                parent if parent != "<root>" else "<top-level>", 
                ", ".join(missing_ids)
            ))
    
    return gaps


def extract_list_of_tables_text(reader: PdfReader, max_scan_pages: int = 120) -> str:
    text_parts: List[str] = []
    for i in range(min(max_scan_pages, len(reader.pages))):
        text_parts.append(reader.pages[i].extract_text() or "")
    return "\n".join(text_parts)


def parse_tables_from_list(front_text: str) -> List[str]:
    """Parse 'List of Tables' style entries into table IDs.

    Heuristic matches labels like 'Table 6-1', 'Table 2-10', 
    possibly followed by title and page.
    """
    ids: List[str] = []
    # Capture at line start for more precision
    pattern = re.compile(
        r"^Table\s+(\d+-\d+)[^\n]*?(?:\s+\d+)?\s*$", 
        re.MULTILINE
    )
    for m in pattern.finditer(front_text):
        ids.append(m.group(1))
    # Deduplicate preserving order
    seen = set()
    uniq: List[str] = []
    for t in ids:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def scan_tables_in_document(reader: PdfReader) -> List[str]:
    """Scan entire PDF text for 'Table X-Y' labels and return unique IDs."""
    found: List[str] = []
    pattern = re.compile(
        r"^Table\s+(\d+-\d+)[^\n]*$", 
        re.MULTILINE
    )
    for i in range(len(reader.pages)):
        text = reader.pages[i].extract_text() or ""
        for m in pattern.finditer(text):
            found.append(m.group(1))
    # Deduplicate preserving order
    seen = set()
    uniq: List[str] = []
    for t in found:
        if t in seen:
            continue
        seen.add(t)
        uniq.append(t)
    return uniq


def create_overview_sheet(wb: Workbook, counts: Counts, errors_toc: List, errors_spec: List) -> None:
    """Create the overview sheet with summary statistics."""
    ws_overview = wb.active
    ws_overview.title = "overview"
    ws_overview.append([
        "toc_total",
        "spec_total",
        "missing_in_spec",
        "extra_in_spec",
        "order_errors",
        "toc_schema_errors",
        "spec_schema_errors",
    ])
    ws_overview.append([
        counts.toc_total,
        counts.spec_total,
        counts.missing_in_spec,
        counts.extra_in_spec,
        counts.order_errors,
        len(errors_toc),
        len(errors_spec),
    ])


def create_analysis_sheets(
    wb: Workbook, missing: List[str], extra: List[str], 
    order_mismatches: List[str], toc_gaps: List[Tuple], 
    spec_gaps: List[Tuple]
) -> None:
    """Create analysis sheets for different types of issues."""
    # Missing sections
    ws_missing = wb.create_sheet("missing_in_spec")
    ws_missing.append(["missing_in_spec"])
    for sid in missing:
        ws_missing.append([sid])

    # Extra sections
    ws_extra = wb.create_sheet("extra_in_spec")
    ws_extra.append(["extra_in_spec"])
    for sid in extra:
        ws_extra.append([sid])

    # Order mismatches
    ws_order = wb.create_sheet("order_mismatches")
    ws_order.append(["order_mismatches"])
    for sid in order_mismatches:
        ws_order.append([sid])

    # TOC gaps
    ws_gaps_toc = wb.create_sheet("gaps_toc")
    ws_gaps_toc.append(["parent_id", "missing_children"])
    for parent, missing_list in toc_gaps:
        ws_gaps_toc.append([parent, missing_list])

    # Spec gaps
    ws_gaps_spec = wb.create_sheet("gaps_spec")
    ws_gaps_spec.append(["parent_id", "missing_children"])
    for parent, missing_list in spec_gaps:
        ws_gaps_spec.append([parent, missing_list])


def create_error_sheets(wb: Workbook, errors_toc: List, errors_spec: List) -> None:
    """Create sheets for schema validation errors."""
    if errors_toc:
        ws_toc_err = wb.create_sheet("toc_schema_errors")
        ws_toc_err.append(["row_index", "error"]) 
        for idx, msg in errors_toc:
            ws_toc_err.append([idx, msg])
    if errors_spec:
        ws_spec_err = wb.create_sheet("spec_schema_errors")
        ws_spec_err.append(["row_index", "error"]) 
        for idx, msg in errors_spec:
            ws_spec_err.append([idx, msg])


def create_table_analysis_sheet(
    wb: Workbook, toc_table_ids: List[str], 
    doc_table_ids: List[str]
) -> None:
    """Create sheet for table count analysis."""
    ws_tables = wb.create_sheet("tables")
    ws_tables.append(["metric", "value"]) 
    ws_tables.append(["toc_tables_count", len(toc_table_ids)])
    ws_tables.append(["parsed_tables_count", len(doc_table_ids)])
    
    # Differences
    toc_table_set = set(toc_table_ids)
    doc_table_set = set(doc_table_ids)
    missing_tables = [t for t in toc_table_ids if t not in doc_table_set]
    extra_tables = [t for t in doc_table_ids if t not in toc_table_set]
    ws_tables.append(["missing_tables", ", ".join(missing_tables)])
    ws_tables.append(["extra_tables", ", ".join(extra_tables)])


def main() -> None:
    """Main function to run the validation and generate report."""
    # Read input files
    toc_rows = read_jsonl("usb_pd_toc.jsonl")
    spec_rows = read_jsonl("usb_pd_spec.jsonl")

    # Validate schemas
    errors_toc = validate_rows(toc_rows, "schema_toc.json")
    errors_spec = validate_rows(spec_rows, "schema_sections.json")

    # Compare TOC vs spec
    counts, missing, extra, order_mismatches = compare_toc_vs_spec(toc_rows, spec_rows)

    # Gap detection
    toc_gaps = detect_gaps([r["section_id"] for r in toc_rows])
    spec_gaps = detect_gaps([r["section_id"] for r in spec_rows])

    # Table analysis
    reader = PdfReader("usb_pd_spec.pdf")
    front_text = extract_list_of_tables_text(reader)
    toc_table_ids = parse_tables_from_list(front_text)
    doc_table_ids = scan_tables_in_document(reader)

    # Create workbook
    wb = Workbook()
    
    # Create sheets
    create_overview_sheet(wb, counts, errors_toc, errors_spec)
    create_analysis_sheets(wb, missing, extra, order_mismatches, toc_gaps, spec_gaps)
    create_error_sheets(wb, errors_toc, errors_spec)
    create_table_analysis_sheet(wb, toc_table_ids, doc_table_ids)

    # Save workbook
    def save_workbook_with_fallback(workbook: Workbook, primary_path: str) -> str:
        try:
            workbook.save(primary_path)
            return primary_path
        except PermissionError:
            alt = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            workbook.save(alt)
            return alt

    output_path = save_workbook_with_fallback(wb, "validation_report.xlsx")
    print(f"✅ Wrote {output_path}")


if __name__ == "__main__":
    main()

