import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from parse_sections import (
    SectionEntry, extract_all_text, find_actual_document_start,
    is_valid_section_title, find_headings, build_sections
)


class TestParseSections(unittest.TestCase):
    
    def test_find_actual_document_start(self):
        """Test document start detection."""
        # Mock pages with different content
        pages = [
            "Revision History",
            "Table of Contents",
            "List of Figures",
            "Some other content",
            "1 Overview",  # Should find this
            "2 Introduction"
        ]
        
        start_page = find_actual_document_start(pages)
        self.assertEqual(start_page, 4)  # Should find "1 Overview"
    
    def test_is_valid_section_title(self):
        """Test section title validation."""
        # Valid titles
        self.assertTrue(is_valid_section_title("Overview"))
        self.assertTrue(is_valid_section_title("Power Delivery Contract"))
        self.assertTrue(is_valid_section_title("Introduction to USB PD"))
        
        # Invalid titles (revision history)
        self.assertFalse(is_valid_section_title("1.0 Initial release"))
        self.assertFalse(is_valid_section_title("Editorial changes"))
        self.assertFalse(is_valid_section_title("Table of Contents"))
        self.assertFalse(is_valid_section_title("2024-10"))
        
        # Invalid titles (too short)
        self.assertFalse(is_valid_section_title(""))
        self.assertFalse(is_valid_section_title("A"))
        
        # Invalid titles (too many numbers)
        self.assertFalse(is_valid_section_title("123456789"))
    
    def test_find_headings(self):
        """Test heading detection."""
        pages = [
            "Revision History",
            "Table of Contents",
            "1 Overview",
            "1.1 Introduction",
            "2 Power Delivery",
            "2.1 Contract Negotiation",
            "2.1.1 Source Capabilities"
        ]
        
        headings = find_headings(pages)
        
        # Should find structured headings
        section_ids = [h[0] for h in headings]
        self.assertIn("1", section_ids)
        self.assertIn("1.1", section_ids)
        self.assertIn("2", section_ids)
        self.assertIn("2.1", section_ids)
        self.assertIn("2.1.1", section_ids)
        
        # Should not find revision history
        self.assertNotIn("1.0", section_ids)
    
    def test_build_sections(self):
        """Test section building."""
        pages = [
            "Page 1 content",
            "Page 2 content",
            "Page 3 content",
            "Page 4 content"
        ]
        
        headings = [
            ("1", "Overview", 1),
            ("1.1", "Introduction", 2),
            ("2", "Power Delivery", 3)
        ]
        
        sections = build_sections(pages, headings, "USB PD Spec")
        
        self.assertEqual(len(sections), 3)
        
        # Check first section
        first = sections[0]
        self.assertEqual(first.section_id, "1")
        self.assertEqual(first.title, "Overview")
        self.assertEqual(first.page, 1)
        self.assertEqual(first.level, 1)
        self.assertIsNone(first.parent_id)
        
        # Check subsection
        subsection = sections[1]
        self.assertEqual(subsection.section_id, "1.1")
        self.assertEqual(subsection.title, "Introduction")
        self.assertEqual(subsection.page, 2)
        self.assertEqual(subsection.level, 2)
        self.assertEqual(subsection.parent_id, "1")
    
    def test_build_sections_content_extraction(self):
        """Test content extraction for sections."""
        pages = [
            "Page 1: Overview content",
            "Page 2: Introduction content",
            "Page 3: Power Delivery content"
        ]
        
        headings = [
            ("1", "Overview", 1),
            ("2", "Power Delivery", 3)
        ]
        
        sections = build_sections(pages, headings, "USB PD Spec")
        
        # First section should have content from pages 1-2
        self.assertIn("Overview content", sections[0].content)
        self.assertIn("Introduction content", sections[0].content)
        
        # Second section should have content from page 3
        self.assertIn("Power Delivery content", sections[1].content)


class TestSectionEntry(unittest.TestCase):
    
    def test_section_entry_creation(self):
        """Test SectionEntry dataclass creation."""
        entry = SectionEntry(
            doc_title="USB PD Spec",
            section_id="2.1.2",
            title="Contract Negotiation",
            page=53,
            level=3,
            parent_id="2.1",
            full_path="2.1.2 Contract Negotiation",
            content="This is the content of the section.",
            tags=["negotiation", "contracts"]
        )
        
        self.assertEqual(entry.section_id, "2.1.2")
        self.assertEqual(entry.title, "Contract Negotiation")
        self.assertEqual(entry.page, 53)
        self.assertEqual(entry.level, 3)
        self.assertEqual(entry.parent_id, "2.1")
        self.assertEqual(entry.content, "This is the content of the section.")
        self.assertEqual(entry.tags, ["negotiation", "contracts"])


class TestIntegration(unittest.TestCase):
    
    def test_end_to_end_parsing(self):
        """Test end-to-end parsing with mock PDF."""
        # Mock PDF content
        mock_pages = [
            "Revision History",
            "Table of Contents",
            "1 Overview",
            "This is the overview content.",
            "1.1 Introduction",
            "This is the introduction content.",
            "2 Power Delivery",
            "This is the power delivery content."
        ]
        
        with patch('parse_sections.PdfReader') as mock_reader:
            # Mock the PDF reader
            mock_reader_instance = Mock()
            mock_reader_instance.pages = [Mock() for _ in range(len(mock_pages))]
            for i, page in enumerate(mock_pages):
                mock_reader_instance.pages[i].extract_text.return_value = page
            
            mock_reader.return_value = mock_reader_instance
            
            # Import and run the main function
            from parse_sections import main
            
            # Run with temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
                temp_file = f.name
            
            try:
                # Mock the PDF path
                with patch('parse_sections.pdf_path', 'mock_pdf.pdf'):
                    main()
                
                # Check if output file was created
                self.assertTrue(os.path.exists('usb_pd_spec.jsonl'))
                
                # Read and validate output
                with open('usb_pd_spec.jsonl', 'r') as f:
                    lines = f.readlines()
                
                # Should have some sections
                self.assertGreater(len(lines), 0)
                
                # Validate JSON format
                for line in lines:
                    data = json.loads(line)
                    self.assertIn('section_id', data)
                    self.assertIn('title', data)
                    self.assertIn('content', data)
                    
            finally:
                # Cleanup
                if os.path.exists('usb_pd_spec.jsonl'):
                    os.remove('usb_pd_spec.jsonl')


if __name__ == '__main__':
    unittest.main()
