import unittest
import json
import os
from base_models import TocEntry, SectionEntry
from parse_toc import normalize_title, infer_parent_id


class TestBasicFunctionality(unittest.TestCase):
    
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
        
        # Test inherited methods
        self.assertEqual(entry.get_hierarchy_level(), 3)
        self.assertFalse(entry.is_top_level())
        self.assertEqual(entry.get_parent_section(), "2.1")
    
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
        
        # Test inherited methods
        self.assertEqual(entry.get_hierarchy_level(), 3)
        self.assertFalse(entry.is_top_level())
        self.assertEqual(entry.get_parent_section(), "2.1")
        
        # Test SectionEntry specific methods
        self.assertEqual(entry.get_content_length(), 35)
        self.assertTrue(entry.has_content())
    
    def test_inheritance_functionality(self):
        """Test that inheritance works correctly."""
        # Test TocEntry inheritance
        toc_entry = TocEntry(
            doc_title="Test Doc",
            section_id="1",
            title="Test Title",
            page=1,
            level=1,
            parent_id=None,
            full_path="1 Test Title",
            tags=[]
        )
        
        # Test SectionEntry inheritance
        section_entry = SectionEntry(
            doc_title="Test Doc",
            section_id="1.1",
            title="Test Section",
            page=2,
            level=2,
            parent_id="1",
            full_path="1.1 Test Section",
            content="Test content",
            tags=[]
        )
        
        # Both should have inherited methods
        self.assertTrue(hasattr(toc_entry, 'get_hierarchy_level'))
        self.assertTrue(hasattr(section_entry, 'get_hierarchy_level'))
        
        # SectionEntry should have additional methods
        self.assertTrue(hasattr(section_entry, 'get_content_length'))
        self.assertTrue(hasattr(section_entry, 'has_content'))
        
        # TocEntry should not have content-specific methods
        self.assertFalse(hasattr(toc_entry, 'get_content_length'))
        self.assertFalse(hasattr(toc_entry, 'has_content'))
    
    def test_json_output_format(self):
        """Test that the actual output files have correct JSON format."""
        # Check if TOC file exists and has valid JSON
        if os.path.exists('usb_pd_toc.jsonl'):
            with open('usb_pd_toc.jsonl', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Should have some entries
            self.assertGreater(len(lines), 0)
            
            # Validate JSON format
            for line in lines:
                data = json.loads(line)
                self.assertIn('section_id', data)
                self.assertIn('title', data)
                self.assertIn('page', data)
                self.assertIn('level', data)
                self.assertIn('parent_id', data)
                self.assertIn('full_path', data)
                self.assertIn('tags', data)
        
        # Check if spec file exists and has valid JSON
        if os.path.exists('usb_pd_spec.jsonl'):
            with open('usb_pd_spec.jsonl', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Should have some entries
            self.assertGreater(len(lines), 0)
            
            # Validate JSON format
            for line in lines:
                data = json.loads(line)
                self.assertIn('section_id', data)
                self.assertIn('title', data)
                self.assertIn('page', data)
                self.assertIn('level', data)
                self.assertIn('parent_id', data)
                self.assertIn('full_path', data)
                self.assertIn('content', data)
                self.assertIn('tags', data)


if __name__ == '__main__':
    unittest.main()
