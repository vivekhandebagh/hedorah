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

        # Key Figures (with descriptions)
        if content.figures:
            md_parts.append("## Key Figures")
            for fig in content.figures:
                # Create relative path to figure
                fig_name = fig.image_path.name
                md_parts.append(f"### Figure {fig.number}")
                md_parts.append(f"![[{figures_folder}/{fig_name}]]")
                # Show description if available, otherwise caption
                if fig.description:
                    md_parts.append(f"\n{fig.description}")
                elif fig.caption:
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

    def create_insight_note(self, paper_title: str, insights: List[Dict[str, Any]],
                            note_connections: List[Dict[str, Any]] = None) -> str:
        """Create a research insight note.

        Args:
            paper_title: Title of the source paper
            insights: List of insights from Claude analysis
            note_connections: Optional connections to user's personal notes

        Returns:
            Markdown formatted note
        """
        # Generate note title
        note_title = f"Insights - {self._sanitize_filename(paper_title)}"

        frontmatter = self._create_frontmatter(
            title=note_title,
            tags=["insights", "research-notes"],
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

        # Add connections to user's personal notes
        if note_connections:
            md_parts.append("## Connections to Your Notes\n")
            for conn in note_connections:
                note_title_link = conn.get("note_title", "Unknown")
                md_parts.append(f"### [[{note_title_link}]]")
                if conn.get("connection"):
                    md_parts.append(f"{conn['connection']}\n")
                if conn.get("insight"):
                    md_parts.append(f"**Insight:** {conn['insight']}\n")

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
        exp_id = experiment.get("experiment_id", "")

        frontmatter = self._create_frontmatter(
            title=exp_title,
            tags=["experiment", "proposal"],
            source_paper=paper_title,
            experiment_id=exp_id,
            difficulty=experiment.get("difficulty", "unknown"),
            status="proposed"
        )

        md_parts = [frontmatter]
        md_parts.append(f"# {exp_title}\n")

        # Research Context
        md_parts.append("## Research Context")
        md_parts.append(f"**Source Paper:** [[{paper_title}]]")
        md_parts.append(f"**Status:** Proposed | **Difficulty:** {experiment.get('difficulty', 'N/A')} | **Est. Time:** {experiment.get('estimated_time', 'N/A')}\n")

        # Motivation
        if experiment.get("motivation"):
            md_parts.append("### Motivation")
            md_parts.append(f"{experiment['motivation']}\n")

        # Hypothesis
        if experiment.get("hypothesis"):
            md_parts.append("### Hypothesis")
            md_parts.append(f"{experiment['hypothesis']}\n")

        # Source Insights
        if experiment.get("source_insights"):
            md_parts.append("### Source Insights")
            for insight in experiment["source_insights"]:
                md_parts.append(f"- {insight}")
            md_parts.append("")

        # Experimental Design
        md_parts.append("## Experimental Design\n")

        # Objective
        if experiment.get("objective"):
            md_parts.append("### Objective")
            md_parts.append(f"{experiment['objective']}\n")

        # Variables
        variables = experiment.get("variables", {})
        if variables:
            md_parts.append("### Variables")
            md_parts.append("| Type | Variables |")
            md_parts.append("|------|-----------|")
            independent = ", ".join(variables.get("independent", [])) or "N/A"
            dependent = ", ".join(variables.get("dependent", [])) or "N/A"
            controlled = ", ".join(variables.get("controlled", [])) or "N/A"
            md_parts.append(f"| Independent (manipulate) | {independent} |")
            md_parts.append(f"| Dependent (measure) | {dependent} |")
            md_parts.append(f"| Controlled | {controlled} |")
            md_parts.append("")

        # Parameters
        parameters = experiment.get("parameters", [])
        if parameters:
            md_parts.append("## Parameters")
            md_parts.append("| Parameter | Type | Description | Default/Range |")
            md_parts.append("|-----------|------|-------------|---------------|")
            for param in parameters:
                name = param.get("name", "")
                ptype = param.get("type", "")
                desc = param.get("description", "")
                default_range = param.get("default", param.get("range", ""))
                md_parts.append(f"| {name} | {ptype} | {desc} | {default_range} |")
            md_parts.append("")

        # Procedure
        procedure = experiment.get("procedure", [])
        if procedure:
            md_parts.append("## Procedure\n")
            for i, phase in enumerate(procedure, 1):
                phase_name = phase.get("phase", f"Phase {i}")
                md_parts.append(f"### {i}. {phase_name}")
                steps = phase.get("steps", [])
                for step in steps:
                    md_parts.append(f"- [ ] {step}")

                pseudocode = phase.get("pseudocode")
                if pseudocode:
                    md_parts.append("")
                    md_parts.append("```")
                    md_parts.append(pseudocode)
                    md_parts.append("```")
                md_parts.append("")

        # Expected Results
        expected_results = experiment.get("expected_results", [])
        if expected_results:
            md_parts.append("## Expected Results")
            md_parts.append("| Result | Type | What it tells us |")
            md_parts.append("|--------|------|------------------|")
            for result in expected_results:
                name = result.get("name", "")
                rtype = result.get("type", "")
                desc = result.get("description", "")
                md_parts.append(f"| {name} | {rtype} | {desc} |")
            md_parts.append("")

        # Implementation Notes
        md_parts.append("## Implementation Notes")
        suggested_tools = experiment.get("suggested_tools", [])
        if suggested_tools:
            md_parts.append(f"**Suggested Tools:** {', '.join(suggested_tools)}")

        prerequisites = experiment.get("prerequisites", [])
        if prerequisites:
            md_parts.append(f"**Prerequisites:** {', '.join(prerequisites)}")

        md_parts.append("")
        md_parts.append("---")
        md_parts.append("*Implementation notes and results go below*\n")

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
