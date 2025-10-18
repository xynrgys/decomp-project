# LLM Decompiler

A powerful decompilation tool that leverages Large Language Models (LLMs) to reverse engineer and decompile binary code into human-readable source code.

## Features

- **Advanced Decompilation**: Converts compiled binaries back into high-level source code
- **LLM-Powered Analysis**: Utilizes state-of-the-art language models for improved code reconstruction
- **Multiple Architecture Support**: Works with various CPU architectures
- **Interactive Mode**: Step through the decompilation process interactively
- **Plugin System**: Extensible architecture for adding new decompilation strategies

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- (Optional) CUDA for GPU acceleration

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/llm-decompiler.git
   cd llm-decompiler
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Unix or MacOS
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python decompile.py <binary_file> [options]
```

### Options

- `-o, --output`: Specify output file (default: stdout)
- `-a, --arch`: Target architecture (x86, x64, arm, etc.)
- `-v, --verbose`: Enable verbose output
- `--interactive`: Launch interactive decompilation session

### Example

```bash
python decompile.py example.exe -o decompiled.c
```

## Project Structure

```
.
├── src/                 # Source code
│   ├── core/           # Core decompilation logic
│   ├── llm/            # LLM integration
│   └── utils/          # Utility functions
├── tests/              # Test suite
├── examples/           # Example binaries and outputs
├── docs/               # Documentation
└── README.md           # This file
```

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all the open-source projects that made this possible
- Special thanks to our contributors

## Support

For support, please open an issue on our [GitHub Issues](https://github.com/yourusername/llm-decompiler/issues) page.
