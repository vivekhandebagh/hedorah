"""Obsidian markdown generation for vault integration."""

import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from .pdf_processor import PDFContent


class ObsidianFormatter:
    """Formats content as Obsidian-compatible markdown."""

    def __init__(self, vault_path: Path):
        """Initialize Obsidian formatter.

        Args:
            vault_path: Path to the Obsidian vault
        """
        self.vault_path = vault_path

    def create_paper_note(self, content: PDFContent, summary: Dict[str, Any],
                          figures_folder: str = "attachments") -> str:
        """Create a paper summary note in Obsidian format.

        Args:
            content: Extracted PDF content
            summary: Summary from local LLM
            figures_folder: Folder name for attachments

        Returns:
            Markdown formatted note
        """
        # Create frontmatter
        frontmatter = self._create_frontmatter(
            title=content.title,
            authors=content.authors,
            tags=summary.get("tags", []) + ["paper", "ai-interpretability"],
            paper_type="research-paper"
        )

        # Build markdown content
        md_parts = [frontmatter]

        # Title
        md_parts.append(f"# {content.title}\n")

        # Metadata section
        md_parts.append("## Metadata")
        md_parts.append(f"**Authors:** {', '.join(content.authors)}")
        md_parts.append(f"**Pages:** {content.metadata.get('page_count', 'N/A')}")
        md_parts.append(f"**Added:** {datetime.now().strftime('%Y-%m-%d')}\n")

        # Abstract
        if content.abstract:
            md_parts.append("## Abstract")
            md_parts.append(f"{content.abstract}\n")

        # Core claims
        if summary.get("core_claims"):
            md_parts.append("## Core Claims")
            for claim in summary["core_claims"]:
                md_parts.append(f"- {claim}")
            md_parts.append("")

        # Methodology
        if summary.get("methodology"):
            md_parts.append("## Methodology")
            methodology = summary["methodology"]

            if methodology.get("approach"):
                md_parts.append(f"**Approach:** {methodology['approach']}\n")

            if methodology.get("key_techniques"):
                md_parts.append("**Key Techniques:**")
                for technique in methodology["key_techniques"]:
                    md_parts.append(f"- {technique}")
                md_parts.append("")

            if methodology.get("datasets"):
                md_parts.append("**Datasets:**")
                for dataset in methodology["datasets"]:
                    md_parts.append(f"- {dataset}")
                md_parts.append("")

        # Key terminology
        if summary.get("key_terminology"):
            md_parts.append("## Key Terminology")
            for term, definition in summary["key_terminology"].items():
                # Create wikilink for the term
                md_parts.append(f"- **[[{term}]]**: {definition}")
            md_parts.append("")

        # Limitations
        if summary.get("limitations"):
            md_parts.append("## Limitations & Critiques")
            for limitation in summary["limitations"]:
                md_parts.append(f"- {limitation}")
            md_parts.append("")

        # Figures
        if content.figures:
            md_parts.append("## Figures")
            for fig in content.figures:
                # Create relative path to figure
                fig_name = fig.image_path.name
                md_parts.append(f"### Figure {fig.number}")
                md_parts.append(f"![[{figures_folder}/{fig_name}]]")
                if fig.caption:
                    md_parts.append(f"*{fig.caption}*")
                md_parts.append("")

        # Equations (sample)
        if content.equations and len(content.equations) <= 10:
            md_parts.append("## Key Equations")
            for eq in content.equations[:10]:
                md_parts.append(f"$${eq.latex}$$")
                if eq.context:
                    md_parts.append(f"*Context: {eq.context[:100]}...*")
                md_parts.append("")

        return "\n".join(md_parts)

    def create_insight_note(self, paper_title: str, insights: List[Dict[str, Any]]) -> str:
        """Create a research insight note.

        Args:
            paper_title: Title of the source paper
            insights: List of insights from Claude analysis

        Returns:
            Markdown formatted note
        """
        # Generate note title
        note_title = f"Insights - {self._sanitize_filename(paper_title)}"

        frontmatter = self._create_frontmatter(
            title=note_title,
            tags=["insights", "research-notes", "ai-interpretability"],
            source_paper=paper_title
        )

        md_parts = [frontmatter]
        md_parts.append(f"# {note_title}\n")
        md_parts.append(f"**Source:** [[{paper_title}]]\n")

        for i, insight in enumerate(insights, 1):
            md_parts.append(f"## Insight {i}: {insight.get('insight', 'Untitled')}")
            md_parts.append(f"\n{insight.get('insight', '')}\n")

            if insight.get("significance"):
                md_parts.append(f"**Significance:** {insight['significance']}\n")

            if insight.get("connections"):
                md_parts.append("**Connections:**")
                for connection in insight["connections"]:
                    # Create wikilinks for connections
                    md_parts.append(f"- [[{connection}]]")
                md_parts.append("")

        return "\n".join(md_parts)

    def create_experiment_note(self, paper_title: str, experiment: Dict[str, Any]) -> str:
        """Create an experiment proposal note.

        Args:
            paper_title: Title of the source paper
            experiment: Experiment data from Claude

        Returns:
            Markdown formatted note
        """
        exp_title = experiment.get("title", "Untitled Experiment")

        frontmatter = self._create_frontmatter(
            title=exp_title,
            tags=["experiment", "proposal", "ai-interpretability"],
            source_paper=paper_title,
            difficulty=experiment.get("difficulty", "unknown"),
            status="proposed"
        )

        md_parts = [frontmatter]
        md_parts.append(f"# {exp_title}\n")
        md_parts.append(f"**Source Paper:** [[{paper_title}]]")
        md_parts.append(f"**Difficulty:** {experiment.get('difficulty', 'N/A')}")
        md_parts.append(f"**Estimated Time:** {experiment.get('estimated_time', 'N/A')}")
        md_parts.append(f"**Status:** 🔵 Proposed\n")

        # Motivation
        if experiment.get("motivation"):
            md_parts.append("## Motivation")
            md_parts.append(f"{experiment['motivation']}\n")

        # Hypothesis
        if experiment.get("hypothesis"):
            md_parts.append("## Hypothesis")
            md_parts.append(f"{experiment['hypothesis']}\n")

        # Methodology
        if experiment.get("methodology"):
            md_parts.append("## Methodology")
            methodology = experiment["methodology"]

            if methodology.get("approach"):
                md_parts.append(f"**Approach:** {methodology['approach']}\n")

            if methodology.get("steps"):
                md_parts.append("**Steps:**")
                for j, step in enumerate(methodology["steps"], 1):
                    md_parts.append(f"{j}. {step}")
                md_parts.append("")

            if methodology.get("required_resources"):
                md_parts.append("**Required Resources:**")
                for resource in methodology["required_resources"]:
                    md_parts.append(f"- {resource}")
                md_parts.append("")

        # Expected outcomes
        if experiment.get("expected_outcomes"):
            md_parts.append("## Expected Outcomes")
            outcomes = experiment["expected_outcomes"]

            if outcomes.get("success_criteria"):
                md_parts.append(f"**Success Criteria:** {outcomes['success_criteria']}\n")

            if outcomes.get("potential_findings"):
                md_parts.append("**Potential Findings:**")
                for finding in outcomes["potential_findings"]:
                    md_parts.append(f"- {finding}")
                md_parts.append("")

            if outcomes.get("implications"):
                md_parts.append(f"**Implications:** {outcomes['implications']}\n")

        # Notes section for user
        md_parts.append("## Implementation Notes")
        md_parts.append("*Add your notes and progress updates here*\n")

        return "\n".join(md_parts)

    def create_connections_note(self, paper_title: str, connections: List[Dict[str, Any]]) -> str:
        """Create a note documenting conceptual connections.

        Args:
            paper_title: Title of the source paper
            connections: List of connections from analysis

        Returns:
            Markdown formatted note
        """
        note_title = f"Connections - {self._sanitize_filename(paper_title)}"

        frontmatter = self._create_frontmatter(
            title=note_title,
            tags=["connections", "research-graph", "ai-interpretability"],
            source_paper=paper_title
        )

        md_parts = [frontmatter]
        md_parts.append(f"# {note_title}\n")
        md_parts.append(f"**Source:** [[{paper_title}]]\n")

        for connection in connections:
            concept = connection.get("concept", "Unknown")
            md_parts.append(f"## [[{concept}]]")

            if connection.get("related_to"):
                md_parts.append("**Related to:**")
                for related in connection["related_to"]:
                    md_parts.append(f"- [[{related}]]")
                md_parts.append("")

            if connection.get("relationship"):
                md_parts.append(f"{connection['relationship']}\n")

        return "\n".join(md_parts)

    def _create_frontmatter(self, title: str, tags: List[str], **kwargs) -> str:
        """Create YAML frontmatter for Obsidian note.

        Args:
            title: Note title
            tags: List of tags
            **kwargs: Additional metadata fields

        Returns:
            YAML frontmatter string
        """
        lines = ["---"]
        lines.append(f'title: "{title}"')
        lines.append(f"created: {datetime.now().isoformat()}")

        if tags:
            lines.append("tags:")
            for tag in tags:
                lines.append(f"  - {tag}")

        for key, value in kwargs.items():
            if isinstance(value, str):
                lines.append(f'{key}: "{value}"')
            else:
                lines.append(f"{key}: {value}")

        lines.append("---\n")
        return "\n".join(lines)

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use as filename.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        # Remove or replace invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces with hyphens
        text = re.sub(r'\s+', '-', text)
        # Limit length
        return text[:100]
