#!/usr/bin/env python3
"""
Test script for iflow LLM provider integration
"""
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from llm.client import LLMClient

def test_iflow_provider():
    """Test iflow provider integration."""
    print("Testing iflow provider integration...")

    # Initialize iflow client
    client = LLMClient(provider='iflow')

    # Test prompt
    prompt = "What is the meaning of life?"
    system_prompt = "You are a helpful AI assistant."

    try:
        print("Sending request to iflow API...")
        response = client.call(prompt, system_prompt)
        print("Response received:")
        print(f"Code: {response.get('code', 'N/A')}")
        print(f"Confidence: {response.get('confidence', 'N/A')}")
        print(f"Explanations: {response.get('explanations', 'N/A')}")
        print(f"Recompilable: {response.get('recompilable', 'N/A')}")
        print("Test completed successfully!")
        return True
    except Exception as e:
        print(f"Error during test: {e}")
        return False

if __name__ == '__main__':
    success = test_iflow_provider()
    sys.exit(0 if success else 1)