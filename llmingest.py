#!/usr/bin/env python3
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
import argparse

# --- Dependencies ---
# pip install GitPython pathspec
import git
import pathspec

# --- Configuration ---

LANGUAGE_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php", ".html": "html",
    ".css": "css", ".scss": "scss", ".json": "json", ".xml": "xml", ".yml": "yaml",
    ".yaml": "yaml", ".md": "markdown", ".sh": "shell", ".bash": "bash",
    ".ps1": "powershell", ".sql": "sql", ".r": "r", ".kt": "kotlin",
    ".swift": "swift", ".dart": "dart", ".vue": "vue", ".svelte": "svelte",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini", ".txt": "text",
    "Dockerfile": "dockerfile",
    "Makefile": "makefile",
}

SEPARATOR = "=" * 50

# --- Helpers ---


def _get_language_identifier(file_path: Path) -> str:
  """Gets the Markdown language identifier for a file."""
  if file_path.name in LANGUAGE_MAP:
    return LANGUAGE_MAP[file_path.name]
  # Default to 'text' for unknown extensions to ensure proper code block formatting
  return LANGUAGE_MAP.get(file_path.suffix, "text")


def _format_file_content(file_path: Path, root_path: Path) -> Optional[str]:
  """Reads a file and formats it with a header and fenced code block."""
  try:
    content = file_path.read_text(encoding="utf-8")
    lang = _get_language_identifier(file_path)
    # Use the same relative path logic as the tree view for consistency
    relative_path = file_path.relative_to(root_path)
    return (
        f"{SEPARATOR}\n"
        f"FILE: {relative_path.as_posix()}\n"
        f"{SEPARATOR}\n"
        f"```{lang}\n"
        f"{content}\n"
        f"```\n"
    )
  except (UnicodeDecodeError, OSError):
    print(f"Skipping binary or unreadable file: {file_path}")
    return None


def _load_gitignore_patterns(root_path: Path) -> Optional[pathspec.PathSpec]:
  """Load ignore rules from .gitignore and .git/info/exclude if present."""
  patterns: List[str] = []
  gitignore_path = root_path / ".gitignore"
  exclude_path = root_path / ".git" / "info" / "exclude"

  if gitignore_path.is_file():
    patterns.extend(gitignore_path.read_text().splitlines())
  if exclude_path.is_file():
    patterns.extend(exclude_path.read_text().splitlines())

  if patterns:
    return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
  return None


def _build_ascii_tree(root_path: Path, spec: Optional[pathspec.PathSpec], display_root: str) -> str:
  """Builds a plain ASCII tree like the `tree` command."""
  lines: List[str] = []

  def walk(dir_path: Path, prefix: str = ""):
    entries: List[str] = []
    try:
      # Sort entries for consistent ordering
      entries = sorted(os.listdir(dir_path))
    except OSError:
      return

    filtered: List[str] = []
    for entry in entries:
      # Always ignore the .git directory
      if entry == ".git":
        continue

      path: Path = dir_path / entry
      rel_path_str = path.relative_to(root_path).as_posix()

      # Check against gitignore rules
      is_dir = path.is_dir()
      check_path = rel_path_str + '/' if is_dir else rel_path_str

      if spec and spec.match_file(check_path):
        continue
      filtered.append(entry)

    for i, entry in enumerate(filtered):
      connector = "└── " if i == len(filtered) - 1 else "├── "
      path: Path = dir_path / entry
      lines.append(f"{prefix}{connector}{entry}")
      if path.is_dir():
        extension = "    " if i == len(filtered) - 1 else "│   "
        walk(path, prefix + extension)

  lines.append(f"{display_root}/")
  walk(root_path)
  return "\n".join(lines)


def _process_directory(root_path: Path, display_root: str) -> Tuple[str, str]:
  """Walks a directory, generates a file tree, and formats file contents."""
  spec = _load_gitignore_patterns(root_path)
  tree_str = _build_ascii_tree(root_path, spec, display_root)

  content_blocks: List[str] = []
  for dirpath, _, filenames in os.walk(root_path):
    # Explicitly skip the .git directory to be safe
    if ".git" in dirpath.split(os.sep):
      continue

    current_path = Path(dirpath)
    for filename in filenames:
      file_path = current_path / filename
      rel_path = file_path.relative_to(root_path)
      if spec and spec.match_file(str(rel_path)):
        continue
      formatted_content = _format_file_content(file_path, root_path)
      if formatted_content:
        content_blocks.append(formatted_content)

  return tree_str, "\n".join(content_blocks)


def _get_contextual_display_path(path: Path) -> str:
  """Gets a path for display, including the git root directory name."""
  try:
    # Find the top-level directory of the Git repository
    repo = git.Repo(path, search_parent_directories=True)
    git_root_dir = repo.working_tree_dir
    if git_root_dir is None:
      raise git.InvalidGitRepositoryError("No working tree directory found.")
    git_root = Path(str(git_root_dir))

    # Calculate the path of the input directory relative to the Git root
    relative_to_git_root = path.relative_to(git_root)

    if str(relative_to_git_root) == '.':
      # If the input path is the Git root itself, just use its name
      return git_root.name
    else:
      # Otherwise, join the root's name with the relative path
      return f"{git_root.name}/{relative_to_git_root.as_posix()}"

  except git.InvalidGitRepositoryError:
    # If not in a git repo, fall back to the input directory's name
    return path.name


def ingest(source: str) -> str:
  """Ingests a Git repository from a URL or local path into a single Markdown string."""
  is_url = source.startswith("http") or source.startswith("git@")

  if is_url:
    temp_dir = tempfile.mkdtemp(prefix="gitingest_")
    print(f"Cloning {source} into {temp_dir}...")
    try:
      git.Repo.clone_from(source, temp_dir, depth=1)
      repo_path = Path(temp_dir)
      # For URLs, the repo name is the last part of the URL, without .git
      repo_name = Path(source).stem
      tree, content = _process_directory(repo_path, repo_name)
    finally:
      shutil.rmtree(temp_dir)
  else:
    repo_path = Path(source).resolve()
    if not repo_path.is_dir():
      raise ValueError(
          f"Local path not found or not a directory: {source}")
    print(f"Processing local directory: {repo_path}...")
    display_path = _get_contextual_display_path(repo_path)
    tree, content = _process_directory(repo_path, display_path)

  return (
      f"Directory structure:\n{tree}\n\n"
      f"File contents:\n\n{content}"
  )


# --- CLI Entry Point ---

def main():
  parser = argparse.ArgumentParser(
      description="LLMIngest: Export a repo's structure and contents into a single Markdown file for LLM context.",
      formatter_class=argparse.RawTextHelpFormatter
  )
  parser.add_argument(
      "source", help="Git repository URL or local path to ingest.")
  parser.add_argument(
      "-o", "--output", default="digest.md",
      help="Output markdown file (default: digest.md)"
  )
  parser.add_argument(
      "--no-tree", action="store_true",
      help="Skip printing the directory tree in the digest."
  )
  parser.add_argument(
      "-v", "--verbose", action="store_true",
      help="Enable verbose logging."
  )
  args = parser.parse_args()

  try:
    digest = ingest(args.source)
    if args.no_tree:
      digest = "\n".join(digest.split("\n\n", 1)[1:])

    with open(args.output, "w", encoding="utf-8") as f:
      f.write(digest)

    if args.verbose:
      print(f"Digest successfully saved to {args.output}")

  except Exception as e:
    parser.error(str(e))


if __name__ == "__main__":
  main()
