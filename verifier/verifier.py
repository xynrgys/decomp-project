"""Compile and runtime verification harness.
"""
from typing import Dict
import subprocess
import tempfile
import os
import shutil
import json

class CompileVerifier:
    def __init__(self, use_docker_sandbox: bool = True):
        self.use_docker_sandbox = use_docker_sandbox
        self.docker_available = self._check_docker()

    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            subprocess.run(['docker', '--version'], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def compile_c(self, code: str) -> Dict:
        """Attempt to compile code; return status and logs."""
        if self.use_docker_sandbox and self.docker_available:
            return self._compile_with_docker(code)
        else:
            return self._compile_without_sandbox(code)

    def _compile_without_sandbox(self, code: str) -> Dict:
        """Compile code without sandboxing (less secure)."""
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, 'candidate.c')
            binf = os.path.join(td, 'candidate')
            with open(src, 'w') as f:
                f.write(code)
            try:
                result = subprocess.run(['gcc', src, '-o', binf],
                                      check=True, capture_output=True, text=True, timeout=30)
                return {'status': 'pass', 'binary': binf, 'logs': result.stdout}
            except subprocess.CalledProcessError as e:
                return {'status': 'fail', 'logs': e.stderr}
            except subprocess.TimeoutExpired:
                return {'status': 'fail', 'logs': 'Compilation timed out'}

    def _compile_with_docker(self, code: str) -> Dict:
        """Compile code within a Docker sandbox for security."""
        try:
            # Create a temporary directory for the compilation
            with tempfile.TemporaryDirectory() as td:
                src = os.path.join(td, 'candidate.c')
                with open(src, 'w') as f:
                    f.write(code)

                # Create a simple Dockerfile for compilation
                dockerfile_content = '''
FROM gcc:latest
WORKDIR /app
COPY candidate.c .
RUN timeout 30s gcc candidate.c -o candidate 2>&1
'''
                dockerfile_path = os.path.join(td, 'Dockerfile')
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)

                # Build the Docker image
                image_name = 'decompiler_compile_sandbox'
                build_result = subprocess.run(
                    ['docker', 'build', '-t', image_name, '.'],
                    cwd=td, capture_output=True, text=True, timeout=120
                )

                if build_result.returncode != 0:
                    return {'status': 'fail', 'logs': f'Build failed: {build_result.stderr}'}

                # Run the container and extract the binary if compilation succeeded
                run_result = subprocess.run(
                    ['docker', 'run', '--rm', image_name, 'ls', '/app/candidate'],
                    capture_output=True, text=True, timeout=10
                )

                if run_result.returncode == 0:
                    # Compilation succeeded, extract the binary
                    extract_result = subprocess.run(
                        ['docker', 'create', image_name],
                        capture_output=True, text=True
                    )
                    container_id = extract_result.stdout.strip()

                    # Copy the binary out
                    binary_path = os.path.join(td, 'candidate')
                    copy_result = subprocess.run(
                        ['docker', 'cp', f'{container_id}:/app/candidate', binary_path],
                        capture_output=True, text=True
                    )

                    # Clean up the container
                    subprocess.run(['docker', 'rm', container_id], capture_output=True)

                    if copy_result.returncode == 0 and os.path.exists(binary_path):
                        return {'status': 'pass', 'binary': binary_path, 'logs': 'Compilation successful'}
                    else:
                        return {'status': 'fail', 'logs': 'Failed to extract binary'}
                else:
                    # Compilation failed, get error logs
                    logs_result = subprocess.run(
                        ['docker', 'run', '--rm', image_name, 'cat', '/app/candidate.c'],
                        capture_output=True, text=True
                    )
                    return {'status': 'fail', 'logs': f'Compilation failed: {logs_result.stderr}'}

        except subprocess.TimeoutExpired:
            return {'status': 'fail', 'logs': 'Compilation timed out in Docker'}
        except Exception as e:
            return {'status': 'fail', 'logs': f'Error during Docker compilation: {str(e)}'}

    def verify_semantics(self, original_binary: str, decompiled_code: str) -> Dict:
        """Verify that the decompiled code has the same semantics as the original."""
        # This is a simplified placeholder - real implementation would be much more complex
        # and might involve running both binaries with the same inputs and comparing outputs

        result = {
            'semantic_equivalence': 'unknown',
            'confidence': 0.0,
            'test_cases_run': 0,
            'passed': 0,
            'failed': 0
        }

        # Basic checks
        if not decompiled_code or not original_binary:
            result['semantic_equivalence'] = 'incomplete'
            return result

        # In a real implementation, we would:
        # 1. Compile the decompiled code
        # 2. Run both binaries with various test inputs
        # 3. Compare outputs
        # 4. Analyze execution traces
        # 5. Check for semantic differences

        # For now, we'll just do a basic check
        if 'main' in decompiled_code.lower():
            result['semantic_equivalence'] = 'partial'
            result['confidence'] = 0.3
        else:
            result['semantic_equivalence'] = 'unknown'

        return result

    def run_safety_check(self, code: str) -> Dict:
        """Check for potentially unsafe code patterns."""
        unsafe_patterns = [
            ('system\\(', 'Use of system() function'),
            ('exec', 'Use of exec family functions'),
            ('popen', 'Use of popen function'),
            ('shell', 'Shell invocation'),
            ('/bin/sh', 'Shell path reference'),
            ('eval', 'Use of eval function')
        ]

        issues = []
        for pattern, description in unsafe_patterns:
            if pattern.lower() in code.lower():
                issues.append(description)

        return {
            'safety_status': 'safe' if not issues else 'warning',
            'issues': issues,
            'unsafe_patterns_count': len(issues)
        }