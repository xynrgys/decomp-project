#!/usr/bin/env python3
"""
LLM Decompiler - Command-line interface for the decompiler.
"""

import argparse
import sys
from pathlib import Path

from src.core import Decompiler
from src.llm import LLMDecompiler
from src.utils import get_file_hash, ensure_directory

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='LLM Decompiler - Decompile binary files using advanced techniques.')
    
    # Required arguments
    parser.add_argument('binary', help='Path to the binary file to decompile')
    
    # Optional arguments
    parser.add_argument('-o', '--output', help='Output file path (default: stdout)')
    parser.add_argument('-a', '--arch', default='x86_64',
                       help='Target architecture (default: x86_64)')
    parser.add_argument('--model', default='gpt-4',
                       help='LLM model to use for enhancement (default: gpt-4)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    return parser.parse_args()

def main():
    """Main entry point for the decompiler."""
    args = parse_arguments()
    
    # Verify input file exists
    binary_path = Path(args.binary)
    if not binary_path.exists():
        print(f"Error: File not found: {binary_path}", file=sys.stderr)
        return 1
    
    if args.verbose:
        print(f"Decompiling {binary_path} for {args.arch} architecture")
    
    try:
        # Initialize decompiler components
        decompiler = Decompiler(arch=args.arch)
        llm = LLMDecompiler(model=args.model)
        
        # Perform decompilation
        decompiled_code = decompiler.decompile(str(binary_path))
        
        # Enhance with LLM
        enhanced_code = llm.enhance_decompilation(decompiled_code)
        
        # Output the result
        if args.output:
            output_path = Path(args.output)
            ensure_directory(output_path.parent)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_code)
            if args.verbose:
                print(f"Decompiled code written to {output_path}")
        else:
            print(enhanced_code)
            
        return 0
        
    except Exception as e:
        print(f"Error during decompilation: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
