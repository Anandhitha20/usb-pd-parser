# USB Power Delivery (USB PD) Specification Parser

A comprehensive Python system for parsing USB Power Delivery specification PDFs and converting them into structured, machine-readable JSONL formats with validation reporting.

## 🎯 Project Overview

This system extracts and structures complex technical documents containing:
- **Hierarchical sections** (chapters, subsections)
- **Table of Contents** with page numbers
- **Figures and tables**
- **Protocol descriptions and state machines**

The output is optimized for:
- **Retrieval and search** operations
- **Vector store ingestion**
- **LLM-based document agents**
- **Hierarchical understanding**

## 📋 Assignment Deliverables

### ✅ Completed Components

1. **Python Scripts:**
   - `parse_toc.py` - Extracts Table of Contents from PDF
   - `parse_sections.py` - Parses all document sections with content
   - `extract_metadata.py` - Extracts document-level metadata
   - `validate_and_report.py` - Generates comprehensive validation report

2. **JSON Schemas:**
   - `schema_toc.json` - Schema for TOC entries
   - `schema_sections.json` - Schema for section entries
   - `schema_metadata.json` - Schema for metadata entries

3. **Output Files:**
   - `usb_pd_toc.jsonl` - Structured TOC hierarchy
   - `usb_pd_spec.jsonl` - All sections with content
   - `usb_pd_metadata.jsonl` - Document metadata
   - `validation_report.xlsx` - Comprehensive validation analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- USB PD specification PDF file

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd usb_pd_parser
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Place your PDF file:**
   ```bash
   # Copy your USB PD specification PDF to the project root
   # and rename it to: usb_pd_spec.pdf
   ```

### Usage

Run the scripts in sequence:

```bash
# 1. Extract Table of Contents
python parse_toc.py

# 2. Parse all document sections
python parse_sections.py

# 3. Extract document metadata
python extract_metadata.py

# 4. Generate validation report
python validate_and_report.py
```

## 📊 Output Format

### JSONL Structure (Each line = one entry)

```json
{
  "doc_title": "USB Power Delivery Specification Rev 3.1",
  "section_id": "2.1.2",
  "title": "Power Delivery Contract Negotiation",
  "page": 53,
  "level": 3,
  "parent_id": "2.1",
  "full_path": "2.1.2 Power Delivery Contract Negotiation",
  "tags": []
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `doc_title` | string | Document name/version |
| `section_id` | string | Hierarchical identifier (e.g., "2.1.2") |
| `title` | string | Section title (without numbering) |
| `page` | integer | Starting page number |
| `level` | integer | Depth level (1=chapter, 2=section, etc.) |
| `parent_id` | string/null | Immediate parent section |
| `full_path` | string | Complete section path |
| `tags` | array | Semantic labels (optional) |

## 📈 Validation Report

The `validation_report.xlsx` contains multiple sheets:

### Overview Sheet
- **TOC Total**: Number of entries in Table of Contents
- **Spec Total**: Number of sections parsed from document
- **Missing in Spec**: TOC entries not found in parsed sections
- **Extra in Spec**: Parsed sections not in TOC
- **Order Errors**: Section ordering mismatches
- **Schema Errors**: JSON validation errors

### Analysis Sheets
- **missing_in_spec**: Sections in TOC but not found in document
- **extra_in_spec**: Sections in document but not in TOC
- **order_mismatches**: Sections with incorrect ordering
- **gaps_toc**: Numeric sequence gaps in TOC
- **gaps_spec**: Numeric sequence gaps in parsed sections
- **tables**: Table count comparison (TOC vs document)

## 🔧 Configuration

### Adjusting TOC Extraction
If TOC is incomplete, modify `parse_toc.py`:
```python
# Increase scan range (default: 120 pages)
toc_text, num_pages = find_toc_text(reader, max_scan_pages=150)
```

### Adjusting Section Detection
If section parsing needs tuning, modify `parse_sections.py`:
```python
# Adjust heading regex pattern in find_headings()
heading_re = re.compile(r"^(?P<sid>\d+(?:\.\d+)*)\s+(?P<title>[^\n]+)$", re.MULTILINE)
```

## 📁 Project Structure

```
usb_pd_parser/
├── parse_toc.py              # TOC extraction script
├── parse_sections.py         # Section parsing script
├── extract_metadata.py       # Metadata extraction script
├── validate_and_report.py    # Validation and reporting script
├── schema_toc.json          # TOC JSON schema
├── schema_sections.json     # Sections JSON schema
├── schema_metadata.json     # Metadata JSON schema
├── usb_pd_toc.jsonl         # Generated TOC output
├── usb_pd_spec.jsonl        # Generated sections output
├── usb_pd_metadata.jsonl    # Generated metadata output
├── validation_report.xlsx   # Validation report
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── .gitignore             # Git ignore rules
```

## 🛠️ Technical Details

### Parsing Heuristics

1. **TOC Detection:**
   - Scans first 120 pages for TOC-like patterns
   - Uses regex: `^(\d+(?:\.\d+)*)\s+([^\n]+?)\s+(\d{1,4})$`
   - Filters out revision history entries
   - Validates page numbers against PDF bounds

2. **Section Detection:**
   - Identifies headings with numeric patterns
   - Slices content between consecutive headings
   - Maintains hierarchical relationships

3. **Validation:**
   - Compares TOC vs parsed sections
   - Detects numeric sequence gaps
   - Validates JSON schema compliance
   - Analyzes table counts

### Dependencies

- `pypdf==4.2.0` - PDF text extraction
- `jsonschema==4.22.0` - JSON validation
- `openpyxl==3.1.5` - Excel report generation

## 🐛 Troubleshooting

### Common Issues

1. **TOC Missing Entries:**
   - Increase `max_scan_pages` in `parse_toc.py`
   - Check if TOC spans multiple pages

2. **Section Parsing Errors:**
   - Adjust heading regex in `parse_sections.py`
   - Verify PDF text extraction quality

3. **Validation Report Issues:**
   - Ensure all scripts run successfully
   - Check file permissions for Excel output

### Performance Notes

- Large PDFs (>1000 pages) may take several minutes to process
- Memory usage scales with PDF size and content complexity
- Consider processing in chunks for very large documents

## 📝 License

This project is developed for educational and research purposes.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

---

**Note**: This system is designed for USB PD specification documents but can be adapted for other technical specifications with similar structure.

