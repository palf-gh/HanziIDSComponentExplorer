# -*- coding: utf-8 -*-
"""
Yi Bai IDS provider for Hanzi Component Explorer RS+.

Downloads yi-bai/ids (MIT) on demand, stores the raw source in the user's
cache directory, and converts Bai-style IDS notation into the compact form
used by HanziCore.

Source: https://github.com/yi-bai/ids
"""

from __future__ import division, print_function, unicode_literals

import os
import re
import time
import gzip
import pickle
from pathlib import Path

try:
    from urllib.request import urlopen, Request
except ImportError:  # pragma: no cover
    from urllib2 import urlopen, Request


YIBAI_REPO = "https://github.com/yi-bai/ids"
YIBAI_RAW_URL = "https://raw.githubusercontent.com/yi-bai/ids/main/ids_lv{level}.txt"
CACHE_MAX_AGE = 7 * 24 * 60 * 60

_VARIANT_TAG_RE = re.compile(r"\{[^{}]*\}")
_BRACKET_RE = re.compile(r"\[[^\[\]]*\]")
_HASH_EXPR_RE = re.compile(r"#\([^()]*\)")
_PAREN_RE = re.compile(r"\([^()]*\)")
_ASCII_QUALIFIER_RE = re.compile(r"[A-Za-z0-9_:+\-]")
_DOT_RE = re.compile(r"[.・]")


def cache_dir():
    path = Path.home() / "Library" / "Caches" / "HanziComponentExplorerRSplus"
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_path(level=1):
    return cache_dir() / ("yi-bai-ids-lv%d.txt" % int(level))


def compiled_cache_path(level=1):
    return cache_dir() / ("yi-bai-ids-lv%d.pdata" % int(level))


def _is_cache_fresh(path, max_age=CACHE_MAX_AGE):
    try:
        return path.exists() and (time.time() - path.stat().st_mtime) < max_age
    except OSError:
        return False


def download(level=1, force=False, timeout=20):
    """Return local path to Yi Bai IDS source, downloading when necessary."""
    level = int(level)
    if level not in (0, 1, 2):
        raise ValueError("Yi Bai IDS level must be 0, 1, or 2")

    target = cache_path(level)
    if not force and _is_cache_fresh(target):
        return target

    url = YIBAI_RAW_URL.format(level=level)
    request = Request(url, headers={"User-Agent": "HanziComponentExplorerRSplus/1"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()

    if not payload:
        raise RuntimeError("Yi Bai IDS download returned an empty response")

    tmp = target.with_suffix(".tmp")
    with open(str(tmp), "wb") as f:
        f.write(payload)
    os.replace(str(tmp), str(target))
    return target


def _split_variants(field):
    if not field:
        return []
    # Bai IDS uses semicolons as variant separators. Entity syntax is not used
    # in the current data, so this remains deliberately conservative.
    return [part.strip() for part in field.split(";") if part.strip()]


def clean_bai_ids(sequence):
    """
    Convert Bai-style IDS notation to the subset HanziCore understands.

    Removes regional/shape qualifiers while preserving IDC and actual component
    characters. Examples:
      '⿰亻青.(.);...' -> '⿰亻青'
      '{一}#(T)(t)'   -> ''
      '⿻[1:]亅⿱...d' -> structural CJK/IDC characters only
    """
    if not sequence:
        return ""

    s = sequence.strip()
    s = _VARIANT_TAG_RE.sub("", s)
    s = _BRACKET_RE.sub("", s)

    # Hash expressions describe strokes rather than reusable components.
    previous = None
    while previous != s:
        previous = s
        s = _HASH_EXPR_RE.sub("", s)
        s = _PAREN_RE.sub("", s)

    s = _DOT_RE.sub("", s)
    s = _ASCII_QUALIFIER_RE.sub("", s)

    # Remove syntax punctuation and whitespace, retaining Unicode component
    # characters and IDC operators.
    s = "".join(ch for ch in s if not ch.isspace() and ch not in "{}[](),;#")
    return s


def _first_clean_variant(field):
    for item in _split_variants(field):
        cleaned = clean_bai_ids(item)
        if cleaned:
            return cleaned
    return ""


def parse_text(text):
    """
    Parse Yi Bai IDS text into HanziCore's pdata-compatible dictionary.

    The first primary IDS is mapped to ids_1 and the first distinct alternative
    IDS to ids_2. Full Bai variant preservation can be layered on later without
    changing this public shape.
    """
    db = {}
    for raw_line in text.splitlines():
        if not raw_line or raw_line.startswith("#"):
            continue

        cols = raw_line.split("\t")
        if not cols:
            continue

        char = cols[0].strip()
        if not char:
            continue

        primary = _first_clean_variant(cols[1] if len(cols) > 1 else "")
        alternative = _first_clean_variant(cols[2] if len(cols) > 2 else "")
        if alternative == primary:
            alternative = ""

        db[char] = {
            "unicode": ("%X" % ord(char[0])) if char else "",
            "char": char,
            "ids_1": primary,
            "ids_2": alternative,
            "strokes": None,
        }
    return db


def _merge_strokes(database, stroke_data_path):
    """Copy stroke counts from the bundled CHISE-derived pdata when available."""
    if not stroke_data_path:
        return database

    try:
        with gzip.open(str(stroke_data_path), "rb") as f:
            source = pickle.load(f)
    except Exception:
        return database

    if not isinstance(source, dict):
        return database

    for char, item in database.items():
        source_item = source.get(char)
        if isinstance(source_item, dict):
            item["strokes"] = source_item.get("strokes")
    return database


def _compiled_cache_is_current(compiled, raw, stroke_data_path=None):
    try:
        if not compiled.exists():
            return False
        compiled_mtime = compiled.stat().st_mtime
        newest_source = raw.stat().st_mtime
        if stroke_data_path:
            stroke_path = Path(stroke_data_path)
            if stroke_path.exists():
                newest_source = max(newest_source, stroke_path.stat().st_mtime)
        return compiled_mtime >= newest_source
    except OSError:
        return False


def load(level=1, force_refresh=False, stroke_data_path=None):
    """
    Load Yi Bai IDS as HanziCore-compatible data.

    The raw upstream text is cached for seven days. A converted gzip+pickle
    cache is kept separately so subsequent plugin launches do not need to
    parse roughly 100k IDS records again. Stroke counts are borrowed from the
    bundled CHISE-derived database because Yi Bai IDS itself does not provide
    stroke metadata.
    """
    raw = download(level=level, force=force_refresh)
    compiled = compiled_cache_path(level)

    if not force_refresh and _compiled_cache_is_current(
        compiled, raw, stroke_data_path
    ):
        try:
            with gzip.open(str(compiled), "rb") as f:
                cached = pickle.load(f)
            if isinstance(cached, dict):
                return cached
        except Exception:
            pass

    with open(str(raw), "r", encoding="utf-8") as f:
        database = parse_text(f.read())

    _merge_strokes(database, stroke_data_path)

    try:
        tmp = compiled.with_suffix(".tmp")
        with gzip.open(str(tmp), "wb") as f:
            pickle.dump(database, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(str(tmp), str(compiled))
    except Exception:
        # Cache failure must not prevent the plugin from working.
        pass

    return database


def source_label(level=1):
    return "Yi Bai IDS lv%d (zi.tools lineage)" % int(level)
