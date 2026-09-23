#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modern Unicode IDC coverage used by Yi Bai IDS."""

import sys
from pathlib import Path

PLUGIN_RESOURCES = (
    Path(__file__).parent.parent
    / "HanziComponentExplorerRSplus.glyphsPlugin"
    / "Contents"
    / "Resources"
)
sys.path.insert(0, str(PLUGIN_RESOURCES))

from hanzi_core import HanziCore, IDC_ARITY, IDC_CHARS  # noqa: E402


def _core(records):
    return HanziCore(database=records, source_name="test")


def test_unicode_15_1_idc_arities():
    assert IDC_ARITY["⿼"] == 2
    assert IDC_ARITY["⿽"] == 2
    assert IDC_ARITY["⿾"] == 1
    assert IDC_ARITY["⿿"] == 1
    assert IDC_ARITY["㇯"] == 2
    for char in "⿼⿽⿾⿿㇯":
        assert char in IDC_CHARS


def test_modern_binary_idc_is_not_indexed_as_component():
    core = _core(
        {
            "X": {
                "unicode": "0058",
                "char": "X",
                "ids_1": "⿼口一",
                "ids_2": "",
                "strokes": None,
            }
        }
    )
    assert "⿼" not in core._component_index
    assert core.parse_ids("⿼口一")[0] == ["⿼", "口", "一"]


def test_modern_unary_idc_parses_one_operand():
    core = _core(
        {
            "X": {
                "unicode": "0058",
                "char": "X",
                "ids_1": "⿾木",
                "ids_2": "",
                "strokes": None,
            }
        }
    )
    assert core.parse_ids("⿾木")[0] == ["⿾", "木"]
