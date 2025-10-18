"""Disassembly wrappers (Capstone) and optional angr lifter.
"""
from typing import List, Dict
import os
try:
    from capstone import *
    from capstone.x86 import *
    capstone_available = True
except ImportError:
    capstone_available = False

class Disassembler:
    """Produce FunctionJSON-like dicts from a binary file.
    """
    def __init__(self, arch='x86'):
        self.arch = arch
        if not capstone_available:
            raise ImportError("Capstone library not installed. Please install using: pip install capstone")

        # Initialize Capstone disassembler
        if arch == 'x86':
            self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        elif arch == 'x86_64':
            self.md = Cs(CS_ARCH_X86, CS_MODE_64)
        elif arch == 'arm':
            self.md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
        else:
            raise ValueError(f"Unsupported architecture: {arch}")

        self.md.detail = True  # Enable detailed information

    def disassemble_section(self, bytes_blob: bytes, addr: int = 0x400000) -> List[Dict]:
        """Return list of instruction dicts (addr, asm, mnemonic, operands)."""
        instructions = []

        try:
            for insn in self.md.disasm(bytes_blob, addr):
                operands = []
                if insn.operands:
                    for op in insn.operands:
                        if op.type == X86_OP_REG:
                            operands.append(f"%{insn.reg_name(op.value.reg)}")
                        elif op.type == X86_OP_IMM:
                            operands.append(f"0x{op.value.imm:x}")
                        elif op.type == X86_OP_MEM:
                            mem = op.value.mem
                            segment = f"%{insn.reg_name(mem.segment)}:" if mem.segment != 0 else ""
                            base = f"%{insn.reg_name(mem.base)}" if mem.base != 0 else ""
                            index = f",%{insn.reg_name(mem.index)}" if mem.index != 0 else ""
                            scale = f"*{mem.scale}" if mem.scale != 1 and mem.index != 0 else ""
                            disp = f"0x{mem.disp:x}" if mem.disp != 0 else ""
                            operands.append(f"{segment}[{base}{index}{scale}{disp}]")
                        else:
                            operands.append(f"<unknown operand type: {op.type}>")

                instruction = {
                    "addr": hex(insn.address),
                    "asm": insn.mnemonic + " " + insn.op_str,
                    "mnemonic": insn.mnemonic,
                    "operands": operands,
                    "bytes": insn.bytes.hex()
                }
                instructions.append(instruction)
        except Exception as e:
            # Fallback for cases where disassembly fails
            instructions.append({
                "addr": hex(addr),
                "asm": f"; Disassembly failed: {str(e)}",
                "mnemonic": "error",
                "operands": [],
                "bytes": bytes_blob.hex()[:32] + "..." if len(bytes_blob) > 16 else bytes_blob.hex()
            })

        return instructions

    def extract_functions(self, binary_path: str) -> List[Dict]:
        """Return FunctionJSON objects for each discovered function."""
        # Placeholder implementation - in a real implementation, this would
        # use angr or another analysis framework to identify functions
        functions = []

        try:
            with open(binary_path, 'rb') as f:
                binary_data = f.read()

            # Simple heuristic: create one function from the entry point
            # In a real implementation, this would use proper function detection
            function_json = {
                "fn_id": "entry_point",
                "bytes": binary_data.hex(),
                "instrs": self.disassemble_section(binary_data[:256], 0x400000),  # First 256 bytes
                "cfg": {"blocks": [], "edges": []},
                "stack_frame": {"vars": [], "sp_delta": 0},
                "xrefs": [],
                "heuristics": {"cc": "unknown", "possible_ret_types": []},
                "surrounding_symbols": []
            }
            functions.append(function_json)
        except Exception as e:
            # Return a minimal function object even if extraction fails
            functions.append({
                "fn_id": "unknown",
                "bytes": "",
                "instrs": [],
                "cfg": {"blocks": [], "edges": []},
                "stack_frame": {"vars": [], "sp_delta": 0},
                "xrefs": [],
                "heuristics": {"cc": "unknown", "possible_ret_types": []},
                "surrounding_symbols": []
            })

        return functions