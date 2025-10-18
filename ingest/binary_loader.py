"""
Binary loader using LIEF.
"""
from pathlib import Path
import json
import uuid
try:
    import lief
except ImportError:
    lief = None

class BinaryLoader:
    """Load binary, extract metadata, and store under storage path."""
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def ingest(self, path: str) -> dict:
        """Ingest a binary file and return metadata with binary_id."""
        if lief is None:
            raise ImportError("LIEF library not installed. Please install using: pip install lief")

        binary_id = str(uuid.uuid4())
        outdir = self.storage_path / binary_id
        outdir.mkdir()
        dst = outdir / Path(path).name

        # Copy the binary file
        with open(path, 'rb') as f:
            binary_data = f.read()

        with open(dst, 'wb') as out:
            out.write(binary_data)

        # Analyze the binary with LIEF
        try:
            binary = lief.parse(path)
            metadata = {
                "binary_id": binary_id,
                "filename": dst.name,
                "arch": str(binary.header.architecture) if binary else "unknown",
                "format": str(binary.format) if binary else "unknown",
                "entrypoint": getattr(binary.header, 'entrypoint', 0),
                "has_nx": getattr(binary, 'has_nx', False),
                "is_pie": getattr(binary, 'is_pie', False),
                "imports": [str(lib.name) for lib in binary.imports] if hasattr(binary, 'imports') else [],
                "sections": [str(section.name) for section in binary.sections] if hasattr(binary, 'sections') else []
            }
        except Exception:
            # Fallback for binaries LIEF can't parse
            import os
            metadata = {
                "binary_id": binary_id,
                "filename": dst.name,
                "arch": "unknown",
                "format": "unknown",
                "entrypoint": 0,
                "has_nx": False,
                "is_pie": False,
                "imports": [],
                "sections": [],
                "original_size": os.path.getsize(path)
            }

        (outdir / 'metadata.json').write_text(json.dumps(metadata, indent=2))
        return metadata