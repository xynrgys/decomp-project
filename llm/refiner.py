"""Refine FunctionJSON into high level C using an LLM.
"""
from typing import Dict
from .client import LLMClient
import json
import os

class Refiner:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        # Load prompt templates
        self._load_prompts()

    def _load_prompts(self):
        """Load prompt templates from files."""
        try:
            # Load decompilation prompt (try improved version first)
            decomp_prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'improved_decompilation_prompt.txt')
            if not os.path.exists(decomp_prompt_path):
                decomp_prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'decompilation_prompt.txt')

            if os.path.exists(decomp_prompt_path):
                with open(decomp_prompt_path, 'r') as f:
                    self.decompilation_prompt_template = f.read()
            else:
                self.decompilation_prompt_template = "Convert the following assembly to C code:\n{function_json}"

            # Load analysis prompt
            analysis_prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'analysis_prompt.txt')
            if os.path.exists(analysis_prompt_path):
                with open(analysis_prompt_path, 'r') as f:
                    self.analysis_prompt_template = f.read()
            else:
                self.analysis_prompt_template = "Analyze the following assembly code:\n{function_json}"
        except Exception:
            # Fallback to simple prompts
            self.decompilation_prompt_template = "Convert the following assembly to C code:\n{function_json}"
            self.analysis_prompt_template = "Analyze the following assembly code:\n{function_json}"

    def _extract_nested_json(self, obj):
        """Recursively extract nested JSON structures to find the actual content."""
        if isinstance(obj, dict):
            # Check for 'code' field (for decompilation responses)
            if 'code' in obj:
                code_content = obj['code']
                # If code_content is a string that looks like JSON, try to parse it recursively
                if isinstance(code_content, str):
                    stripped_code = code_content.strip()
                    # Handle case where the entire response is a JSON string starting with '{'
                    if stripped_code.startswith('{') and stripped_code.endswith('}'):
                        try:
                            parsed_inner = json.loads(stripped_code)
                            # If the parsed content has a 'code' field, extract that directly
                            if isinstance(parsed_inner, dict) and 'code' in parsed_inner:
                                obj['code'] = parsed_inner['code']
                                return obj
                            # Otherwise, recursively extract from the parsed content
                            else:
                                extracted = self._extract_nested_json(parsed_inner)
                                if extracted != parsed_inner:
                                    obj['code'] = extracted
                        except json.JSONDecodeError:
                            # If parsing fails, try to extract code content from the JSON string
                            try:
                                # Look for "code": "..." pattern in the string
                                import re
                                match = re.search(r'"code":\s*"([^"]*(?:\\.[^"]*)*)"', stripped_code)
                                if match:
                                    # Unescape the extracted code
                                    extracted_code = match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    obj['code'] = extracted_code
                            except Exception:
                                pass
                return obj
            # Check for 'analysis' field (for analysis responses)
            elif 'analysis' in obj:
                analysis_content = obj['analysis']
                # If analysis_content is a string that looks like JSON, try to parse it recursively
                if isinstance(analysis_content, str):
                    stripped_analysis = analysis_content.strip()
                    if stripped_analysis.startswith('{') and stripped_analysis.endswith('}'):
                        try:
                            parsed_inner = json.loads(stripped_analysis)
                            # If the parsed content has an 'analysis' field, extract that directly
                            if isinstance(parsed_inner, dict) and 'analysis' in parsed_inner:
                                obj['analysis'] = parsed_inner['analysis']
                                return obj
                            # Otherwise, recursively extract from the parsed content
                            else:
                                extracted = self._extract_nested_json(parsed_inner)
                                if extracted != parsed_inner:
                                    obj['analysis'] = extracted
                        except json.JSONDecodeError:
                            # If parsing fails, try to extract analysis content from the JSON string
                            try:
                                # Look for "analysis": "..." pattern in the string
                                import re
                                match = re.search(r'"analysis":\s*"([^"]*(?:\\.[^"]*)*)"', stripped_analysis)
                                if match:
                                    # Unescape the extracted analysis
                                    extracted_analysis = match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                    obj['analysis'] = extracted_analysis
                            except Exception:
                                pass
                return obj
            else:
                # Check if the entire response is a JSON string
                resp_str = str(obj)
                stripped_resp = resp_str.strip()
                if stripped_resp.startswith('{') and stripped_resp.endswith('}'):
                    try:
                        parsed_resp = json.loads(stripped_resp)
                        # Recursively extract from the parsed response
                        return self._extract_nested_json(parsed_resp)
                    except json.JSONDecodeError:
                        # If JSON parsing fails, try regex extraction as fallback
                        try:
                            # Look for "code": "..." pattern in the string
                            import re
                            match = re.search(r'"code":\s*"([^"]*(?:\\.[^"]*)*)"', stripped_resp)
                            if match:
                                # Unescape the extracted code
                                extracted_code = match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                                return {'code': extracted_code}
                        except Exception:
                            pass
                        return obj
                else:
                    return obj
        else:
            # For non-dict responses, check if they're JSON strings
            resp_str = str(obj)
            stripped_resp = resp_str.strip()
            if stripped_resp.startswith('{') and stripped_resp.endswith('}'):
                try:
                    parsed_resp = json.loads(stripped_resp)
                    # Recursively extract from the parsed response
                    return self._extract_nested_json(parsed_resp)
                except json.JSONDecodeError:
                    # If parsing fails, try regex extraction as fallback
                    try:
                        # Look for "code": "..." pattern in the string
                        import re
                        match = re.search(r'"code":\s*"([^"]*(?:\\.[^"]*)*)"', stripped_resp)
                        if match:
                            # Unescape the extracted code
                            extracted_code = match.group(1).replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                            return {'code': extracted_code}
                    except Exception:
                        pass
                    return obj
            else:
                return obj

    def refine(self, function_json: Dict, baseline: str = '') -> Dict:
        """Return LLMResponseJSON with C code. Uses prompt templates to ensure JSON output."""
        # Prepare the prompt with the function data
        function_json_str = json.dumps(function_json, indent=2)
        prompt = self.decompilation_prompt_template.replace('{{function_json}}', function_json_str)

        # Add baseline if provided
        if baseline:
            prompt += f"\n\nBaseline C code for reference:\n{baseline}"

        # Call the LLM with a system prompt to guide the output format
        system_prompt = "You are a binary decompiler assistant. Convert assembly code to C code and return valid JSON with the code in the 'code' field."
        resp = self.llm.call(prompt, system_prompt)

        # Extract nested JSON structures
        resp = self._extract_nested_json(resp)

        # Ensure all required keys exist
        if not isinstance(resp, dict):
            resp = {
                'code': str(resp),
                'confidence': 0.1,
                'edits': [],
                'recompilable': False,
                'explanations': 'Response was converted to dict'
            }

        resp.setdefault('code', '// No code generated')
        resp.setdefault('confidence', 0.0)
        resp.setdefault('edits', [])
        resp.setdefault('recompilable', False)
        resp.setdefault('explanations', '')

        return resp

    def analyze(self, function_json: Dict) -> Dict:
        """Return detailed analysis report of the function."""
        # Prepare the prompt with the function data
        function_json_str = json.dumps(function_json, indent=2)
        prompt = self.analysis_prompt_template.replace('{{function_json}}', function_json_str)

        # Call the LLM with a system prompt to guide the output format
        system_prompt = "You are a binary analysis expert. Analyze assembly code and return a detailed JSON report with findings."
        resp = self.llm.call(prompt, system_prompt)

        # Use the same nested JSON extraction logic as in refine method
        resp = self._extract_nested_json(resp)

        # Ensure required keys exist
        resp.setdefault('analysis', 'Analysis not available')
        resp.setdefault('confidence', 0.0)
        resp.setdefault('findings', [])
        resp.setdefault('vulnerabilities', [])

        return resp