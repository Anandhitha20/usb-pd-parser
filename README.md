## USB PD Specification Parsing Prototype

This prototype parses the USB Power Delivery (USB PD) specification PDF and produces structured JSONL outputs for the Table of Contents (ToC), full sections, and document metadata, and generates an XLS validation report comparing ToC vs parsed sections.

### Outputs
- `usb_pd_toc.jsonl`: ToC hierarchy with page numbers.
- `usb_pd_spec.jsonl`: All sections with content slices.
- `usb_pd_metadata.jsonl`: Document-level metadata.
- `validation_report.xlsx`: Validation summary (counts, mismatches, schema errors).

### Setup
1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv/Scripts/activate  # Windows PowerShell
pip install -r requirements.txt
```

2. Place the PDF as `usb_pd_spec.pdf` in the project root.

### Run
1. Extract ToC:
```bash
python parse_toc.py
```
2. Extract full sections:
```bash
python parse_sections.py
```
3. Extract metadata:
```bash
python extract_metadata.py
```
4. Generate validation report (XLS):
```bash
python validate_and_report.py
```

### Schemas
- `schema_toc.json`: JSON Schema for ToC entries
- `schema_sections.json`: JSON Schema for section entries
- `schema_metadata.json`: JSON Schema for metadata entry

### Notes and heuristics
- ToC detection scans the first ~50 pages and uses conservative regex with page-range validation to avoid revision history noise. Dot leaders are stripped.
- Section extraction identifies headings with `^<num>(.<num>)* <Title>$` and slices content between headings. This is a best-effort heuristic and may need adjustment per document formatting.
- The validator compares section IDs between ToC and parsed sections and writes an Excel workbook with counts, differences, and schema errors.

### Caveats
- PDF text extraction depends on the PDF’s internal structure; headings might be split or hyphenated across lines, which may require tuning regex and pre-processing.
- If the ToC spans more than the scanned pages or uses non-standard formatting, adjust scan limits and regex in `parse_toc.py` accordingly.

