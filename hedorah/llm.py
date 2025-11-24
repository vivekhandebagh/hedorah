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


class ReasoningClient(ABC):
    """Abstract base class for reasoning LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, system: str = None, max_tokens: int = 4000) -> str:
        """Generate text using the LLM."""
        pass

    def analyze_paper(self, content: PDFContent, summary: Dict[str, Any]) -> Dict[str, Any]:
        """Perform deep analysis of a research paper.

        Args:
            content: Extracted PDF content
            summary: Summary from local model

        Returns:
            Deep analysis with insights and connections
        """
        system_prompt = """You are an expert AI researcher specializing in mechanistic interpretability and AI safety.
Your task is to deeply analyze research papers, identify conceptual connections, research gaps,
and generate actionable experiment ideas."""

        user_prompt = f"""Deeply analyze this research paper:

Title: {content.title}
Authors: {', '.join(content.authors)}

Summary:
{json.dumps(summary, indent=2)}

Abstract:
{content.abstract}

Key sections:
{self._format_sections(content.sections)}

Provide a comprehensive analysis in JSON format:
{{
    "key_insights": [
        {{
            "insight": "description",
            "significance": "why this matters",
            "connections": ["connection to other concepts/papers"]
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
            "related_to": ["related concepts/papers"],
            "relationship": "description of relationship"
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

    def generate_experiments(self, content: PDFContent, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate experiment proposals based on the paper.

        Args:
            content: Extracted PDF content
            analysis: Deep analysis results

        Returns:
            List of experiment proposals
        """
        system_prompt = """You are an expert experimental designer in AI mechanistic interpretability.
Generate concrete, actionable experiment proposals that could extend or validate the paper's findings."""

        user_prompt = f"""Based on this paper analysis, generate experiment proposals:

Paper: {content.title}

Key insights:
{json.dumps(analysis.get('key_insights', []), indent=2)}

Research gaps:
{json.dumps(analysis.get('research_gaps', []), indent=2)}

Generate 2-4 experiment proposals in JSON format:
{{
    "experiments": [
        {{
            "title": "experiment title",
            "motivation": "why this experiment is worth doing",
            "hypothesis": "what you expect to find and why",
            "methodology": {{
                "approach": "high-level approach",
                "steps": ["step 1", "step 2", ...],
                "required_resources": ["resource1", "resource2"]
            }},
            "expected_outcomes": {{
                "success_criteria": "what success looks like",
                "potential_findings": ["finding1", "finding2"],
                "implications": "what the results would tell us"
            }},
            "difficulty": "easy|medium|hard",
            "estimated_time": "time estimate"
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
