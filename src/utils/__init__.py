"""
Utility functions for the LLM Decompiler.
"""

import os
import hashlib
from typing import Optional, Dict, Any, List

def get_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hashing algorithm to use (default: sha256)
        
    Returns:
        str: Hexadecimal digest of the file
    """
    hash_func = getattr(hashlib, algorithm, hashlib.sha256)
    with open(file_path, 'rb') as f:
        return hash_func(f.read()).hexdigest()

def ensure_directory(directory: str) -> None:
    """Ensure that a directory exists, create it if it doesn't.
    
    Args:
        directory: Path to the directory
    """
    os.makedirs(directory, exist_ok=True)

def format_code(code: str, language: str = 'c') -> str:
    """Format code for better readability.
    
    Args:
        code: The code to format
        language: Programming language of the code
        
    Returns:
        str: Formatted code
    """
    # TODO: Implement code formatting based on language
    return code

def parse_arguments() -> Dict[str, Any]:
    """Parse command line arguments.
    
    Returns:
        Dict with parsed arguments
    """
    # TODO: Implement argument parsing
    return {}
