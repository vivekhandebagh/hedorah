"""Vault reading utilities for Hedorah."""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class VaultReader:
    """Reads and parses notes from an Obsidian vault."""

    def __init__(self, vault_path: Path):
        """Initialize vault reader.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = vault_path

    def read_notes(self, folder: Path, limit: int = 50) -> List[Dict[str, str]]:
        """Read markdown notes from a folder.

        Args:
            folder: Folder to read notes from
            limit: Maximum number of notes to read

        Returns:
            List of dicts with 'title', 'content', 'path', 'modified' keys
        """
        notes = []

        if not folder.exists():
            return notes

        # Get all markdown files, sorted by modification time (newest first)
        md_files = sorted(
            folder.glob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        for md_file in md_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                title, body = self._parse_note(content, md_file.stem)

                notes.append({
                    'title': title,
                    'content': body,
                    'path': str(md_file),
                    'modified': datetime.fromtimestamp(md_file.stat().st_mtime).isoformat()
                })
            except Exception:
                # Skip files that can't be read
                continue

        return notes

    def _parse_note(self, content: str, filename: str) -> tuple:
        """Parse a note's content, extracting title and body.

        Args:
            content: Raw markdown content
            filename: Filename (used as fallback title)

        Returns:
            Tuple of (title, body)
        """
        lines = content.split('\n')
        title = filename
        body_start = 0

        # Check for YAML frontmatter
        if lines and lines[0].strip() == '---':
            # Find closing ---
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    # Extract title from frontmatter if present
                    frontmatter = '\n'.join(lines[1:i])
                    title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', frontmatter)
                    if title_match:
                        title = title_match.group(1).strip()
                    body_start = i + 1
                    break

        # Get body content
        body_lines = lines[body_start:]

        # If first line is a heading, use it as title
        if body_lines and body_lines[0].startswith('# '):
            title = body_lines[0][2:].strip()
            body_lines = body_lines[1:]

        body = '\n'.join(body_lines).strip()

        # Truncate very long notes
        if len(body) > 2000:
            body = body[:2000] + "..."

        return title, body

    def get_recent_notes(self, folder: Path, days: int = 30) -> List[Dict[str, str]]:
        """Get notes modified within the last N days.

        Args:
            folder: Folder to read notes from
            days: Number of days to look back

        Returns:
            List of recent notes
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        all_notes = self.read_notes(folder, limit=100)

        return [
            note for note in all_notes
            if datetime.fromisoformat(note['modified']) > cutoff
        ]

    def search_notes(self, folder: Path, query: str) -> List[Dict[str, str]]:
        """Search notes for a query string.

        Args:
            folder: Folder to search in
            query: Search query (case-insensitive)

        Returns:
            List of matching notes
        """
        all_notes = self.read_notes(folder, limit=100)
        query_lower = query.lower()

        return [
            note for note in all_notes
            if query_lower in note['title'].lower() or query_lower in note['content'].lower()
        ]
