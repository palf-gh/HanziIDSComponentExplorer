# -*- coding: utf-8 -*-
from pathlib import Path
import importlib.util


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "HanziComponentExplorerRSplus.glyphsPlugin"
    / "Contents"
    / "Resources"
    / "yibai_ids.py"
)
spec = importlib.util.spec_from_file_location("yibai_ids", MODULE_PATH)
yibai_ids = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yibai_ids)


def test_clean_bai_ids_removes_shape_qualifiers():
    assert yibai_ids.clean_bai_ids("⿰亻青.(.)") == "⿰亻青"
    assert yibai_ids.clean_bai_ids("⿱一.内P(.n)") == "⿱一内"


def test_clean_bai_ids_removes_variant_and_position_annotations():
    assert yibai_ids.clean_bai_ids("{一}#(T)(t)") == ""
    assert yibai_ids.clean_bai_ids("⿻[1:]亅⿱一.八d") == "⿻亅⿱一八"


def test_parse_text_maps_primary_and_alternative_ids():
    data = yibai_ids.parse_text(
        "上\t⿱⺊一.(.);⿱⺊一t(t)\t⿺丄.一.(.);⿺丄t一.(t)\n"
        "休\t⿰亻木.\n"
    )
    assert data["上"]["ids_1"] == "⿱⺊一"
    assert data["上"]["ids_2"] == "⿺丄一"
    assert data["休"]["ids_1"] == "⿰亻木"
    assert data["休"]["ids_2"] == ""


def test_parse_text_uses_first_nonempty_clean_variant():
    data = yibai_ids.parse_text("丶\t#(D)(.);{丶}#(S)(s)\n")
    assert data["丶"]["ids_1"] == ""


def test_parse_text_preserves_regional_variants_and_indicators():
    data = yibai_ids.parse_text("蝉\t⿰虫单(.);⿰虫単(J)\n")
    assert data["蝉"]["ids_variants"] == [
        {"ids": "⿰虫单", "indicators": ["."], "group": "primary"},
        {"ids": "⿰虫単", "indicators": ["J"], "group": "primary"},
    ]


def test_variant_indicators_ignore_hash_expression_syntax():
    assert yibai_ids._variant_indicators("#(H)(.)") == ["."]


def test_bundled_levels_exist():
    for level in (0, 1, 2):
        path = yibai_ids.bundled_path(level)
        assert path.exists()
        assert path.name == "ids_lv%d.txt" % level
