from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def detect_encoding(raw: bytes) -> str:
    """Detect text encoding with BOM precedence, strict UTF-8, GBK, Big5, and fallback."""
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if raw.startswith(b"\xff\xfe"):
        return "utf-16-le"
    if raw.startswith(b"\xfe\xff"):
        return "utf-16-be"

    for enc in ("utf-8", "gbk", "big5"):
        try:
            raw.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def read_file_text(file_path: Path) -> tuple[str, str]:
    """Read file content with auto-detected encoding."""
    raw = file_path.read_bytes()
    enc = detect_encoding(raw)
    try:
        text = raw.decode(enc)
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")
        enc = "utf-8"
    return text, enc


def discover_files(source_dir: Path) -> list[Path]:
    """Discover text and structured document files in target directory."""
    extensions = {".md", ".txt", ".json", ".yaml", ".yml"}
    files = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.suffix.lower() in extensions:
            files.append(path)
    return files


def parse_markdown(content: str, default_title: str = "导入章节") -> list[dict[str, Any]]:
    """Parse Markdown content into structured chapters and scenes."""
    chapters: list[dict[str, Any]] = []
    curr_chapter: dict[str, Any] | None = None
    curr_scene_title = "导入场景"
    curr_scene_lines: list[str] = []

    def flush_scene():
        nonlocal curr_scene_lines, curr_scene_title
        content_text = "\n".join(curr_scene_lines).strip()
        if curr_chapter is not None:
            if content_text or (curr_scene_title != "导入场景"):
                curr_chapter["scenes"].append({
                    "title": curr_scene_title or "导入场景",
                    "content": content_text,
                })
        curr_scene_lines = []
        curr_scene_title = "导入场景"

    for line in content.splitlines():
        if line.startswith("# "):
            flush_scene()
            if curr_chapter and curr_chapter["scenes"]:
                chapters.append(curr_chapter)
            elif curr_chapter and not curr_chapter["scenes"]:
                # If previous chapter had no scenes, still retain or merge
                chapters.append(curr_chapter)
            curr_chapter = {"title": line[2:].strip() or default_title, "scenes": []}
        elif line.startswith("## "):
            if curr_chapter is None:
                curr_chapter = {"title": default_title, "scenes": []}
            flush_scene()
            curr_scene_title = line[3:].strip() or "导入场景"
        else:
            if curr_chapter is None:
                curr_chapter = {"title": default_title, "scenes": []}
            curr_scene_lines.append(line)

    flush_scene()
    if curr_chapter:
        chapters.append(curr_chapter)
    elif content.strip():
        chapters.append({"title": default_title, "scenes": [{"title": "导入场景", "content": content.strip()}]})
    return chapters


def parse_json_document(content: str, default_title: str = "导入章节") -> list[dict[str, Any]]:
    """Parse JSON document supporting chapter and scene structures."""
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "chapters" in data and isinstance(data["chapters"], list):
            return data["chapters"]
    except json.JSONDecodeError:
        pass
    return [{"title": default_title, "scenes": [{"title": "导入场景", "content": content}]}]


def parse_yaml_document(content: str, default_title: str = "导入章节") -> list[dict[str, Any]]:
    """Parse YAML document supporting chapter/scene structures or key-value scenes."""
    chapters: list[dict[str, Any]] = []
    try:
        import yaml
        data = yaml.safe_load(content)
        if isinstance(data, dict) and "chapters" in data and isinstance(data["chapters"], list):
            return data["chapters"]
    except Exception:
        pass
    return parse_markdown(content, default_title=default_title)


def parse_txt_document(content: str, default_title: str = "导入章节") -> list[dict[str, Any]]:
    """Parse plain text document, checking for chapter markings or paragraph grouping."""
    import re
    chapter_pattern = re.compile(r"^(?:第[0-9一二三四五六七八九十百千]+[卷章节回部]|Chapter\s+[0-9]+)\s*(.*)$", re.IGNORECASE)
    lines = content.splitlines()
    chapters: list[dict[str, Any]] = []
    curr_title = default_title
    curr_lines: list[str] = []

    for line in lines:
        match = chapter_pattern.match(line.strip())
        if match:
            if curr_lines:
                chapters.append({"title": curr_title, "scenes": [{"title": "导入场景", "content": "\n".join(curr_lines).strip()}]})
                curr_lines = []
            curr_title = line.strip() or default_title
        else:
            curr_lines.append(line)

    if curr_lines:
        chapters.append({"title": curr_title, "scenes": [{"title": "导入场景", "content": "\n".join(curr_lines).strip()}]})
    elif not chapters and content.strip():
        chapters.append({"title": default_title, "scenes": [{"title": "导入场景", "content": content.strip()}]})
    return chapters


def parse_document_file(file_path: Path) -> tuple[list[dict[str, Any]], str]:
    """Parse document file by suffix into structured chapters and scenes with detected encoding."""
    text, enc = read_file_text(file_path)
    stem = file_path.stem or "导入章节"
    ext = file_path.suffix.lower()

    if ext == ".md":
        return parse_markdown(text, default_title=stem), enc
    if ext == ".json":
        return parse_json_document(text, default_title=stem), enc
    if ext in {".yaml", ".yml"}:
        return parse_yaml_document(text, default_title=stem), enc
    return parse_txt_document(text, default_title=stem), enc
