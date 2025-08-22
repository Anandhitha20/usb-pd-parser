"""Base models for document parsing to reduce code duplication through inheritance."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class BaseEntry:
    """Base class for document entries to reduce code duplication.
    
    This class contains common attributes shared between TOC entries
    and section entries, promoting code reuse through inheritance.
    
    Attributes:
        doc_title: The title of the document
        section_id: Hierarchical section identifier (e.g., "2.1.2")
        title: Section title without numbering
        page: Starting page number of the section
        level: Depth level (chapter = 1, section = 2, etc.)
        parent_id: Immediate parent section (null for top level)
        full_path: Concatenation of section_id and title
        tags: Optional semantic labels
    """
    doc_title: str
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    tags: List[str]
    
    def get_hierarchy_level(self) -> int:
        """Get the hierarchy level based on section ID.
        
        Returns:
            The depth level of this entry in the document hierarchy
        """
        return self.section_id.count(".") + 1
    
    def is_top_level(self) -> bool:
        """Check if this entry is at the top level of the hierarchy.
        
        Returns:
            True if this is a top-level entry (no parent), False otherwise
        """
        return self.parent_id is None
    
    def get_parent_section(self) -> Optional[str]:
        """Get the parent section ID.
        
        Returns:
            Parent section ID or None if this is a top-level entry
        """
        return self.parent_id


@dataclass
class TocEntry(BaseEntry):
    """Represents a single entry in the Table of Contents.
    
    Inherits from BaseEntry to reuse common attributes and methods.
    TOC entries represent the table of contents structure without content.
    """
    pass


@dataclass
class SectionEntry(BaseEntry):
    """Represents a single section entry from the document.
    
    Inherits from BaseEntry to reuse common attributes and methods.
    Section entries include the actual content of each section.
    
    Attributes:
        content: The actual content text of the section
    """
    content: str
    
    def get_content_length(self) -> int:
        """Get the length of the section content.
        
        Returns:
            Number of characters in the content
        """
        return len(self.content)
    
    def has_content(self) -> bool:
        """Check if the section has meaningful content.
        
        Returns:
            True if content exists and is not empty, False otherwise
        """
        return bool(self.content.strip())
