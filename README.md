# LLMIngest

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![Python: 3.7+](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)

**LLMIngest** is a command-line utility that ingests a Git repository and formats its entire structure and contents into a single Markdown file. This makes it easy to generate **context-rich prompts for LLMs** like GPT, Claude, Gemini, or Llama.

The script respects `.gitignore` rules, keeping your context clean and free of unnecessary files or artifacts.

---

## Key Features

*   **LLM-Ready Context:** Generates a single-file output ready for LLM prompts.
*   **Local & Remote Repos:** Works with both local paths and remote Git URLs.
*   **Smart Ignoring:** Respects `.gitignore` and `.git/info/exclude` rules.
*   **Directory Tree:** Includes a `tree`-like view by default for easy navigation.
*   **Relative Paths:** Shows paths relative to the repository root, preserving structure.

---

## Quick Start

You can try LLMIngest immediately after cloning without the full installation:

```sh
# Ingest the current directory and generate context.md
python3 llmingest.py . -o context.md
```

---

## Installation & Setup

Follow these steps to install LLMIngest as a global command.

### 1. Clone the Repository

```sh
mkdir -p ~/tools
git clone https://github.com/rakshitx1/llmingest.git ~/tools/llmingest
```

### 2. Install Dependencies

```sh
cd ~/tools/llmingest
pip3 install -r requirements.txt
```

### 3. Make the Script Executable

```sh
chmod +x llmingest.py
```
The script uses `#!/usr/bin/env python3` so it runs with your default Python environment.

### 4. (Optional) Rename for Convenience

To run the command as `llmingest` instead of `llmingest.py`, rename the file:
```sh
mv llmingest.py llmingest
```

### 5. Add to Your PATH

*   **Bash (Linux / older macOS):**
    ```sh
    echo 'export PATH="$HOME/tools/llmingest:$PATH"' >> ~/.bashrc
    ```

*   **Zsh (default on modern macOS):**
    ```sh
    echo 'export PATH="$HOME/tools/llmingest:$PATH"' >> ~/.zshrc
    ```

### 6. Reload Your Shell

```sh
# Zsh
source ~/.zshrc

# Bash
source ~/.bashrc
```

You can now run `llmingest` from any directory.

---

## Usage

```sh
llmingest <source> [options]
```

### Examples

*   **Ingest a remote GitHub repo:**
    ```sh
    llmingest https://github.com/someuser/some-repo.git
    ```

*   **Ingest a local project to a Markdown file:**
    ```sh
    llmingest /path/to/my/project -o context.md
    ```

*   **Ingest the current directory:**
    ```sh
    llmingest .
    ```

*   **Ingest content only (skip directory tree):**
    ```sh
    llmingest . --no-tree
    ```

---

### Command-line Options

| Option          | Description                                 |
| --------------- | ------------------------------------------- |
| `source`        | (Required) Git repository URL or local path |
| `-o, --output`  | Output file name (default: `digest.md`)     |
| `--no-tree`     | Skip printing the directory tree            |
| `-v, --verbose` | Enable verbose logging                      |
| `-h, --help`    | Show help message                           |

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
