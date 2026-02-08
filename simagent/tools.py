import os
import re
from dataclasses import dataclass


@dataclass
class ToolResult:
    ok: bool
    output: str


def list_files(repo_path: str, subdir: str | None = None, limit: int = 200) -> ToolResult:
    base = os.path.join(repo_path, subdir) if subdir else repo_path
    if not os.path.exists(base):
        return ToolResult(ok=False, output=f"Path not found: {base}")
    entries = []
    for root, dirs, files in os.walk(base):
        if ".git" in root:
            continue
        rel_root = os.path.relpath(root, repo_path)
        for name in sorted(dirs + files):
            entries.append(os.path.join(rel_root, name))
            if len(entries) >= limit:
                break
        if len(entries) >= limit:
            break
    output = "\n".join(entries) if entries else "(empty)"
    return ToolResult(ok=True, output=output)


def read_file(repo_path: str, path: str, max_chars: int = 8000) -> ToolResult:
    full_path = os.path.join(repo_path, path)
    if not os.path.exists(full_path):
        return ToolResult(ok=False, output=f"File not found: {path}")
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as handle:
            data = handle.read(max_chars)
    except OSError as exc:
        return ToolResult(ok=False, output=str(exc))
    return ToolResult(ok=True, output=data)


def write_file(repo_path: str, path: str, content: str) -> ToolResult:
    full_path = os.path.join(repo_path, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    try:
        with open(full_path, "w", encoding="utf-8") as handle:
            handle.write(content)
    except OSError as exc:
        return ToolResult(ok=False, output=str(exc))
    return ToolResult(ok=True, output=f"Wrote {len(content)} bytes to {path}")


def search(repo_path: str, pattern: str, limit: int = 20) -> ToolResult:
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return ToolResult(ok=False, output=f"Invalid regex: {exc}")
    matches = []
    for root, _, files in os.walk(repo_path):
        if ".git" in root:
            continue
        for name in files:
            full_path = os.path.join(root, name)
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as handle:
                    for idx, line in enumerate(handle, start=1):
                        if regex.search(line):
                            rel_path = os.path.relpath(full_path, repo_path)
                            matches.append(f"{rel_path}:{idx}: {line.strip()}")
                            if len(matches) >= limit:
                                return ToolResult(ok=True, output="\n".join(matches))
            except OSError:
                continue
    output = "\n".join(matches) if matches else "(no matches)"
    return ToolResult(ok=True, output=output)
