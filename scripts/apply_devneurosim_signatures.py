#!/usr/bin/env python3
# AUTH:DEVNEUROSIM:7A3F9E2B | scripts/apply_devneurosim_signatures.py
"""
Prepend AUTH:DEVNEUROSIM:7A3F9E2B marker to important source files under Legacy/ and NaturalCompute/.
Skips obj/, bin/, .pytest_cache, __pycache__, *.g.cs (generated), wpftmp.
Re-run after adding files; idempotent (skips if marker already present).
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = "AUTH:DEVNEUROSIM:7A3F9E2B"

SKIP_DIR_NAMES = {
    "obj",
    "bin",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".git",
    ".venv",
    "venv",
    ".cursor",
}
SKIP_FILE_SUFFIXES = (".g.cs",)  # WPF / generated


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIR_NAMES:
        return True
    name = path.name
    if name.endswith(SKIP_FILE_SUFFIXES):
        return True
    if "wpftmp" in name:
        return True
    return False


def comment_line(path: Path, style: str) -> str:
    rel = path.relative_to(ROOT).as_posix()
    payload = f"{MARKER} | {rel}"
    if style == "hash":
        return f"# {payload}\n"
    if style == "slash":
        return f"// {payload}\n"
    if style == "xml":
        return f"<!-- {payload} -->\n"
    if style == "plain":
        return f"{payload}\n\n"
    raise ValueError(style)


def _header_already_signed(body: str) -> bool:
    """True if an auth signature line is already in the file header (not e.g. inside docstrings)."""
    for line in body.split("\n")[:16]:
        s = line.strip()
        if s.startswith("# AUTH:DEVNEUROSIM:7A3F9E2B |"):
            return True
        if s.startswith("// AUTH:DEVNEUROSIM:7A3F9E2B |"):
            return True
        if "AUTH:DEVNEUROSIM:7A3F9E2B |" in s and s.startswith("<!--"):
            return True
        if s.startswith("AUTH:DEVNEUROSIM:7A3F9E2B |"):
            return True
    return False


def prepend_to_text(path: Path, style: str, body: str) -> str | None:
    if _header_already_signed(body):
        return None
    sig = comment_line(path, style)
    if style == "plain":
        return sig + body
    if style == "hash" and body.startswith("#!"):
        nl = body.find("\n")
        if nl == -1:
            return sig + body
        return body[: nl + 1] + sig + body[nl + 1 :]
    if style == "xml" and body.lstrip().startswith("<?xml"):
        nl = body.find("\n")
        if nl == -1:
            return sig + body
        return body[: nl + 1] + sig + body[nl + 1 :]
    return sig + body


def process_file(path: Path) -> bool:
    suf = path.suffix.lower()
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    style: str | None = None
    if suf in (".py", ".ps1", ".toml"):
        style = "hash"
    elif suf in (".cs", ".cpp", ".h", ".c"):
        style = "slash"
    elif suf in (".xaml", ".csproj"):
        style = "xml"
    elif suf == ".sh":
        style = "hash"
    elif suf == ".md":
        style = "xml"
    elif suf == ".txt":
        if path.name == "CMakeLists.txt":
            style = "hash"
        elif path.name.upper().startswith("README") and path.suffix.lower() == ".txt":
            style = "plain"
        else:
            return False
    elif suf in (".yml", ".yaml"):
        style = "hash"
    else:
        return False
    new = prepend_to_text(path, style, text)
    if new is None:
        return False
    path.write_text(new, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    roots = [ROOT, ROOT / "Legacy", ROOT / "NaturalCompute", ROOT / "scripts"]
    patterns = (
        "*.py",
        "*.cs",
        "*.xaml",
        "*.csproj",
        "*.ps1",
        "*.toml",
        "*.sh",
        "*.md",
        "*.txt",
        "*.yml",
        "*.yaml",
    )
    touched = 0
    for base in roots:
        if not base.is_dir():
            continue
        for pat in patterns:
            for path in base.rglob(pat):
                if not path.is_file():
                    continue
                if should_skip(path):
                    continue
                if process_file(path):
                    touched += 1
    print(f"Signed {touched} files ({MARKER})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
