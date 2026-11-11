from __future__ import annotations

import posixpath
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Union
from xml.etree import ElementTree as ET

from .text import words_from_text

PathLike = Union[str, Path]

_CONTAINER_NS = {"ocf": "urn:oasis:names:tc:opendocument:xmlns:container"}
_OPF_NS = {"opf": "http://www.idpf.org/2007/opf"}


class EpubError(ValueError):
    """Raised when an EPUB cannot be opened or has no readable text."""


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "svg", "head"}:
            self._skip_depth += 1
        elif lowered in {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr", "blockquote"}:
            self._chunks.append(" ")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"script", "style", "svg", "head"} and self._skip_depth:
            self._skip_depth -= 1
        elif lowered in {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "blockquote"}:
            self._chunks.append(" ")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0 and data:
            self._chunks.append(data)

    def text(self) -> str:
        return " ".join("".join(self._chunks).split())


def _text_from_html(raw: bytes) -> str:
    parser = _VisibleTextParser()
    try:
        parser.feed(raw.decode("utf-8"))
    except UnicodeDecodeError:
        parser.feed(raw.decode("utf-8", errors="ignore"))
    parser.close()
    return parser.text()


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _find_opf_path(zf: zipfile.ZipFile) -> str:
    try:
        container = zf.read("META-INF/container.xml")
    except KeyError as exc:
        raise EpubError("EPUB is missing META-INF/container.xml") from exc
    try:
        root = ET.fromstring(container)
    except ET.ParseError as exc:
        raise EpubError("EPUB container.xml is not valid XML") from exc
    path = None
    for node in root.findall(".//ocf:rootfile", _CONTAINER_NS):
        media = node.attrib.get("media-type", "")
        if media in {"", "application/oebps-package+xml"}:
            path = node.attrib.get("full-path")
            if path:
                break
    if not path:
        for node in root.iter():
            if _local(node.tag) == "rootfile":
                path = node.attrib.get("full-path")
                if path:
                    break
    if not path:
        raise EpubError("EPUB container.xml does not name a package document")
    return posixpath.normpath(path)


def _spine_hrefs(zf: zipfile.ZipFile, opf_path: str) -> list[str]:
    try:
        opf = zf.read(opf_path)
    except KeyError as exc:
        raise EpubError(f"EPUB is missing the package document {opf_path}") from exc
    try:
        root = ET.fromstring(opf)
    except ET.ParseError as exc:
        raise EpubError("EPUB package document is not valid XML") from exc

    manifest: dict[str, str] = {}
    for item in root.iter():
        if _local(item.tag) != "item":
            continue
        item_id = item.attrib.get("id")
        href = item.attrib.get("href")
        if item_id and href:
            manifest[item_id] = href

    hrefs: list[str] = []
    seen: set[str] = set()
    base = posixpath.dirname(opf_path)
    for itemref in root.iter():
        if _local(itemref.tag) != "itemref":
            continue
        href = manifest.get(itemref.attrib.get("idref", ""))
        if not href:
            continue
        full = posixpath.normpath(posixpath.join(base, href) if base else href)
        if full not in seen:
            seen.add(full)
            hrefs.append(full)
    if not hrefs:
        raise EpubError("EPUB spine is empty or does not match the manifest")
    return hrefs


def words_from_epub(path: PathLike) -> int:
    """Count whitespace-separated words in an EPUB spine."""
    epub_path = Path(path)
    if not epub_path.is_file():
        raise EpubError(f"EPUB not found: {epub_path}")
    try:
        zf = zipfile.ZipFile(epub_path)
    except zipfile.BadZipFile as exc:
        raise EpubError(f"Not a valid EPUB (zip) file: {epub_path}") from exc

    with zf:
        names = set(zf.namelist())
        if "META-INF/encryption.xml" in names:
            raise EpubError(
                "This EPUB appears to be copy-protected and cannot be counted"
            )
        opf_path = _find_opf_path(zf)
        total = 0
        for href in _spine_hrefs(zf, opf_path):
            if href not in names:
                continue
            lowered = href.lower()
            if not lowered.endswith((".xhtml", ".html", ".htm", ".xml")):
                continue
            try:
                raw = zf.read(href)
            except KeyError:
                continue
            total += words_from_text(_text_from_html(raw))
    return total
