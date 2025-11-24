# Hedorah: Personal Research Agent

A personal research agent system for AI interpretability and mechanistic interpretability research. Hedorah automatically processes research papers, creates structured summaries, identifies insights and connections, and generates actionable experiment proposals in your Obsidian vault.

## Features

- Automated PDF Processing: Extracts text, figures, equations, and citations from research papers
- Two-Tier LLM System:
  - Local model (Qwen 2.5 via Ollama) for summarization and librarian work
  - Claude API for deep reasoning, insight generation, and experiment design
- Obsidian Integration: Generates properly formatted markdown notes with wikilinks, tags, and frontmatter
- Structured Output:
  - Paper summaries with core claims, methodology, terminology, and limitations
  - Research insights with conceptual connections
  - Experiment proposals with hypotheses, methodologies, and expected outcomes
- Flexible Usage:
  - CLI for manual processing
  - Watch mode for automatic processing of new PDFs
  - Batch processing for multiple papers

## Installation

### Prerequisites

1. Python 3.11+ with uv package manager
2. Ollama for local model inference (https://ollama.ai)
3. Anthropic API key for Claude access

### Setup

1. Clone the repository and navigate to the project directory

2. Install dependencies:
```bash
uv sync
```

3. Pull the Qwen model in Ollama:
```bash
ollama pull qwen2.5:latest
```

4. Initialize configuration:
```bash
uv run hedorah init
```

5. Edit config.yaml and set your Obsidian vault path

6. Edit .env and add your API key(s)

## Supported LLM Providers

Hedorah supports multiple LLM providers for deep reasoning and analysis:

### Anthropic (Claude)
```yaml
# config.yaml
llm:
  reasoning:
    provider: "anthropic"
    model: "claude-sonnet-4-5-20250929"
    api_key: "${ANTHROPIC_API_KEY}"
```

Models: claude-sonnet-4-5-20250929, claude-opus-4-20250514, claude-sonnet-3-5-20241022

### OpenAI (GPT-4, o1)
```yaml
# config.yaml
llm:
  reasoning:
    provider: "openai"
    model: "gpt-4-turbo"
    api_key: "${OPENAI_API_KEY}"
```

Models: gpt-4-turbo, gpt-4, gpt-4o, o1-preview, o1-mini

### Google Gemini
```yaml
# config.yaml
llm:
  reasoning:
    provider: "gemini"
    model: "gemini-1.5-pro"
    api_key: "${GOOGLE_API_KEY}"
```

Models: gemini-1.5-pro, gemini-1.5-flash, gemini-pro

## Usage

### Process a Single PDF

```bash
uv run hedorah process path/to/paper.pdf
```

Options:
- `-s, --skip-experiments`: Skip experiment generation for faster processing
- `-c, --config`: Specify custom config file path

### Batch Process Multiple PDFs

```bash
uv run hedorah batch path/to/papers/directory
```

### Watch Mode (Automatic Processing)

```bash
uv run hedorah watch
```

Drop PDFs into vault/inbox/ and Hedorah will automatically process them.

### View Configuration

```bash
uv run hedorah info
```

## Vault Structure

Hedorah creates the following structure in your Obsidian vault:

```
vault/
  papers/          # Paper summaries
  notes/           # Research insights and connections
  experiments/     # Experiment proposals
  attachments/     # Extracted figures and diagrams
  inbox/           # Drop PDFs here for watch mode
```

## Architecture

The system follows a three-stage pipeline:

1. PDF Processing (pymupdf): Extract text, figures, equations, citations
2. Summarization (Qwen 2.5): Generate structured summaries with metadata
3. Deep Analysis (Claude): Identify insights, connections, and generate experiments

All outputs are formatted as Obsidian-compatible markdown with proper wikilinks and tags.

## Development

### Project Structure

```
hedorah_agent/
  hedorah/
    cli.py              # Command-line interface
    config.py           # Configuration management
    pdf_processor.py    # PDF extraction
    llm.py              # LLM integrations
    obsidian.py         # Markdown generation
    pipeline.py         # Main orchestration
    watcher.py          # File watching
  config.example.yaml   # Example configuration
  .env.example          # Example environment variables
  pyproject.toml        # Project dependencies
```

## Troubleshooting

### Configuration file not found
Run `hedorah init` to create configuration files from examples.

### Anthropic API key not configured
Ensure your .env file contains a valid ANTHROPIC_API_KEY.

### Ollama connection failed
Make sure Ollama is running: `ollama serve`

### Figures not extracting
Some PDFs have images embedded as vector graphics. Try using a different PDF source.

## License

MIT

## Contributing

This is a personal research tool, but suggestions and improvements are welcome!
