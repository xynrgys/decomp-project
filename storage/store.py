"""Lightweight storage wrapper for artifacts and metrics.
"""
from pathlib import Path
import json

class Store:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save_function(self, binary_id: str, fn_id: str, function_json: dict):
        out = self.root / binary_id
        out.mkdir(parents=True, exist_ok=True)
        (out / f'{fn_id}.json').write_text(json.dumps(function_json))

    def load_function(self, binary_id: str, fn_id: str):
        p = self.root / binary_id / f'{fn_id}.json'
        return json.loads(p.read_text())