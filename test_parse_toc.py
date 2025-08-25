import unittest
import json
import os
from parse_toc import TocEntry, normalize_title, infer_parent_id, parse_toc_entries


class TestParseToc(unittest.TestCase):
    
    def test_normalize_title(self):
        """Test title normalization."""
        # Test dot leader removal
        self.assertEqual(normalize_title("Title .........."), "Title")
        
        # Test excessive whitespace
        self.assertEqual(normalize_title("  Title   "), "Title")
        
        # Test mixed whitespace and dots
        self.assertEqual(normalize_title("Title . . . . ."), "Title")
        
        # Test normal title
        self.assertEqual(normalize_title("Power Delivery Contract"), "Power Delivery Contract")
    
    def test_infer_parent_id(self):
        """Test parent ID inference."""
        # Test section with parent
        self.assertEqual(infer_parent_id("2.1.2"), "2.1")
        self.assertEqual(infer_parent_id("1.3.4.5"), "1.3.4")
        
        # Test top-level section
        self.assertIsNone(infer_parent_id("1"))
        self.assertIsNone(infer_parent_id("2"))


class TestTocEntry(unittest.TestCase):
    
    def test_toc_entry_creation(self):
        """Test TocEntry dataclass creation."""
        entry = TocEntry(
            doc_title="USB PD Spec",
            section_id="2.1.2",
            title="Contract Negotiation",
            page=53,
            level=3,
            parent_id="2.1",
            full_path="2.1.2 Contract Negotiation",
            tags=["negotiation", "contracts"]
        )
        
        self.assertEqual(entry.section_id, "2.1.2")
        self.assertEqual(entry.title, "Contract Negotiation")
        self.assertEqual(entry.page, 53)
        self.assertEqual(entry.level, 3)
        self.assertEqual(entry.parent_id, "2.1")
        self.assertEqual(entry.tags, ["negotiation", "contracts"])


class TestIntegration(unittest.TestCase):
    
    def test_parse_toc_entries(self):
        """Test parsing TOC entries from text."""
        # Create mock TOC text that matches our regex pattern
        # The regex expects: section_id + title + page_number at the end
        mock_toc_text = """
        1 Overview 10
        1.1 Introduction 11
        1.2 Background 12
        2 Power Delivery 20
        2.1 Contract Negotiation 21
        2.1.1 Initial Contract 22
        """
        
        # Debug: Print what we're trying to parse
        print(f"DEBUG: Mock text: {repr(mock_toc_text)}")
        
        # Test parsing the TOC entries
        entries = parse_toc_entries(mock_toc_text, 50, "USB PD Spec")
        
        # Debug: Print what we got
        print(f"DEBUG: Found {len(entries)} entries")
        for entry in entries:
            print(f"DEBUG: Entry: {entry}")
        
        # Should have some entries
        self.assertGreater(len(entries), 0)
        
        # Validate the first entry
        first_entry = entries[0]
        self.assertEqual(first_entry.section_id, "1")
        self.assertEqual(first_entry.title, "Overview")
        self.assertEqual(first_entry.page, 10)
        self.assertEqual(first_entry.level, 1)
        self.assertIsNone(first_entry.parent_id)
        
        # Validate a subsection
        subsection = entries[1]
        self.assertEqual(subsection.section_id, "1.1")
        self.assertEqual(subsection.title, "Introduction")
        self.assertEqual(subsection.page, 11)
        self.assertEqual(subsection.level, 2)
        self.assertEqual(subsection.parent_id, "1")


if __name__ == '__main__':
    unittest.main()
