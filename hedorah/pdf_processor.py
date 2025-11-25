"""PDF processing module for extracting text, figures, equations, and citations."""

import re
import pymupdf
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class Citation:
    """Represents a citation found in the paper."""
    text: str
    context: str  # Surrounding text for context
    page: int


@dataclass
class Figure:
    """Represents an extracted figure/diagram."""
    number: int
    caption: str
    image_path: Path
    page: int
    width: int = 0
    height: int = 0
    description: str = ""  # LLM-generated description


@dataclass
class Equation:
    """Represents an equation found in the paper."""
    latex: str
    context: str
    page: int


@dataclass
class PDFContent:
    """Structured content extracted from a PDF."""
    title: str
    authors: List[str]
    abstract: str
    full_text: str
    sections: Dict[str, str]  # section_title -> content
    figures: List[Figure] = field(default_factory=list)
    equations: List[Equation] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PDFProcessor:
    """Processes PDF files to extract structured content."""

    # Minimum image dimensions to consider (skip icons, logos, etc.)
    MIN_IMAGE_WIDTH = 200
    MIN_IMAGE_HEIGHT = 200

    def __init__(self, extract_figures: bool = True,
                 extract_equations: bool = True,
                 extract_citations: bool = True,
                 max_figures: int = 2):
        """Initialize PDF processor.

        Args:
            extract_figures: Whether to extract figures and diagrams
            extract_equations: Whether to extract equations
            extract_citations: Whether to extract citations
            max_figures: Maximum number of figures to extract (default 2)
        """
        self.extract_figures = extract_figures
        self.extract_equations = extract_equations
        self.extract_citations = extract_citations
        self.max_figures = max_figures

    def process(self, pdf_path: Path, output_dir: Path = None) -> PDFContent:
        """Process a PDF file and extract all content.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save extracted figures (optional)

        Returns:
            Structured PDF content
        """
        doc = pymupdf.open(pdf_path)

        # Extract text and structure
        full_text = self._extract_text(doc)
        sections = self._extract_sections(full_text)

        # Extract metadata
        title, authors, abstract = self._extract_metadata(doc, full_text)

        # Create content object
        content = PDFContent(
            title=title,
            authors=authors,
            abstract=abstract,
            full_text=full_text,
            sections=sections,
            metadata={
                'page_count': len(doc),
                'pdf_metadata': doc.metadata,
            }
        )

        # Extract figures if enabled
        if self.extract_figures and output_dir:
            content.figures = self._extract_figures(doc, output_dir)

        # Extract equations if enabled
        if self.extract_equations:
            content.equations = self._extract_equations(full_text, doc)

        # Extract citations if enabled
        if self.extract_citations:
            content.citations = self._extract_citations(full_text, doc)

        doc.close()
        return content

    def _extract_text(self, doc: pymupdf.Document) -> str:
        """Extract all text from the document.

        Args:
            doc: PyMuPDF document

        Returns:
            Full text content
        """
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        return "\n".join(text_parts)

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from the text.

        Args:
            text: Full text content

        Returns:
            Dictionary mapping section titles to content
        """
        sections = {}

        # Common academic paper sections
        section_patterns = [
            r'\n\s*(\d+\.?\s+)?Abstract\s*\n',
            r'\n\s*(\d+\.?\s+)?Introduction\s*\n',
            r'\n\s*(\d+\.?\s+)?Related Work\s*\n',
            r'\n\s*(\d+\.?\s+)?Background\s*\n',
            r'\n\s*(\d+\.?\s+)?Methodology\s*\n',
            r'\n\s*(\d+\.?\s+)?Methods\s*\n',
            r'\n\s*(\d+\.?\s+)?Experiments?\s*\n',
            r'\n\s*(\d+\.?\s+)?Results\s*\n',
            r'\n\s*(\d+\.?\s+)?Discussion\s*\n',
            r'\n\s*(\d+\.?\s+)?Conclusion\s*\n',
            r'\n\s*(\d+\.?\s+)?References\s*\n',
        ]

        # Find all section headers
        section_matches = []
        for pattern in section_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                section_name = match.group(0).strip()
                # Clean up section name
                section_name = re.sub(r'^\d+\.?\s*', '', section_name)
                section_matches.append((match.start(), section_name))

        # Sort by position
        section_matches.sort(key=lambda x: x[0])

        # Extract section content
        for i, (start, name) in enumerate(section_matches):
            if i < len(section_matches) - 1:
                end = section_matches[i + 1][0]
                sections[name] = text[start:end].strip()
            else:
                sections[name] = text[start:].strip()

        return sections

    def _extract_metadata(self, doc: pymupdf.Document, text: str) -> Tuple[str, List[str], str]:
        """Extract title, authors, and abstract from the document.

        Args:
            doc: PyMuPDF document
            text: Full text content

        Returns:
            Tuple of (title, authors, abstract)
        """
        # Try to get title from metadata first
        title = doc.metadata.get('title', '')

        # If not in metadata, try to extract from first page
        if not title:
            first_page_text = doc[0].get_text()
            lines = first_page_text.split('\n')
            # Assume title is one of the first few non-empty lines
            for line in lines[:10]:
                if len(line.strip()) > 10:
                    title = line.strip()
                    break

        # Extract authors (basic heuristic)
        authors = []
        author_match = doc.metadata.get('author', '')
        if author_match:
            authors = [a.strip() for a in author_match.split(',')]

        # Extract abstract
        abstract = ''
        abstract_match = re.search(
            r'Abstract\s*\n\s*(.*?)\n\s*(?:\d+\.?\s+)?(?:Introduction|Keywords)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            abstract = abstract_match.group(1).strip()

        return title, authors, abstract

    def _extract_figures(self, doc: pymupdf.Document, output_dir: Path) -> List[Figure]:
        """Extract figures and diagrams from the document.

        Filters out small images (icons, logos) and limits to max_figures.
        Prioritizes images with captions and larger dimensions.

        Args:
            doc: PyMuPDF document
            output_dir: Directory to save extracted images

        Returns:
            List of extracted figures (up to max_figures)
        """
        candidates = []
        output_dir.mkdir(parents=True, exist_ok=True)

        for page_num, page in enumerate(doc, start=1):
            # Get images from the page
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]

                try:
                    # Extract image
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    width = base_image.get("width", 0)
                    height = base_image.get("height", 0)

                    # Skip small images (icons, logos, decorations)
                    if width < self.MIN_IMAGE_WIDTH or height < self.MIN_IMAGE_HEIGHT:
                        continue

                    # Try to find caption
                    caption = self._find_figure_caption(page.get_text(), img_index + 1)

                    # Calculate priority score (prefer larger images with captions)
                    area = width * height
                    has_caption = 1 if caption else 0
                    priority_score = area + (has_caption * 500000)  # Bonus for having caption

                    candidates.append({
                        "image_bytes": image_bytes,
                        "image_ext": image_ext,
                        "width": width,
                        "height": height,
                        "caption": caption,
                        "page": page_num,
                        "priority": priority_score
                    })
                except Exception:
                    # Skip images that can't be extracted
                    continue

        # Sort by priority (highest first) and take top max_figures
        candidates.sort(key=lambda x: x["priority"], reverse=True)
        selected = candidates[:self.max_figures]

        # Save selected figures
        figures = []
        for i, candidate in enumerate(selected, start=1):
            image_filename = f"figure_{i}.{candidate['image_ext']}"
            image_path = output_dir / image_filename

            with open(image_path, "wb") as img_file:
                img_file.write(candidate["image_bytes"])

            figures.append(Figure(
                number=i,
                caption=candidate["caption"],
                image_path=image_path,
                page=candidate["page"],
                width=candidate["width"],
                height=candidate["height"]
            ))

        return figures

    def _find_figure_caption(self, page_text: str, fig_num: int) -> str:
        """Find caption for a figure.

        Args:
            page_text: Text from the page
            fig_num: Figure number on the page

        Returns:
            Caption text if found, empty string otherwise
        """
        # Look for "Figure X:" or "Fig X:" patterns
        caption_pattern = rf'(?:Figure|Fig\.?)\s*{fig_num}[:\s]+(.*?)(?:\n\n|\n(?:Figure|Fig\.?)\s*\d+)'
        match = re.search(caption_pattern, page_text, re.IGNORECASE | re.DOTALL)

        if match:
            return match.group(1).strip()
        return ""

    def _extract_equations(self, text: str, doc: pymupdf.Document) -> List[Equation]:
        """Extract equations from the document.

        Args:
            text: Full text content
            doc: PyMuPDF document

        Returns:
            List of extracted equations
        """
        equations = []

        # Look for LaTeX-style equations
        # Pattern 1: Display equations with $$ ... $$
        for match in re.finditer(r'\$\$(.*?)\$\$', text, re.DOTALL):
            latex = match.group(1).strip()
            context = self._get_context(text, match.start(), match.end())
            page = self._find_page_number(doc, match.start(), text)

            equations.append(Equation(
                latex=latex,
                context=context,
                page=page
            ))

        # Pattern 2: Inline equations with $ ... $
        for match in re.finditer(r'\$(.*?)\$', text):
            latex = match.group(1).strip()
            # Skip if it's just a dollar amount
            if not re.match(r'^\d+(?:\.\d+)?$', latex):
                context = self._get_context(text, match.start(), match.end())
                page = self._find_page_number(doc, match.start(), text)

                equations.append(Equation(
                    latex=latex,
                    context=context,
                    page=page
                ))

        return equations

    def _extract_citations(self, text: str, doc: pymupdf.Document) -> List[Citation]:
        """Extract citations from the document.

        Args:
            text: Full text content
            doc: PyMuPDF document

        Returns:
            List of extracted citations
        """
        citations = []

        # Pattern 1: [Author, Year] format
        for match in re.finditer(r'\[([A-Z][a-z]+(?:\s+et\s+al\.?)?,\s*\d{4})\]', text):
            citation_text = match.group(1)
            context = self._get_context(text, match.start(), match.end())
            page = self._find_page_number(doc, match.start(), text)

            citations.append(Citation(
                text=citation_text,
                context=context,
                page=page
            ))

        # Pattern 2: [Number] format
        for match in re.finditer(r'\[(\d+)\]', text):
            citation_text = match.group(1)
            context = self._get_context(text, match.start(), match.end())
            page = self._find_page_number(doc, match.start(), text)

            citations.append(Citation(
                text=f"[{citation_text}]",
                context=context,
                page=page
            ))

        return citations

    def _get_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Get surrounding context for a match.

        Args:
            text: Full text
            start: Start position of match
            end: End position of match
            window: Number of characters before/after to include

        Returns:
            Context string
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()

    def _find_page_number(self, doc: pymupdf.Document, position: int, full_text: str) -> int:
        """Find which page a text position corresponds to.

        Args:
            doc: PyMuPDF document
            position: Character position in full text
            full_text: Full text content

        Returns:
            Page number (1-indexed)
        """
        # Simple approximation: divide position by average chars per page
        avg_chars_per_page = len(full_text) / len(doc)
        page = int(position / avg_chars_per_page) + 1
        return min(page, len(doc))
