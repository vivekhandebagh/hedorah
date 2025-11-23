"""File watcher for automatic PDF processing."""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent
from .config import Config
from .pipeline import HedorahPipeline

logger = logging.getLogger(__name__)


class PDFHandler(FileSystemEventHandler):
    """Handler for PDF file events."""

    def __init__(self, pipeline: HedorahPipeline, skip_experiments: bool = False):
        """Initialize PDF handler.

        Args:
            pipeline: Hedorah pipeline for processing
            skip_experiments: Skip experiment generation
        """
        self.pipeline = pipeline
        self.skip_experiments = skip_experiments
        self.processing = set()  # Track files currently being processed

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only process PDF files
        if file_path.suffix.lower() != '.pdf':
            return

        # Skip if already processing
        if file_path in self.processing:
            return

        # Wait a moment to ensure file is fully written
        time.sleep(1)

        try:
            self.processing.add(file_path)
            logger.info(f"New PDF detected: {file_path.name}")
            print(f"\n📄 Processing new PDF: {file_path.name}")

            # Process the paper
            created_notes = self.pipeline.process_paper(file_path, self.skip_experiments)

            print(f"✅ Successfully processed {file_path.name}")
            print(f"   Created {len(created_notes)} notes")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)
            print(f"❌ Error processing {file_path.name}: {e}")

        finally:
            self.processing.remove(file_path)


class VaultWatcher:
    """Watches vault inbox for new PDFs."""

    def __init__(self, config: Config, skip_experiments: bool = False):
        """Initialize vault watcher.

        Args:
            config: Hedorah configuration
            skip_experiments: Skip experiment generation
        """
        self.config = config
        self.skip_experiments = skip_experiments
        self.inbox_path = config.get_vault_folder('inbox')

        # Ensure inbox exists
        self.inbox_path.mkdir(parents=True, exist_ok=True)

        # Create pipeline and handler
        self.pipeline = HedorahPipeline(config)
        self.event_handler = PDFHandler(self.pipeline, skip_experiments)

        # Create observer
        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.inbox_path),
            recursive=False
        )

    def start(self):
        """Start watching the inbox folder."""
        logger.info(f"Starting watcher on {self.inbox_path}")

        # Process any existing PDFs first
        self._process_existing_pdfs()

        # Start watching
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop watching."""
        logger.info("Stopping watcher")
        self.observer.stop()
        self.observer.join()

    def _process_existing_pdfs(self):
        """Process any PDFs already in the inbox."""
        existing_pdfs = list(self.inbox_path.glob("*.pdf"))

        if existing_pdfs:
            logger.info(f"Found {len(existing_pdfs)} existing PDFs in inbox")
            print(f"\n📦 Found {len(existing_pdfs)} existing PDFs in inbox")

            for pdf_path in existing_pdfs:
                try:
                    print(f"\n📄 Processing: {pdf_path.name}")
                    created_notes = self.pipeline.process_paper(
                        pdf_path, self.skip_experiments
                    )
                    print(f"✅ Successfully processed {pdf_path.name}")
                    print(f"   Created {len(created_notes)} notes")

                except Exception as e:
                    logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)
                    print(f"❌ Error processing {pdf_path.name}: {e}")

            print(f"\n👁️  Now watching for new PDFs...\n")
