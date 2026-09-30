from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

import fitz

from .models import PaperRecord

DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19\d{2}|20\d{2}|2100)\b")
GENERIC_TITLES = {"untitled", "document", "microsoft word", "pdf", "paper"}
DEFAULT_RENAME_TEMPLATE = "{year}_{author}_{title}"
SUPPORTED_TEMPLATE_FIELDS = ("year", "author", "title", "doi")
TEMPLATE_TOKEN_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_doi(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value, flags=re.IGNORECASE)
    value = re.sub(r"^doi\s*:\s*", "", value, flags=re.IGNORECASE)
    match = DOI_RE.search(value)
    if not match:
        return ""
    return match.group(0).rstrip(".,;)]}").lower()


def _clean_text(value: str) -> str:
    return " ".join(value.replace("\x00", " ").split()).strip()


def _good_title(value: str) -> bool:
    value = _clean_text(value)
    if len(value) < 8 or len(value) > 260:
        return False
    lower = value.lower().strip(" .-_()")
    if lower in GENERIC_TITLES:
        return False
    if lower.startswith(("doi:", "http://", "https://", "arxiv:")):
        return False
    if DOI_RE.search(value):
        return False
    alpha = sum(ch.isalpha() for ch in value)
    return alpha >= 5


def _fallback_title(first_page_text: str) -> str:
    lines = [_clean_text(x) for x in first_page_text.splitlines()]
    lines = [x for x in lines if x]
    # Academic titles are usually near the top; score by length and reject boilerplate.
    candidates: list[tuple[int, str]] = []
    for idx, line in enumerate(lines[:25]):
        low = line.lower()
        if not _good_title(line):
            continue
        if any(token in low for token in ("abstract", "keywords", "copyright", "journal", "volume", "www.")):
            continue
        score = max(0, 20 - idx) + min(len(line), 140)
        candidates.append((score, line))
    if not candidates:
        return ""
    return max(candidates, key=lambda item: item[0])[1]


def _parse_authors(value: str) -> list[str]:
    value = _clean_text(value)
    if not value:
        return []
    parts = re.split(r"\s*(?:;|\band\b|\|)\s*", value, flags=re.IGNORECASE)
    cleaned = [p.strip(" ,") for p in parts if p.strip(" ,")]
    # Avoid exploding a single "Last, First" metadata author into two people.
    if len(cleaned) == 1:
        return cleaned
    return cleaned[:12]


def _extract_year(metadata: dict[str, str], text: str) -> str:
    for key in ("creationDate", "modDate", "subject", "keywords"):
        raw = metadata.get(key) or ""
        match = YEAR_RE.search(raw)
        if match:
            return match.group(1)
    years = YEAR_RE.findall(text[:12000])
    if years:
        return years[0]
    return ""


def safe_filename_component(value: str, max_len: int = 110) -> str:
    value = unicodedata.normalize("NFKC", value or "")
    value = value.replace("/", " ").replace("\\", " ")
    value = re.sub(r"[<>:\"|?*\x00-\x1F]", "", value)
    value = re.sub(r"\s+", " ", value).strip(" ._-\t\r\n")
    value = re.sub(r"[^\w\- .()\[\]]+", "", value, flags=re.UNICODE)
    value = re.sub(r"[ .]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_.")
    return value[:max_len] or "Untitled"


def surname_from_author(author: str) -> str:
    author = _clean_text(author)
    if not author:
        return "UnknownAuthor"
    if "," in author:
        surname = author.split(",", 1)[0]
    else:
        surname = author.split()[-1]
    return safe_filename_component(surname, 36)


def validate_rename_template(template: str) -> str:
    template = (template or "").strip()
    if not template:
        raise ValueError("命名模板不能为空")
    unknown = sorted(set(TEMPLATE_TOKEN_RE.findall(template)) - set(SUPPORTED_TEMPLATE_FIELDS))
    if unknown:
        allowed = "、".join(f"{{{name}}}" for name in SUPPORTED_TEMPLATE_FIELDS)
        raise ValueError(f"不支持的模板字段：{', '.join(unknown)}。可用字段：{allowed}")
    return template


def build_proposed_filename(record: PaperRecord, template: str = DEFAULT_RENAME_TEMPLATE) -> str:
    template = validate_rename_template(template)
    values = {
        "year": record.year,
        "author": surname_from_author(record.authors[0]) if record.authors else "",
        "title": record.title,
        "doi": record.doi,
    }

    rendered = TEMPLATE_TOKEN_RE.sub(lambda match: values.get(match.group(1), ""), template).strip()
    if rendered.lower().endswith(".pdf"):
        rendered = rendered[:-4]

    literal_text = TEMPLATE_TOKEN_RE.sub("", template)
    if not any(values.values()) and not re.search(r"[\w]", literal_text, re.UNICODE):
        return record.path.name

    stem = safe_filename_component(rendered, 165).rstrip("_.")
    if not stem or stem == "Untitled":
        return record.path.name
    return f"{stem}.pdf"


def extract_paper_record(path: Path, max_text_pages: int = 3) -> PaperRecord:
    path = Path(path)
    record = PaperRecord(
        path=path,
        size_bytes=path.stat().st_size,
        sha256=sha256_file(path),
    )
    try:
        with fitz.open(path) as doc:
            record.page_count = doc.page_count
            metadata = {k: (v or "") for k, v in (doc.metadata or {}).items()}
            chunks: list[str] = []
            for index in range(min(doc.page_count, max_text_pages)):
                try:
                    chunks.append(doc.load_page(index).get_text("text"))
                except Exception:
                    record.warnings.append(f"第 {index + 1} 页文本提取失败")
            text = "\n".join(chunks)

            meta_title = _clean_text(metadata.get("title", ""))
            record.title = meta_title if _good_title(meta_title) else _fallback_title(chunks[0] if chunks else "")
            record.authors = _parse_authors(metadata.get("author", ""))
            record.year = _extract_year(metadata, text)

            doi_sources = "\n".join(
                [
                    metadata.get("subject", ""),
                    metadata.get("keywords", ""),
                    metadata.get("title", ""),
                    text,
                ]
            )
            record.doi = normalize_doi(doi_sources)
    except Exception as exc:
        record.warnings.append(f"PDF 解析失败: {exc}")

    if not record.title:
        record.warnings.append("未可靠识别标题")
    if not record.authors:
        record.warnings.append("未可靠识别作者")
    if not record.year:
        record.warnings.append("未可靠识别年份")
    record.proposed_filename = build_proposed_filename(record)
    return record
