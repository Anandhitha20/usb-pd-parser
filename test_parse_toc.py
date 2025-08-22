import unittest
import json
import tempfile
import os
from unittest.mock import Mock, patch
from parse_toc import TocEntry, normalize_title, infer_parent_id


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
    
    def test_end_to_end_parsing(self):
        """Test end-to-end parsing with mock PDF."""
        with patch('parse_toc.PdfReader') as mock_reader:
            # Mock the PDF reader
            mock_reader_instance = Mock()
            mock_reader_instance.pages = [Mock() for _ in range(10)]
            
            # Mock page content with TOC-like text
            toc_content = """
            1 Overview 10
            1.1 Introduction 11
            2 Power Delivery 20
            """
            
            for i in range(10):
                mock_reader_instance.pages[i].extract_text.return_value = toc_content if i < 5 else ""
            
            mock_reader.return_value = mock_reader_instance
            
            # Import and run the main function
            from parse_toc import main
            
            try:
                # Run the main function
                main()
                
                # Check if output file was created
                self.assertTrue(os.path.exists('usb_pd_toc.jsonl'))
                
                # Read and validate output
                with open('usb_pd_toc.jsonl', 'r') as f:
                    lines = f.readlines()
                
                # Should have some entries
                self.assertGreater(len(lines), 0)
                
                # Validate JSON format
                for line in lines:
                    data = json.loads(line)
                    self.assertIn('section_id', data)
                    self.assertIn('title', data)
                    self.assertIn('page', data)
                    
            finally:
                # Cleanup
                if os.path.exists('usb_pd_toc.jsonl'):
                    os.remove('usb_pd_toc.jsonl')


if __name__ == '__main__':
    unittest.main()
