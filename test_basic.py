import unittest
import json
import os
from parse_toc import TocEntry, normalize_title, infer_parent_id


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
