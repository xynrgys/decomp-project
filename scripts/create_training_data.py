#!/usr/bin/env python3
"""
Create training data for fine-tuning LLMs on binary decompilation
"""
import json
import os
from pathlib import Path

def create_training_pairs():
    """Generate training pairs of (assembly, C_code) from source files"""

    # Sample training data structure
    training_examples = [
        {
            "instruction": "Convert the following disassembled code to C:",
            "input": {
                "disassembly": """
push    rbp
mov     rbp, rsp
mov     DWORD PTR [rbp-4], edi
mov     DWORD PTR [rbp-8], esi
mov     DWORD PTR [rbp-12], 0
mov     DWORD PTR [rbp-16], 0
jmp     .L2
.L3:
mov     eax, DWORD PTR [rbp-4]
imul    eax, DWORD PTR [rbp-16]
add     DWORD PTR [rbp-12], eax
add     DWORD PTR [rbp-16], 1
.L2:
mov     eax, DWORD PTR [rbp-16]
cmp     eax, DWORD PTR [rbp-8]
jl      .L3
mov     eax, DWORD PTR [rbp-12]
and     eax, 1
test    eax, eax
jne     .L4
add     DWORD PTR [rbp-12], 3
jmp     .L5
.L4:
sub     DWORD PTR [rbp-12], 2
.L5:
mov     eax, DWORD PTR [rbp-12]
pop     rbp
ret
""",
                "metadata": {
                    "arch": "x86_64",
                    "calling_convention": "System V AMD64",
                    "parameters": ["int a", "int b"],
                    "return_type": "int"
                }
            },
            "output": {
                "code": """int compute(int a, int b) {
    int result = 0;
    for (int i = 0; i < b; i++) {
        result += a * i;
    }
    if (result % 2 == 0) {
        result += 3;
    } else {
        result -= 2;
    }
    return result;
}""",
                "confidence": 0.95,
                "explanations": "Simple compute function with loop and conditional arithmetic"
            }
        }
    ]

    return training_examples

def create_fine_tuning_dataset():
    """Create dataset in various fine-tuning formats"""

    examples = create_training_pairs()

    # OpenAI fine-tuning format
    openai_format = []
    for ex in examples:
        openai_format.append({
            "messages": [
                {"role": "system", "content": "You are a binary decompiler assistant. Convert assembly to C code."},
                {"role": "user", "content": f"Convert to C:\n{ex['input']['disassembly']}"},
                {"role": "assistant", "content": ex['output']['code']}
            ]
        })

    # Save in different formats
    output_dir = Path("training_data")
    output_dir.mkdir(exist_ok=True)

    with open(output_dir / "openai_finetune.jsonl", "w") as f:
        for item in openai_format:
            f.write(json.dumps(item) + "\n")

    with open(output_dir / "examples.json", "w") as f:
        json.dump(examples, f, indent=2)

    print(f"Training data saved to {output_dir}/")
    print(f"Generated {len(examples)} training examples")

if __name__ == "__main__":
    create_fine_tuning_dataset()