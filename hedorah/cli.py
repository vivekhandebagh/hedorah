"""Command-line interface for Hedorah."""

import click
import sys
from pathlib import Path
from .config import get_config
from .pipeline import HedorahPipeline
from .watcher import VaultWatcher


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Hedorah: Personal research agent for AI interpretability.

    Process research papers, generate insights, and create structured
    experiment proposals in your Obsidian vault.
    """
    pass


@main.command()
@click.argument('pdf_path', type=click.Path(exists=True, path_type=Path))
@click.option('--config', '-c', default='config.yaml',
              help='Path to configuration file')
@click.option('--skip-experiments', '-s', is_flag=True,
              help='Skip experiment generation (faster)')
def process(pdf_path: Path, config: str, skip_experiments: bool):
    """Process a single PDF file.

    PDF_PATH: Path to the PDF file to process
    """
    try:
        # Load configuration
        cfg = get_config(config)
        click.echo(f"Processing: {pdf_path.name}")
        click.echo(f"Vault: {cfg.vault_path}")

        # Create pipeline
        pipeline = HedorahPipeline(cfg)

        # Process the paper
        with click.progressbar(length=5, label='Processing paper') as bar:
            created_notes = pipeline.process_paper(pdf_path, skip_experiments)
            bar.update(5)

        # Show results
        click.echo("\n✅ Processing complete!")
        click.echo(f"Created {len(created_notes)} notes:\n")
        for note_type, note_path in created_notes.items():
            click.echo(f"  • {note_type}: {note_path.name}")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("Please copy config.example.yaml to config.yaml and configure it.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('directory', type=click.Path(exists=True, path_type=Path))
@click.option('--config', '-c', default='config.yaml',
              help='Path to configuration file')
@click.option('--skip-experiments', '-s', is_flag=True,
              help='Skip experiment generation (faster)')
def batch(directory: Path, config: str, skip_experiments: bool):
    """Process all PDFs in a directory.

    DIRECTORY: Path to directory containing PDF files
    """
    try:
        # Load configuration
        cfg = get_config(config)
        click.echo(f"Processing all PDFs in: {directory}")
        click.echo(f"Vault: {cfg.vault_path}\n")

        # Create pipeline
        pipeline = HedorahPipeline(cfg)

        # Process directory
        results = pipeline.process_directory(directory, skip_experiments)

        # Show results
        click.echo(f"\n✅ Batch processing complete!")
        click.echo(f"Processed {len(results)} papers\n")

        for pdf_name, notes in results.items():
            if "error" in notes:
                click.echo(f"  ❌ {pdf_name}: {notes['error']}")
            else:
                click.echo(f"  ✅ {pdf_name}: {len(notes)} notes created")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("Please copy config.example.yaml to config.yaml and configure it.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option('--config', '-c', default='config.yaml',
              help='Path to configuration file')
@click.option('--skip-experiments', '-s', is_flag=True,
              help='Skip experiment generation (faster)')
def watch(config: str, skip_experiments: bool):
    """Watch inbox folder for new PDFs and process them automatically.

    Monitors the vault inbox folder and automatically processes any new
    PDF files that are added.
    """
    try:
        # Load configuration
        cfg = get_config(config)

        inbox_path = cfg.get_vault_folder('inbox')
        if not inbox_path.exists():
            inbox_path.mkdir(parents=True)
            click.echo(f"Created inbox folder: {inbox_path}")

        click.echo(f"👁️  Watching: {inbox_path}")
        click.echo(f"Vault: {cfg.vault_path}")
        click.echo("\nPress Ctrl+C to stop\n")

        # Create and start watcher
        watcher = VaultWatcher(cfg, skip_experiments)
        watcher.start()

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("Please copy config.example.yaml to config.yaml and configure it.", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n👋 Stopping watcher...")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
def init():
    """Initialize a new Hedorah configuration.

    Creates config.yaml and .env from example files if they don't exist.
    """
    import shutil

    config_created = False
    env_created = False

    # Create config.yaml
    if not Path('config.yaml').exists():
        if Path('config.example.yaml').exists():
            shutil.copy('config.example.yaml', 'config.yaml')
            click.echo("✅ Created config.yaml from example")
            config_created = True
        else:
            click.echo("❌ config.example.yaml not found", err=True)
    else:
        click.echo("⚠️  config.yaml already exists")

    # Create .env
    if not Path('.env').exists():
        if Path('.env.example').exists():
            shutil.copy('.env.example', '.env')
            click.echo("✅ Created .env from example")
            env_created = True
        else:
            click.echo("❌ .env.example not found", err=True)
    else:
        click.echo("⚠️  .env already exists")

    if config_created or env_created:
        click.echo("\n📝 Next steps:")
        if config_created:
            click.echo("  1. Edit config.yaml and set your vault path")
        if env_created:
            click.echo("  2. Edit .env and add your ANTHROPIC_API_KEY")
        click.echo("  3. Run 'hedorah process <pdf>' to process a paper")


@main.command()
@click.option('--config', '-c', default='config.yaml',
              help='Path to configuration file')
def info(config: str):
    """Show current configuration and system status."""
    try:
        cfg = get_config(config)

        click.echo("Hedorah Configuration\n")
        click.echo(f"Vault Path: {cfg.vault_path}")
        click.echo(f"  Papers: {cfg.get_vault_folder('papers')}")
        click.echo(f"  Notes: {cfg.get_vault_folder('notes')}")
        click.echo(f"  Experiments: {cfg.get_vault_folder('experiments')}")
        click.echo(f"  Attachments: {cfg.get_vault_folder('attachments')}")
        click.echo(f"  Inbox: {cfg.get_vault_folder('inbox')}")

        click.echo(f"\nLocal Model: {cfg.local_model}")
        click.echo(f"  Ollama URL: {cfg.ollama_url}")

        click.echo(f"\nReasoning Model: {cfg.reasoning_model}")
        api_key = cfg.get('llm.reasoning.api_key', 'NOT SET')
        if api_key and not api_key.startswith('${'):
            click.echo(f"  API Key: {'*' * 20}{api_key[-4:]}")
        else:
            click.echo(f"  API Key: ❌ NOT CONFIGURED")

        click.echo(f"\nProcessing Options:")
        click.echo(f"  Extract Figures: {cfg.get('processing.extract_figures', True)}")
        click.echo(f"  Extract Equations: {cfg.get('processing.extract_equations', True)}")
        click.echo(f"  Extract Citations: {cfg.get('processing.extract_citations', True)}")

    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        click.echo("\nRun 'hedorah init' to create configuration files.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
