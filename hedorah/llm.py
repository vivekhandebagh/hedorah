"""LLM integration for local and SOTA models."""

import json
import requests
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai
from .config import Config
from .pdf_processor import PDFContent


class OllamaClient:
    """Client for local Ollama models."""

    def __init__(self, config: Config):
        """Initialize Ollama client.

        Args:
            config: Hedorah configuration
        """
        self.config = config
        self.api_url = config.ollama_url
        self.model = config.local_model

    def generate(self, prompt: str, system: str = None) -> str:
        """Generate text using Ollama.

        Args:
            prompt: User prompt
            system: System prompt (optional)

        Returns:
            Generated text
        """
        url = f"{self.api_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if system:
            payload["system"] = system

        response = requests.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        return result.get("response", "")

    def summarize_paper(self, content: PDFContent) -> Dict[str, Any]:
        """Summarize a research paper using local model.

        Args:
            content: Extracted PDF content

        Returns:
            Structured summary
        """
        system_prompt = """You are an expert research librarian specializing in AI interpretability and mechanistic interpretability.
Your task is to summarize research papers in a structured format suitable for an Obsidian vault.
Focus on clarity, accuracy, and extracting key information."""

        user_prompt = f"""Analyze this research paper and provide a structured summary:

Title: {content.title}
Authors: {', '.join(content.authors)}

Abstract:
{content.abstract}

Full text (first 3000 chars):
{content.full_text[:3000]}

Provide a JSON response with the following structure:
{{
    "core_claims": ["claim1", "claim2", ...],
    "methodology": {{
        "approach": "description of the approach",
        "key_techniques": ["technique1", "technique2", ...],
        "datasets": ["dataset1", "dataset2", ...]
    }},
    "key_terminology": {{
        "term1": "definition1",
        "term2": "definition2"
    }},
    "limitations": ["limitation1", "limitation2", ...],
    "tags": ["tag1", "tag2", ...]
}}"""

        response = self.generate(user_prompt, system=system_prompt)

        # Try to parse JSON from response
        try:
            # Sometimes the model wraps JSON in markdown code blocks
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()
            else:
                json_text = response

            summary = json.loads(json_text)
            return summary
        except json.JSONDecodeError:
            # Fallback: return raw response
            return {
                "core_claims": [],
                "methodology": {},
                "key_terminology": {},
                "limitations": [],
                "tags": [],
                "raw_response": response
            }

    def generate_figure_descriptions(self, paper_title: str, abstract: str,
                                      figures: list, max_figures: int = 2) -> List[Dict[str, Any]]:
        """Generate descriptions for figures and select the most relevant ones.

        Args:
            paper_title: Title of the paper
            abstract: Paper abstract for context
            figures: List of Figure objects with captions
            max_figures: Maximum number of figures to select

        Returns:
            List of dicts with figure indices and descriptions
        """
        if not figures:
            return []

        # Build figure info for prompt
        figure_info = []
        for i, fig in enumerate(figures):
            caption_text = fig.caption if fig.caption else "No caption available"
            figure_info.append(f"Figure {i+1} (page {fig.page}, {fig.width}x{fig.height}): {caption_text}")

        figures_text = "\n".join(figure_info)

        system_prompt = """You are an expert at analyzing research papers and identifying the most important figures.
Select the figures that are most essential for understanding the paper's key contributions."""

        user_prompt = f"""Paper: {paper_title}

Abstract: {abstract}

Available figures:
{figures_text}

Select the {max_figures} most important figures for understanding this paper.
For each selected figure, provide a clear description of what it shows and why it's important.

Respond in JSON format:
{{
    "selected_figures": [
        {{
            "figure_number": 1,
            "description": "This figure shows...",
            "importance": "This is important because..."
        }}
    ]
}}"""

        response = self.generate(user_prompt, system=system_prompt)

        try:
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()
            else:
                json_text = response

            result = json.loads(json_text)
            return result.get("selected_figures", [])
        except json.JSONDecodeError:
            # Fallback: return first max_figures with basic descriptions
            return [{"figure_number": i+1, "description": fig.caption or "No description", "importance": ""}
                    for i, fig in enumerate(figures[:max_figures])]


class ReasoningClient(ABC):
    """Abstract base class for reasoning LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000) -> str:
        """Generate text using the LLM."""
        pass

    def analyze_paper(self, content: PDFContent, summary: Dict[str, Any],
                       user_notes: List[Dict[str, str]] = None,
                       agenda: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform deep analysis of a research paper.

        Args:
            content: Extracted PDF content
            summary: Summary from local model
            user_notes: Optional list of user notes from vault to incorporate
            agenda: Optional research agenda to guide analysis

        Returns:
            Deep analysis with insights and connections
        """
        # Build agenda-aware system prompt
        agenda_context = ""
        if agenda:
            agenda_context = f"""

IMPORTANT: The user has a specific research agenda. Prioritize insights and connections that align with their goals. Here is their research agenda:

{agenda.get('content', '')}

When analyzing this paper:
- Highlight aspects most relevant to their stated focus areas
- Identify connections to their current questions and interests
- Flag if the paper contradicts or supports their hunches
- Note if the paper is outside their stated interests (but still summarize key findings)
"""

        system_prompt = f"""You are an expert research analyst. Your task is to deeply analyze research papers, identify conceptual connections, research gaps, and generate actionable insights.

If the user has provided personal notes/thoughts, treat them as important context. Look for connections between the paper and these notes. The user's intuitions and questions are valuable - try to validate, extend, or connect them to the paper's findings.{agenda_context}"""

        # Build user notes section if provided
        notes_section = ""
        if user_notes:
            notes_text = "\n\n".join([
                f"**{note['title']}**\n{note['content']}"
                for note in user_notes
            ])
            notes_section = f"""

USER'S NOTES & THOUGHTS:
The following are the user's personal notes and ideas. Look for connections between these thoughts and the paper. If any of these notes relate to the paper's content, explicitly mention the connection.

{notes_text}
"""

        user_prompt = f"""Deeply analyze this research paper:

Title: {content.title}
Authors: {', '.join(content.authors)}

Summary:
{json.dumps(summary, indent=2)}

Abstract:
{content.abstract}

Key sections:
{self._format_sections(content.sections)}
{notes_section}
Provide a comprehensive analysis in JSON format:
{{
    "key_insights": [
        {{
            "insight": "description",
            "significance": "why this matters",
            "connections": ["connection to other concepts/papers/user notes"]
        }}
    ],
    "research_gaps": [
        {{
            "gap": "description of what's missing",
            "importance": "why this gap matters",
            "potential_impact": "what addressing it could enable"
        }}
    ],
    "connections": [
        {{
            "concept": "concept name",
            "related_to": ["related concepts/papers/user notes"],
            "relationship": "description of relationship"
        }}
    ],
    "note_connections": [
        {{
            "note_title": "title of user note that connects",
            "connection": "how this note relates to the paper",
            "insight": "what this connection reveals"
        }}
    ],
    "questions": [
        "interesting question 1",
        "interesting question 2"
    ]
}}"""

        response = self.generate(user_prompt, system=system_prompt, max_tokens=8000)

        try:
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()
            else:
                json_text = response

            analysis = json.loads(json_text)
            return analysis
        except json.JSONDecodeError:
            return {
                "key_insights": [],
                "research_gaps": [],
                "connections": [],
                "questions": [],
                "raw_response": response
            }

    def generate_experiments(self, content: PDFContent, analysis: Dict[str, Any],
                              agenda: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Generate experiment proposals based on the paper.

        Args:
            content: Extracted PDF content
            analysis: Deep analysis results
            agenda: Optional research agenda to guide experiment design

        Returns:
            List of experiment proposals
        """
        # Build agenda-aware context
        agenda_context = ""
        if agenda:
            agenda_context = f"""

IMPORTANT: The user has a specific research agenda. Design experiments that align with their goals and constraints. Here is their research agenda:

{agenda.get('content', '')}

When designing experiments:
- Prioritize experiments that address their stated questions and interests
- Respect any resource constraints they've mentioned (compute, time, etc.)
- Avoid suggesting experiments in areas they've marked as "not interested"
- Connect experiments to their current hunches and hypotheses when relevant
"""

        system_prompt = f"""You are an expert research experiment designer. Your task is to read research papers and design structured experiment specifications that could validate, extend, or challenge the paper's findings.

You are NOT generating code. You are generating a detailed experiment specification document that another researcher or agent could use to implement the experiment.

Focus on:
1. Clear, testable hypotheses grounded in the paper's claims
2. Well-defined experimental variables (independent, dependent, controlled)
3. Logical procedure broken into phases with clear steps
4. Pseudocode for any complex algorithmic logic
5. Expected results with clear success criteria

The experiment specification should be self-contained - someone reading it should understand exactly what to build and why, without needing to read the source paper.{agenda_context}"""

        user_prompt = f"""Based on this paper analysis, generate experiment proposals:

Paper: {content.title}
Authors: {', '.join(content.authors)}

Abstract:
{content.abstract}

Key insights from analysis:
{json.dumps(analysis.get('key_insights', []), indent=2)}

Research gaps identified:
{json.dumps(analysis.get('research_gaps', []), indent=2)}

Generate 2-4 experiment proposals in JSON format. Each experiment should be a complete specification that could be handed off to another researcher or implementation agent:

{{
    "experiments": [
        {{
            "title": "Descriptive experiment title",
            "experiment_id": "snake_case_identifier",

            "motivation": "Why this experiment is worth doing - what question does it answer?",
            "hypothesis": "A testable prediction with reasoning - what do you expect to find and why?",
            "source_insights": ["Specific insight from the paper that inspires this experiment"],

            "objective": "What we're trying to measure or discover",

            "variables": {{
                "independent": ["Variables to manipulate"],
                "dependent": ["Variables to measure"],
                "controlled": ["Variables to hold constant"]
            }},

            "parameters": [
                {{
                    "name": "parameter_name",
                    "type": "str|int|float|bool|list",
                    "description": "What this parameter controls",
                    "default": "sensible default value",
                    "range": "valid range if applicable"
                }}
            ],

            "procedure": [
                {{
                    "phase": "Phase Name",
                    "steps": ["Step 1 description", "Step 2 description"],
                    "pseudocode": "Optional pseudocode for complex algorithmic logic"
                }}
            ],

            "expected_results": [
                {{
                    "name": "result_name",
                    "type": "Python type hint (e.g., float, list[dict], dict[str, float])",
                    "description": "What this result tells us"
                }}
            ],

            "difficulty": "easy|medium|hard",
            "estimated_time": "Time estimate (e.g., '2-4 hours', '1-2 days')",
            "suggested_tools": ["Libraries or frameworks useful for this experiment"],
            "prerequisites": ["What needs to be in place before starting"]
        }}
    ]
}}"""

        response = self.generate(user_prompt, system=system_prompt, max_tokens=8000)

        try:
            if "```json" in response:
                json_text = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_text = response.split("```")[1].split("```")[0].strip()
            else:
                json_text = response

            result = json.loads(json_text)
            return result.get("experiments", [])
        except json.JSONDecodeError:
            return []

    def _format_sections(self, sections: Dict[str, str]) -> str:
        """Format sections for prompt.

        Args:
            sections: Dictionary of section titles to content

        Returns:
            Formatted string
        """
        formatted = []
        for title, content in sections.items():
            # Truncate long sections
            truncated = content[:500] + "..." if len(content) > 500 else content
            formatted.append(f"## {title}\n{truncated}")

        return "\n\n".join(formatted)


class ClaudeClient(ReasoningClient):
    """Client for Claude API (Anthropic)."""

    def __init__(self, config: Config):
        """Initialize Claude client.

        Args:
            config: Hedorah configuration
        """
        self.config = config
        api_key = config.get('llm.reasoning.api_key')
        if not api_key or api_key.startswith('${'):
            raise ValueError("Anthropic API key not configured")
        self.client = Anthropic(api_key=api_key)
        self.model = config.reasoning_model

    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000) -> str:
        """Generate text using Claude.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }

        if system:
            kwargs["system"] = system

        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenAIClient(ReasoningClient):
    """Client for OpenAI API (GPT-4, o1, etc.)."""

    def __init__(self, config: Config):
        """Initialize OpenAI client.

        Args:
            config: Hedorah configuration
        """
        self.config = config
        api_key = config.get('llm.reasoning.api_key')
        if not api_key or api_key.startswith('${'):
            raise ValueError("OpenAI API key not configured")
        self.client = OpenAI(api_key=api_key)
        self.model = config.reasoning_model

    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000) -> str:
        """Generate text using OpenAI.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content


class GeminiClient(ReasoningClient):
    """Client for Google Gemini API."""

    def __init__(self, config: Config):
        """Initialize Gemini client.

        Args:
            config: Hedorah configuration
        """
        self.config = config
        api_key = config.get('llm.reasoning.api_key')
        if not api_key or api_key.startswith('${'):
            raise ValueError("Google API key not configured")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config.reasoning_model)

    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000) -> str:
        """Generate text using Gemini.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        # Gemini combines system and user prompts
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        response = self.model.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens
            )
        )

        return response.text


def create_reasoning_client(config: Config) -> ReasoningClient:
    """Factory function to create the appropriate reasoning client.

    Args:
        config: Hedorah configuration

    Returns:
        ReasoningClient instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = config.get('llm.reasoning.provider', 'anthropic').lower()

    if provider == 'anthropic':
        return ClaudeClient(config)
    elif provider == 'openai':
        return OpenAIClient(config)
    elif provider == 'gemini' or provider == 'google':
        return GeminiClient(config)
    else:
        raise ValueError(f"Unsupported reasoning provider: {provider}")
