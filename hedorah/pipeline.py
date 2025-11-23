"""Main processing pipeline for Hedorah."""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .config import Config
from .pdf_processor import PDFProcessor, PDFContent
from .llm import OllamaClient, ClaudeClient
from .obsidian import ObsidianFormatter

logger = logging.getLogger(__name__)


class HedorahPipeline:
    """Main pipeline for processing research papers."""

    def __init__(self, config: Config):
        """Initialize the pipeline.

        Args:
            config: Hedorah configuration
        """
        self.config = config

        # Initialize components
        self.pdf_processor = PDFProcessor(
            extract_figures=config.get('processing.extract_figures', True),
            extract_equations=config.get('processing.extract_equations', True),
            extract_citations=config.get('processing.extract_citations', True)
        )

        self.ollama = OllamaClient(config)
        self.claude = ClaudeClient(config)
        self.formatter = ObsidianFormatter(config.vault_path)

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging configuration."""
        log_level = self.config.get('logging.level', 'INFO')
        log_file = self.config.get('logging.file', 'hedorah.log')

        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def process_paper(self, pdf_path: Path, skip_experiments: bool = False) -> Dict[str, Path]:
        """Process a research paper through the full pipeline.

        Args:
            pdf_path: Path to the PDF file
            skip_experiments: Skip experiment generation (faster)

        Returns:
            Dictionary mapping note types to their file paths
        """
        logger.info(f"Processing paper: {pdf_path.name}")

        # 1. Extract content from PDF
        logger.info("Step 1/5: Extracting content from PDF...")
        attachments_dir = self.config.get_vault_folder('attachments')
        content = self.pdf_processor.process(pdf_path, attachments_dir)

        logger.info(f"Extracted {len(content.figures)} figures, "
                   f"{len(content.equations)} equations, "
                   f"{len(content.citations)} citations")

        # 2. Generate summary with local model
        logger.info("Step 2/5: Generating summary with local model (Qwen)...")
        summary = self.ollama.summarize_paper(content)
        logger.info(f"Generated summary with {len(summary.get('tags', []))} tags")

        # 3. Deep analysis with Claude
        logger.info("Step 3/5: Performing deep analysis with Claude...")
        analysis = self.claude.analyze_paper(content, summary)
        logger.info(f"Identified {len(analysis.get('key_insights', []))} insights, "
                   f"{len(analysis.get('research_gaps', []))} research gaps")

        # 4. Generate experiment proposals (optional)
        experiments = []
        if not skip_experiments:
            logger.info("Step 4/5: Generating experiment proposals...")
            experiments = self.claude.generate_experiments(content, analysis)
            logger.info(f"Generated {len(experiments)} experiment proposals")
        else:
            logger.info("Step 4/5: Skipping experiment generation")

        # 5. Create Obsidian notes
        logger.info("Step 5/5: Creating Obsidian notes...")
        created_notes = self._create_notes(content, summary, analysis, experiments)

        logger.info(f"Successfully processed {pdf_path.name}")
        logger.info(f"Created {len(created_notes)} notes in vault")

        return created_notes

    def _create_notes(self, content: PDFContent, summary: Dict[str, Any],
                     analysis: Dict[str, Any], experiments: list) -> Dict[str, Path]:
        """Create all Obsidian notes.

        Args:
            content: Extracted PDF content
            summary: Summary from Ollama
            analysis: Analysis from Claude
            experiments: Experiment proposals

        Returns:
            Dictionary mapping note types to file paths
        """
        created_notes = {}

        # Sanitize title for filename
        safe_title = self._sanitize_filename(content.title)

        # 1. Create paper summary note
        papers_dir = self.config.get_vault_folder('papers')
        papers_dir.mkdir(parents=True, exist_ok=True)

        paper_note_path = papers_dir / f"{safe_title}.md"
        paper_note = self.formatter.create_paper_note(content, summary)
        paper_note_path.write_text(paper_note, encoding='utf-8')
        created_notes['paper'] = paper_note_path
        logger.info(f"Created paper note: {paper_note_path.name}")

        # 2. Create insights note
        if analysis.get('key_insights'):
            notes_dir = self.config.get_vault_folder('notes')
            notes_dir.mkdir(parents=True, exist_ok=True)

            insights_note_path = notes_dir / f"Insights - {safe_title}.md"
            insights_note = self.formatter.create_insight_note(
                content.title, analysis['key_insights']
            )
            insights_note_path.write_text(insights_note, encoding='utf-8')
            created_notes['insights'] = insights_note_path
            logger.info(f"Created insights note: {insights_note_path.name}")

        # 3. Create connections note
        if analysis.get('connections'):
            notes_dir = self.config.get_vault_folder('notes')
            notes_dir.mkdir(parents=True, exist_ok=True)

            connections_note_path = notes_dir / f"Connections - {safe_title}.md"
            connections_note = self.formatter.create_connections_note(
                content.title, analysis['connections']
            )
            connections_note_path.write_text(connections_note, encoding='utf-8')
            created_notes['connections'] = connections_note_path
            logger.info(f"Created connections note: {connections_note_path.name}")

        # 4. Create experiment notes
        if experiments:
            experiments_dir = self.config.get_vault_folder('experiments')
            experiments_dir.mkdir(parents=True, exist_ok=True)

            for i, experiment in enumerate(experiments, 1):
                exp_title = experiment.get('title', f'Experiment {i}')
                safe_exp_title = self._sanitize_filename(exp_title)

                exp_note_path = experiments_dir / f"{safe_exp_title}.md"
                exp_note = self.formatter.create_experiment_note(
                    content.title, experiment
                )
                exp_note_path.write_text(exp_note, encoding='utf-8')
                created_notes[f'experiment_{i}'] = exp_note_path
                logger.info(f"Created experiment note: {exp_note_path.name}")

        return created_notes

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use as filename.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        import re
        # Remove or replace invalid filename characters
        text = re.sub(r'[<>:"/\\|?*]', '', text)
        # Replace spaces with hyphens
        text = re.sub(r'\s+', '-', text)
        # Limit length
        return text[:100]

    def process_directory(self, directory: Path, skip_experiments: bool = False) -> Dict[str, Dict[str, Path]]:
        """Process all PDFs in a directory.

        Args:
            directory: Directory containing PDFs
            skip_experiments: Skip experiment generation

        Returns:
            Dictionary mapping PDF names to their created notes
        """
        results = {}

        pdf_files = list(directory.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        for pdf_path in pdf_files:
            try:
                logger.info(f"Processing {pdf_path.name}...")
                created_notes = self.process_paper(pdf_path, skip_experiments)
                results[pdf_path.name] = created_notes
            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
                results[pdf_path.name] = {"error": str(e)}

        logger.info(f"Completed processing {len(results)} papers")
        return results
