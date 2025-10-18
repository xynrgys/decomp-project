"""LLM client abstraction with local and remote adapters.
"""
from typing import Dict
import json
import os

class LLMClient:
    def __init__(self, provider: str = 'mock', api_key: str = None, base_url: str = None):
        self.provider = provider
        self.api_key = api_key or os.getenv('LLM_API_KEY')
        self.base_url = base_url

        # Initialize provider-specific clients
        if provider == 'openai':
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("OpenAI library not installed. Please install using: pip install openai")
        elif provider == 'anthropic':
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Anthropic library not installed. Please install using: pip install anthropic")
        elif provider == 'iflow':
            try:
                import openai
                self.client = openai.OpenAI(
                    base_url="https://apis.iflow.cn/v1",
                    api_key=self.api_key or "sk-xxx"
                )
            except ImportError:
                raise ImportError("OpenAI library not installed. Please install using: pip install openai")
        elif provider == 'local':
            # For local models, we might use transformers or similar
            self.client = None
        else:
            self.client = None

    def call(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call the underlying LLM and return parsed JSON.
        For MVP this can return a mock response.
        """
        if self.provider == 'openai':
            return self._call_openai(prompt, system_prompt)
        elif self.provider == 'anthropic':
            return self._call_anthropic(prompt, system_prompt)
        elif self.provider == 'iflow':
            return self._call_iflow(prompt, system_prompt)
        elif self.provider == 'local':
            return self._call_local(prompt, system_prompt)
        else:
            # Mock response - fallback for testing
            return {
                "code": "int foo(){ return 0; }",
                "confidence": 0.5,
                "edits": [],
                "recompilable": True,
                "explanations": "Mock response for testing purposes"
            }

    def _call_openai(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call OpenAI API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            # Try to parse as JSON, fallback to text if parsing fails
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "code": content,
                    "confidence": 0.8,
                    "edits": [],
                    "recompilable": True,
                    "explanations": "Generated from OpenAI"
                }
        except Exception as e:
            # Fallback to mock response if API call fails
            return {
                "code": f"// Error calling OpenAI: {str(e)}\nint foo(){{ return 0; }}",
                "confidence": 0.1,
                "edits": [],
                "recompilable": False,
                "explanations": f"Error calling OpenAI: {str(e)}"
            }

    def _call_anthropic(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call Anthropic API."""
        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.client.messages.create(
                model="claude-3-opus-20240229",
                messages=messages,
                system=system_prompt or "You are a binary decompiler assistant.",
                max_tokens=2000,
                temperature=0.2
            )

            content = response.content[0].text
            # Try to parse as JSON, fallback to text if parsing fails
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "code": content,
                    "confidence": 0.8,
                    "edits": [],
                    "recompilable": True,
                    "explanations": "Generated from Anthropic"
                }
        except Exception as e:
            # Fallback to mock response if API call fails
            return {
                "code": f"// Error calling Anthropic: {str(e)}\nint foo(){{ return 0; }}",
                "confidence": 0.1,
                "edits": [],
                "recompilable": False,
                "explanations": f"Error calling Anthropic: {str(e)}"
            }

    def _call_local(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call local model (placeholder implementation)."""
        # This would require implementing local model loading and inference
        # For now, return a mock response
        return {
            "code": "// Local model response placeholder\nint foo(){ return 0; }",
            "confidence": 0.6,
            "edits": [],
            "recompilable": True,
            "explanations": "Generated from local model (placeholder)"
        }

    def _call_iflow(self, prompt: str, system_prompt: str = None) -> Dict:
        """Call iflow API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                extra_body={},
                model="glm-4.6",
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            # Try to parse as JSON, fallback to text if parsing fails
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "code": content,
                    "confidence": 0.8,
                    "edits": [],
                    "recompilable": True,
                    "explanations": "Generated from iflow"
                }
        except Exception as e:
            # Fallback to mock response if API call fails
            return {
                "code": f"// Error calling iflow: {str(e)}\nint foo(){{ return 0; }}",
                "confidence": 0.1,
                "edits": [],
                "recompilable": False,
                "explanations": f"Error calling iflow: {str(e)}"
            }