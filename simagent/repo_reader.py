import os
from dataclasses import dataclass
from typing import Iterable


DEFAULT_EXTENSIONS = {
    ".py", ".md", ".txt", ".toml", ".yaml", ".yml", ".json", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".kt", ".c", ".h", ".cpp", ".hpp", ".cs", ".rb", ".php",
}


@dataclass
class DocumentChunk:
    path: str
    start_line: int
    end_line: int
    content: str


class RepoReader:
    def __init__(self, repo_path: str, extensions: set[str] | None = None, max_file_kb: int = 512):
        self.repo_path = os.path.abspath(repo_path)
        self.extensions = extensions or DEFAULT_EXTENSIONS
        self.max_file_kb = max_file_kb

    def iter_files(self) -> Iterable[str]:
        for root, _, files in os.walk(self.repo_path):
            if ".git" in root:
                continue
            for name in files:
                _, ext = os.path.splitext(name)
                if ext.lower() not in self.extensions:
                    continue
                full_path = os.path.join(root, name)
                try:
                    size_kb = os.path.getsize(full_path) / 1024
                except OSError:
                    continue
                if size_kb > self.max_file_kb:
                    continue
                yield full_path

    def iter_chunks(self, lines_per_chunk: int = 200) -> Iterable[DocumentChunk]:
        for full_path in self.iter_files():
            rel_path = os.path.relpath(full_path, self.repo_path)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as handle:
                    lines = handle.readlines()
            except OSError:
                continue
            if not lines:
                continue
            for idx in range(0, len(lines), lines_per_chunk):
                chunk_lines = lines[idx: idx + lines_per_chunk]
                start_line = idx + 1
                end_line = idx + len(chunk_lines)
                yield DocumentChunk(
                    path=rel_path,
                    start_line=start_line,
                    end_line=end_line,
                    content="".join(chunk_lines),
                )
