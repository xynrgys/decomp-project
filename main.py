#!/usr/bin/env python3
"""
Main entry point for the Hybrid LLM-Powered Binary Decompiler
"""
import argparse
import sys
import os
import json
from pathlib import Path
import traceback
import logging

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from ingest.binary_loader import BinaryLoader
from disasm.disassembler import Disassembler
from analysis.analyzer import Analyzer
from llm.client import LLMClient
from llm.refiner import Refiner
from verifier.verifier import CompileVerifier
from storage.store import Store
from utils.logger import get_decompiler_logger

def main():
    parser = argparse.ArgumentParser(description='Hybrid LLM-Powered Binary Decompiler')
    parser.add_argument('binary', help='Path to the binary file to decompile')
    parser.add_argument('--output', '-o', default='output', help='Output directory')
    parser.add_argument('--llm-provider', choices=['mock', 'openai', 'anthropic', 'local', 'iflow'],
                       default='mock', help='LLM provider to use')
    parser.add_argument('--arch', choices=['x86', 'x86_64', 'arm'],
                       default='x86', help='Target architecture')
    parser.add_argument('--no-sandbox', action='store_true',
                       help='Disable Docker sandboxing (less secure)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')

    args = parser.parse_args()

    # Set up logging
    log_level = getattr(logging, args.log_level)
    logger = get_decompiler_logger(args.output)
    logger.setLevel(log_level)

    logger.info("Starting Hybrid LLM-Powered Binary Decompiler")
    logger.info(f"Arguments: binary={args.binary}, output={args.output}, "
                f"llm_provider={args.llm_provider}, arch={args.arch}")

    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)

    # Initialize components
    logger.info("Initializing decompiler components...")

    try:
        # Storage
        storage = Store(output_path / "storage")

        # Binary loader
        loader = BinaryLoader(output_path / "binaries")

        # Disassembler
        disasm = Disassembler(arch=args.arch)

        # Analyzer
        analyzer = Analyzer(args.binary)

        # LLM client
        llm = LLMClient(provider=args.llm_provider)
        refiner = Refiner(llm)

        # Verifier
        verifier = CompileVerifier(use_docker_sandbox=not args.no_sandbox)

    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        logger.debug(traceback.format_exc())
        return 1

    # Load and analyze binary
    logger.info(f"Loading binary: {args.binary}")
    try:
        metadata = loader.ingest(args.binary)
        logger.info(f"Binary loaded with ID: {metadata['binary_id']}")
    except Exception as e:
        logger.error(f"Error loading binary: {e}")
        logger.debug(traceback.format_exc())
        return 1

    # Disassemble
    logger.info("Disassembling binary...")
    try:
        functions = disasm.extract_functions(args.binary)
        logger.info(f"Found {len(functions)} functions")
    except Exception as e:
        logger.error(f"Error during disassembly: {e}")
        logger.debug(traceback.format_exc())
        return 1

    # Analyze functions
    logger.info("Analyzing functions...")
    analyzed_functions = []
    for i, func in enumerate(functions):
        try:
            analyzed_func = analyzer.analyze_function(func)
            analyzed_functions.append(analyzed_func)
            if (i + 1) % 10 == 0 or i + 1 == len(functions):
                logger.info(f"Analyzed function {i+1}/{len(functions)}")
        except Exception as e:
            logger.warning(f"Error analyzing function {i}: {e}")
            logger.debug(traceback.format_exc())
            analyzed_functions.append(func)  # Keep original if analysis fails

    # Refine with LLM
    logger.info("Refining with LLM...")
    refined_functions = []
    analysis_reports = []
    for i, func in enumerate(analyzed_functions):
        try:
            # Generate C code
            refined_func = refiner.refine(func)
            refined_functions.append(refined_func)

            # Generate analysis report
            analysis_report = refiner.analyze(func)
            analysis_reports.append(analysis_report)

            if (i + 1) % 10 == 0 or i + 1 == len(analyzed_functions):
                logger.info(f"Refined function {i+1}/{len(analyzed_functions)}")

            # Save refined function (code only)
            storage.save_function(metadata['binary_id'], f"func_{i}_refined", refined_func)

            # Save analysis report separately
            storage.save_function(metadata['binary_id'], f"func_{i}_analysis", analysis_report)
        except Exception as e:
            logger.warning(f"Error refining function {i}: {e}")
            logger.debug(traceback.format_exc())
            refined_functions.append({
                "code": "// Error during LLM refinement",
                "confidence": 0.0,
                "edits": [],
                "recompilable": False,
                "explanations": f"Error: {str(e)}"
            })
            analysis_reports.append({
                "analysis": f"// Error during LLM analysis: {str(e)}",
                "confidence": 0.0,
                "findings": [],
                "vulnerabilities": []
            })

    # Verify results
    logger.info("Verifying results...")
    verification_results = []
    for i, refined_func in enumerate(refined_functions):
        if refined_func.get('code'):
            try:
                # Safety check
                safety_result = verifier.run_safety_check(refined_func['code'])
                logger.debug(f"Function {i} safety check: {safety_result['safety_status']}")

                # Compilation check
                compile_result = verifier.compile_c(refined_func['code'])
                logger.debug(f"Function {i} compilation: {compile_result['status']}")

                # Semantic verification (simplified)
                semantic_result = verifier.verify_semantics(args.binary, refined_func['code'])

                verification_result = {
                    'function_index': i,
                    'safety': safety_result,
                    'compilation': compile_result,
                    'semantics': semantic_result,
                    'confidence': refined_func.get('confidence', 0.0)
                }

                verification_results.append(verification_result)
                if (i + 1) % 10 == 0 or i + 1 == len(refined_functions):
                    logger.info(f"Verified function {i+1}/{len(refined_functions)}")

                # Save verification result
                storage.save_function(metadata['binary_id'], f"func_{i}_verification", verification_result)
            except Exception as e:
                logger.warning(f"Error verifying function {i}: {e}")
                logger.debug(traceback.format_exc())
                verification_results.append({
                    'function_index': i,
                    'error': str(e)
                })

    # Generate final report
    logger.info("Generating final report...")
    report = {
        'binary_metadata': metadata,
        'total_functions': len(functions),
        'analyzed_functions': len(analyzed_functions),
        'refined_functions': len(refined_functions),
        'verification_results': verification_results,
        'summary': {
            'successful_compilations': sum(1 for v in verification_results
                                         if 'compilation' in v and v['compilation']['status'] == 'pass'),
            'safe_functions': sum(1 for v in verification_results
                                if 'safety' in v and v['safety']['safety_status'] == 'safe'),
            'average_confidence': sum(v.get('confidence', 0) for v in refined_functions) / len(refined_functions) if refined_functions else 0
        }
    }

    # Save report
    report_path = output_path / "decompilation_report.json"
    try:
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        logger.debug(traceback.format_exc())

    # Save refined code to files
    code_output_dir = output_path / "decompiled_code"
    code_output_dir.mkdir(exist_ok=True)

    saved_files = 0
    for i, refined_func in enumerate(refined_functions):
        if refined_func.get('code'):
            try:
                code_file = code_output_dir / f"function_{i}.c"
                with open(code_file, 'w') as f:
                    f.write(refined_func['code'])
                saved_files += 1
                if saved_files % 10 == 0:
                    logger.debug(f"Saved {saved_files} decompiled functions")
            except Exception as e:
                logger.warning(f"Error saving function {i}: {e}")

    logger.info(f"Saved {saved_files} decompiled functions to: {code_output_dir}")

    # Save analysis reports to files
    analysis_output_dir = output_path / "analysis_reports"
    analysis_output_dir.mkdir(exist_ok=True)

    saved_reports = 0
    for i, analysis_report in enumerate(analysis_reports):
        if analysis_report.get('analysis'):
            try:
                report_file = analysis_output_dir / f"function_{i}_analysis.md"
                with open(report_file, 'w') as f:
                    f.write(analysis_report['analysis'])
                saved_reports += 1
            except Exception as e:
                logger.warning(f"Error saving analysis report {i}: {e}")

    logger.info(f"Saved {saved_reports} analysis reports to: {analysis_output_dir}")

    # Print summary
    print(f"\nDecompilation complete!")
    print(f"Report saved to: {report_path}")
    print(f"Decompiled code saved to: {code_output_dir}")
    print(f"Summary:")
    print(f"  - Functions processed: {report['total_functions']}")
    print(f"  - Successfully compiled: {report['summary']['successful_compilations']}")
    print(f"  - Safe functions: {report['summary']['safe_functions']}")
    print(f"  - Average confidence: {report['summary']['average_confidence']:.2f}")

    logger.info("Decompilation complete")
    return 0

if __name__ == '__main__':
    sys.exit(main())