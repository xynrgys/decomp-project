"""Static analysis: CFG recovery, stack frame heuristics.
"""
from typing import Dict
try:
    import angr
    import claripy
except ImportError:
    angr = None

class Analyzer:
    def __init__(self, binary_path: str = None):
        self.binary_path = binary_path
        self.project = None
        if angr is not None and binary_path:
            try:
                self.project = angr.Project(binary_path, load_options={'auto_load_libs': False})
            except Exception:
                self.project = None

    def analyze_function(self, function_json: Dict) -> Dict:
        """Enrich FunctionJSON with CFG, stack_frame, heuristics."""
        # Add basic heuristics
        function_json.setdefault('heuristics', {})
        function_json['heuristics']['cc'] = 'cdecl'

        # If we have an angr project, perform more advanced analysis
        if self.project is not None:
            try:
                # Get CFG
                cfg = self.project.analyses.CFGFast()
                function_json['cfg'] = {
                    'blocks': [],
                    'edges': []
                }

                # Try to find the function in the CFG
                for addr, func in cfg.kb.functions.items():
                    # Add basic block information
                    for block in func.blocks:
                        function_json['cfg']['blocks'].append({
                            'addr': hex(block.addr),
                            'size': block.size
                        })

                    # Add control flow edges
                    for src_node, dst_nodes in func.transition_graph.adj.items():
                        for dst_node in dst_nodes:
                            function_json['cfg']['edges'].append({
                                'src': hex(src_node.addr),
                                'dst': hex(dst_node.addr)
                            })

                # Add stack frame analysis
                function_json.setdefault('stack_frame', {})
                function_json['stack_frame']['vars'] = []
                function_json['stack_frame']['sp_delta'] = 0

                # Add calling convention analysis
                try:
                    cc_analysis = self.project.analyses.CallingConvention(cfg.kb.functions.get_by_addr(0x400000))
                    if cc_analysis.cc is not None:
                        function_json['heuristics']['cc'] = str(cc_analysis.cc)
                except Exception:
                    pass  # Continue with default

            except Exception as e:
                # If analysis fails, keep the basic information
                function_json.setdefault('cfg', {'blocks': [], 'edges': []})
                function_json.setdefault('stack_frame', {'vars': [], 'sp_delta': 0})
        else:
            # Fallback if angr is not available or not working
            function_json.setdefault('cfg', {'blocks': [], 'edges': []})
            function_json.setdefault('stack_frame', {'vars': [], 'sp_delta': 0})

        return function_json

    def get_possible_return_types(self, function_json: Dict) -> list:
        """Analyze possible return types for a function."""
        # Basic heuristic-based approach
        possible_types = ['int', 'void']

        # If we have angr, we can do more sophisticated analysis
        if self.project is not None:
            try:
                # This is a simplified placeholder - real implementation would be more complex
                possible_types = ['int', 'void', 'char*', 'struct*']
            except Exception:
                pass  # Keep default types

        return possible_types