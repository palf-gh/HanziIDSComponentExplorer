# -*- coding: utf-8 -*-
"""
Yi Bai IDS provider for Hanzi Component Explorer RS+.

Bundles yi-bai/ids (MIT) with the plugin and converts Bai-style IDS notation
into the compact form used by HanziCore. Converted data is cached locally for
faster subsequent launches; normal use requires no network access.

Source: https://github.com/yi-bai/ids
"""

from __future__ import division, print_function, unicode_literals

import os
import re
import gzip
import pickle
from pathlib import Path

YIBAI_REPO = "https://github.com/yi-bai/ids"
CACHE_VERSION = 2

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


def bundled_path(level=1):
    """Return the Yi Bai IDS text bundled inside the plugin."""
    level = int(level)
    if level not in (0, 1, 2):
        raise ValueError("Yi Bai IDS level must be 0, 1, or 2")
    return Path(__file__).parent / "data" / "yi-bai" / ("ids_lv%d.txt" % level)


def compiled_cache_path(level=1):
    return cache_dir() / ("yi-bai-ids-v%d-lv%d.pdata" % (CACHE_VERSION, int(level)))


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


def _variant_indicators(sequence):
    """Return the trailing Bai IDS variant indicators without IDS syntax tags.

    A sequence such as ``⿰虫単(J)`` has the regional indicator ``J``.  The
    IDS syntax itself can also contain parenthesised hash expressions, for
    example ``#(T)(.)``.  Only parenthesis groups after the expression are
    indicators, so a group directly preceded by ``#`` is left untouched.
    """
    indicators = []
    remaining = (sequence or "").strip()
    while remaining.endswith(")"):
        match = re.search(r"\(([^()]*)\)$", remaining)
        if not match or match.start() > 0 and remaining[match.start() - 1] == "#":
            break
        indicators.insert(0, match.group(1).strip())
        remaining = remaining[:match.start()].rstrip()
    return indicators


def _parse_variants(field, group):
    """Parse every semicolon-separated IDS variant in one source column."""
    variants = []
    for item in _split_variants(field):
        cleaned = clean_bai_ids(item)
        if cleaned:
            variants.append(
                {
                    "ids": cleaned,
                    "indicators": _variant_indicators(item),
                    "group": group,
                }
            )
    return variants


def parse_text(text):
    """
    Parse Yi Bai IDS text into HanziCore's pdata-compatible dictionary.

    Every primary and alternative IDS is retained in ``ids_variants``.  The
    legacy ``ids_1`` / ``ids_2`` fields remain populated for compatibility with
    the existing CHISE-oriented code paths.
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

        variants = _parse_variants(cols[1] if len(cols) > 1 else "", "primary")
        variants.extend(_parse_variants(cols[2] if len(cols) > 2 else "", "alternative"))

        # Several source variants can normalise to the same compact IDS. Keep
        # one page for that IDS but retain every attached regional annotation.
        unique_variants = []
        variant_by_ids = {}
        for variant in variants:
            existing = variant_by_ids.get(variant["ids"])
            if existing is None:
                existing = dict(variant)
                existing["indicators"] = list(variant.get("indicators", []))
                variant_by_ids[variant["ids"]] = existing
                unique_variants.append(existing)
            else:
                for indicator in variant.get("indicators", []):
                    if indicator not in existing["indicators"]:
                        existing["indicators"].append(indicator)

        ids_1 = unique_variants[0]["ids"] if unique_variants else ""
        ids_2 = unique_variants[1]["ids"] if len(unique_variants) > 1 else ""

        db[char] = {
            "unicode": ("%X" % ord(char[0])) if char else "",
            "char": char,
            "ids_1": ids_1,
            "ids_2": ids_2,
            "ids_variants": unique_variants,
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
    Load bundled Yi Bai IDS as HanziCore-compatible data.

    Yi Bai lv0/lv1/lv2 text files are shipped with the plugin, so normal use
    requires no network access. A converted gzip+pickle cache is kept in the
    user's cache directory so subsequent launches do not need to parse the
    full IDS text again. Stroke counts are borrowed from the bundled
    CHISE-derived database because Yi Bai IDS itself does not provide them.
    """
    raw = bundled_path(level)
    if not raw.exists():
        raise FileNotFoundError("Bundled Yi Bai IDS file not found: %s" % raw)
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
    return "Yi Bai IDS lv%d (bundled)" % int(level)
