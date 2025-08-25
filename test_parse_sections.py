import unittest
import json
import os
from parse_sections import SectionEntry, find_actual_document_start, is_valid_section_title, find_headings, build_sections


class TestParseSections(unittest.TestCase):
    
    def test_find_actual_document_start(self):
        """Test finding the actual document start."""
        pages = [
            "Revision History",
            "Table of Contents", 
            "List of Figures",
            "List of Tables",
            "1 Overview",
            "This is the overview content."
        ]
        
        start_page = find_actual_document_start(pages)
        self.assertEqual(start_page, 4)  # Should find "1 Overview"
    
    def test_is_valid_section_title(self):
        """Test section title validation."""
        # Valid titles
        self.assertTrue(is_valid_section_title("Overview"))
        self.assertTrue(is_valid_section_title("Power Delivery"))
        self.assertTrue(is_valid_section_title("Contract Negotiation"))
        
        # Invalid titles (revision history)
        self.assertFalse(is_valid_section_title("Revision History"))
        self.assertFalse(is_valid_section_title("Initial release"))
        self.assertFalse(is_valid_section_title("2024-10"))
    
    def test_find_headings(self):
        """Test finding section headings."""
        pages = [
            "1 Overview",
            "This is overview content.",
            "1.1 Introduction", 
            "This is introduction content.",
            "2 Power Delivery",
            "This is power delivery content."
        ]
        
        headings = find_headings(pages)
        self.assertGreater(len(headings), 0)
        
        # Check first heading
        first_heading = headings[0]
        self.assertEqual(first_heading[0], "1")  # section_id
        self.assertEqual(first_heading[1], "Overview")  # title
        self.assertEqual(first_heading[2], 1)  # page index
    
    def test_build_sections(self):
        """Test building sections from headings."""
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
    
    def test_parse_sections_functions(self):
        """Test that all required functions can be imported and called."""
        # Test that we can call the main parsing functions
        from parse_sections import extract_all_text, create_page_based_sections
        
        # Test with simple mock data (need more pages since function starts from page 5)
        mock_pages = [
            "1 Overview",
            "This is overview content.",
            "2 Power Delivery", 
            "This is power delivery content.",
            "3 Additional Content",
            "This is additional content.",
            "4 More Content",
            "This is more content.",
            "5 Test Content",
            "This is test content with enough length to pass the 50 character minimum."
        ]
        
        # Test page-based sections creation
        sections = create_page_based_sections(mock_pages, "USB PD Spec")
        self.assertGreater(len(sections), 0)
        
        # Validate first section
        first_section = sections[0]
        self.assertIsInstance(first_section, SectionEntry)
        # The first section is from page 5, so check for that content
        self.assertIn("test content", first_section.content)


if __name__ == '__main__':
    unittest.main()
