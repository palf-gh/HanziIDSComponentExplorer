#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hanzi Component Explorer RS+ - 核心邏輯層
完全獨立的漢字分析引擎，無任何 UI 或 Glyphs 依賴

Original copyright © 2025 TzuYuan Yin
Fork modifications copyright © 2026 Ooma Kobayashi
Modified from the original upstream project.
"""

from __future__ import division, print_function, unicode_literals

import re
import gzip
import pickle
import unicodedata
from collections import Counter
from typing import Dict, List, Tuple, Union, Optional, Set
from pathlib import Path


# 錯誤訊息常數定義
ERROR_NO_MATCH_FOUND = "未找到符合的字符"
ERROR_UNKNOWN_CHAR = "未知字符"
ERROR_SEARCH_FAILED = "搜尋失敗"

# IDS 分隔字符 (Ideographic Description Characters)
IDC_CHARS = "⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻〾"

# 每個 IDC 帶的 operand 個數（IDS 標準）：
# 二元：⿰⿱⿴⿵⿶⿷⿸⿹⿺⿻；三元：⿲⿳；一元：〾（變體）
IDC_ARITY = {
    "⿰": 2,
    "⿱": 2,
    "⿲": 3,
    "⿳": 3,
    "⿴": 2,
    "⿵": 2,
    "⿶": 2,
    "⿷": 2,
    "⿸": 2,
    "⿹": 2,
    "⿺": 2,
    "⿻": 2,
    "〾": 1,
}

# 位置分組標籤的展示順序（IDC 主序、位置升序、≡ 在最後、direct before nested）
IDC_ORDER = "⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻〾∅"
MULTI_POSITION_MARKER = "≡"
NESTED_POSITION_MARKER = "·"
UNCLASSIFIED_LABEL = "∅"

# 應做 NFKC 正規化的 Unicode 區塊（CJK 相關變體）
# 康熙部首 (2F00-2FD5): ⽊→木
# CJK 相容字 BMP (F900-FAFF): 虜→虜
# CJK 相容字補充 SIP (2F800-2FA1F): 巢(U+2F882)→巢(U+5DE2)
_NFKC_RANGES = ((0x2F00, 0x2FD5), (0xF900, 0xFAFF), (0x2F800, 0x2FA1F))


def _skip_one_operand(tokens: List[str], pos: int) -> int:
    """跳過 tokens 從 pos 起的一個完整 operand（含遞迴子結構）。"""
    if pos >= len(tokens):
        return pos
    token = tokens[pos]
    arity = IDC_ARITY.get(token)
    if arity is None:
        return pos + 1
    pos += 1
    for _ in range(arity):
        pos = _skip_one_operand(tokens, pos)
    return pos


def _split_top_operands(tokens: List[str]) -> List[List[str]]:
    """將 IDS tokens 按頂層 IDC 切成 operands sub-list。"""
    if not tokens:
        return []
    arity = IDC_ARITY.get(tokens[0])
    if arity is None:
        return []
    operands: List[List[str]] = []
    pos = 1
    for _ in range(arity):
        if pos >= len(tokens):
            break
        start = pos
        pos = _skip_one_operand(tokens, pos)
        operands.append(tokens[start:pos])
    return operands


def resolve_display_char(
    char: Optional[str], sticky: Optional[str], current: Optional[str]
) -> Optional[str]:
    """決定右欄顯示字：明示參數 > sticky 右欄視角 > current 本字。"""
    if char is not None:
        return char
    return sticky or current


def _normalize_cjk_variant(char: str) -> str:
    """將 CJK 相關 Unicode 變體正規化為統一字，非 CJK 變體保持原樣"""
    if len(char) != 1:
        return char
    cp = ord(char)
    if any(start <= cp <= end for start, end in _NFKC_RANGES):
        normalized = unicodedata.normalize("NFKC", char)
        if len(normalized) == 1:
            return normalized
    return char


class HanziCore:
    """漢字部件分析核心引擎"""

    def __init__(
        self,
        data_path: Optional[str] = None,
        database: Optional[Dict[str, Dict[str, object]]] = None,
        source_name: Optional[str] = None,
    ):
        """
        初始化引擎並載入資料庫

        參數:
        data_path (Optional[str]): IDS 資料庫檔案路徑（.pdata 格式）
        database (Optional[Dict]): 已載入的 pdata 相容資料庫。
            指定時は data_path より優先し、外部 IDS provider を利用できる。
        source_name (Optional[str]): UI/診断用の資料源名称。
        """
        self.data_path = self._resolve_path(data_path) if data_path else None
        self.source_name = source_name or ("CHISE IDS" if data_path else "External IDS")
        self._parsed_ids_cache: Dict[str, List[List[str]]] = {}

        if database is not None:
            if not isinstance(database, dict):
                raise ValueError("database must be a dict")
            self.db = self._convert_format(database)
        elif self.data_path is not None:
            self.db = self._load_database()
        else:
            raise ValueError("Either data_path or database must be provided")

        self._build_indexes()

    def _resolve_path(self, path: str) -> Path:
        """
        解析資料庫路徑

        參數:
        path (str): 資料庫路徑（可以是相對或絕對路徑）

        回傳:
        Path: 解析後的絕對路徑
        """
        path_obj = Path(path)

        if not path_obj.is_absolute():
            # 相對路徑：相對於當前檔案所在目錄
            script_dir = Path(__file__).parent
            path_obj = script_dir / path_obj

        if not path_obj.exists():
            raise FileNotFoundError(f"資料庫檔案不存在：{path_obj}")

        return path_obj

    def _load_database(self) -> Dict[str, Dict[str, str]]:
        """
        載入 gzip+pickle 格式的漢字資料庫

        回傳:
        Dict[str, Dict[str, str]]: 漢字資料庫
            格式: {'字符': {'unicode': 'xxxx', 'char': '字符', 'ids_1': 'xxx', 'ids_2': 'xxx'}}
        """
        try:
            with gzip.open(str(self.data_path), "rb") as f:
                pdata = pickle.load(f)

            if not isinstance(pdata, dict):
                raise ValueError(f"資料庫格式錯誤，期望字典，取得 {type(pdata)}")

            # 轉換為內部格式
            return self._convert_format(pdata)

        except gzip.BadGzipFile:
            raise ValueError(f"無效的 gzip 檔案: {self.data_path}")
        except pickle.UnpicklingError:
            raise ValueError(f"pickle 反序列化失敗: {self.data_path}")
        except Exception as e:
            raise RuntimeError(f"資料庫載入失敗: {e}")

    def _convert_format(
        self, pdata: Dict[str, Dict[str, Optional[str]]]
    ) -> Dict[str, Dict[str, str]]:
        """
        將新格式資料庫轉換為內部使用格式

        正規化 IDS 字串中的 CJK 變體，並清除正規化後重複的 ids_2。
        保留 strokes 欄位（若存在），舊版資料庫無此欄位則為 None。

        參數:
        pdata: 新格式資料庫

        回傳:
        內部格式資料庫
            格式: {'字符': {'unicode': 'xxxx', 'char': '字符', 'ids_1': 'xxx', 'ids_2': 'xxx', 'strokes': int|None}}
        """
        converted_data = {}

        for char, data in pdata.items():
            ids_1 = self._normalize_ids_string(data.get("ids_1", ""))
            ids_2 = self._normalize_ids_string(data.get("ids_2", ""))
            if ids_2 and ids_2 == ids_1:
                ids_2 = ""
            converted_data[char] = {
                "unicode": data.get("unicode", ""),
                "char": char,
                "ids_1": ids_1,
                "ids_2": ids_2,
                "strokes": data.get("strokes"),  # 舊版資料庫無此欄位 → None
            }

        return converted_data

    @staticmethod
    def _normalize_ids_string(ids: str) -> str:
        """正規化 IDS 字串中的 CJK 變體字元"""
        if not ids:
            return ids or ""
        return "".join(_normalize_cjk_variant(ch) for ch in ids)

    def _build_indexes(self):
        """
        載入後一次遍歷建立所有反向索引

        建立：
        - _unicode_index: unicode_hex → char 的反向映射
        - _component_index: component_char → set of chars containing it
        """
        self._unicode_index: Dict[str, str] = {}
        self._component_index: Dict[str, Set[str]] = {}

        for char, data in self.db.items():
            # Unicode 反向索引
            unicode_hex = data.get("unicode")
            if unicode_hex:
                self._unicode_index[unicode_hex.upper()] = char

            # 部件反向索引（含 NFKC 正規化）
            for ids_key in ("ids_1", "ids_2"):
                ids_str = data.get(ids_key)
                if not ids_str:
                    continue
                components = self.parse_ids(ids_str)[0]
                for comp in components:
                    if comp in IDC_CHARS or comp.startswith("&"):
                        continue
                    comp = _normalize_cjk_variant(comp)
                    self._component_index.setdefault(comp, set()).add(char)

        # 全層級部件反向索引（lazy 建立，見 _ensure_recursive_index）
        self._recursive_index: Optional[Dict[str, Set[str]]] = None

    # === 字符查詢 ===

    def get_data(self, char_or_code: str) -> Dict[str, Dict[str, str]]:
        """
        獲取字符的相關資料，支援 Unicode 編碼

        參數:
        char_or_code (str): 漢字或 Unicode 編碼（支援 U+4E00, uni4E00, 4E00 等格式）
                           當輸入多個字符時，自動取第一個有效字符

        回傳:
        Dict[str, Dict[str, str]]: 包含字符資料的字典
        """
        # 處理多字符輸入：逐個嘗試，返回第一個有效字符
        # 排除 Unicode 格式（U+、uni、u 前綴）和純十六進位值
        is_unicode_format = char_or_code.startswith(("U+", "uni", "u")) or (
            len(char_or_code) in (4, 5)
            and all(c in "0123456789ABCDEFabcdef" for c in char_or_code)
        )
        if len(char_or_code) > 1 and not is_unicode_format:
            for char in char_or_code:
                if char.strip() and char in self.db:
                    return {char: self.db[char]}
            # 所有字符都無效
            return {}

        # 直接字符查詢
        if char_or_code in self.db:
            return {char_or_code: self.db[char_or_code]}

        # Unicode 格式標準化處理
        normalized_code = char_or_code.upper()
        if normalized_code.startswith(("U+", "UNI")):
            # 移除 U+ 或 UNI 前綴
            normalized_code = normalized_code.replace("U+", "").replace("UNI", "")
        elif normalized_code.startswith("U"):
            # 處理只有 u 前綴的情況
            normalized_code = normalized_code[1:]

        # 使用 Unicode 反向索引 O(1) 查表
        char = self._unicode_index.get(normalized_code)
        if char and char in self.db:
            return {char: self.db[char]}

        return {}

    # === 筆畫數查詢與篩選 ===

    def get_stroke_count(self, char: str) -> Optional[int]:
        """
        取得字符的筆畫數

        參數:
        char (str): 字符

        回傳:
        Optional[int]: 筆畫數；字不在資料庫或無筆畫資料時為 None
        """
        data = self.db.get(char)
        if not data:
            return None
        strokes = data.get("strokes")
        # 防禦性轉型：舊資料或損壞資料可能不是 int
        if isinstance(strokes, int):
            return strokes
        return None

    def filter_by_strokes(
        self,
        chars,
        base_char: str,
        max_diff: Optional[int],
    ) -> List[str]:
        """
        依筆畫差距篩選字符列表

        參數:
        chars: 待篩選的字符 iterable
        base_char (str): 比較基準字（通常是搜尋主字）
        max_diff (Optional[int]):
            None → 不篩選，全部回傳
            int  → 只保留筆畫差 ≤ max_diff 的字

        回傳:
        List[str]: 篩選後的字符列表，順序與輸入一致

        備註：
        - 主字無筆畫資料時，回退為全顯示（避免空白面板）
        - max_diff 不為 None 時，無筆畫資料的字一律排除
        """
        base_strokes = self.get_stroke_count(base_char)
        # 主字無資料且要篩選 → 回退全顯示（避免空白面板）
        if max_diff is not None and base_strokes is None:
            return list(chars)
        return self.filter_by_stroke_value(chars, base_strokes, max_diff)

    def filter_by_stroke_value(
        self,
        chars,
        base_strokes: Optional[int],
        max_diff: Optional[int],
    ) -> List[str]:
        """
        依筆畫差距篩選字符列表（數值基準版）

        多部件搜尋以「各部件筆畫加總」為基準時使用此版本。

        參數:
        chars: 待篩選的字符 iterable
        base_strokes (Optional[int]): 比較基準筆畫數
        max_diff (Optional[int]):
            None 或 base_strokes 為 None → 不篩選，全部回傳
            int → 只保留筆畫差 ≤ max_diff 的字（無筆畫資料的字一律排除）

        回傳:
        List[str]: 篩選後的字符列表，順序與輸入一致
        """
        chars_list = list(chars)
        if max_diff is None or base_strokes is None:
            return chars_list

        result = []
        for char in chars_list:
            char_strokes = self.get_stroke_count(char)
            if char_strokes is None:
                continue
            if abs(char_strokes - base_strokes) <= max_diff:
                result.append(char)
        return result

    def parse_ids(self, ids: Union[str, List[str]]) -> List[List[str]]:
        """
        解析 IDS（Ideographic Description Sequence）字符串

        參數:
        ids (str 或 List[str]): IDS 字符串或 IDS 字符串列表

        回傳:
        List[List[str]]: 解析後的 IDS 列表
        """

        def split_special_chars(s):
            return re.findall(r"&[^;]+;|[⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻〾]|\S", s)

        if isinstance(ids, str):
            if ids in self._parsed_ids_cache:
                return self._parsed_ids_cache[ids]
            result = [split_special_chars(ids)]
            self._parsed_ids_cache[ids] = result
            return result
        return [split_special_chars(id_str) for id_str in ids]

    # === 搜尋功能 ===

    def search(self, query: str, charset: Optional[Set[str]] = None) -> List[str]:
        """
        根據部件搜尋相關字符，支援模糊搜尋

        參數:
        query (str): 要搜尋的部件或字符
        charset (Optional[Set[str]]): 可選的字符集篩選（None = 搜尋全部）

        回傳:
        List[str]: 包含該部件的字符列表
        """
        # 快速路徑：單一字元且在部件反向索引中
        normalized_query = _normalize_cjk_variant(query) if len(query) == 1 else query
        if len(normalized_query) == 1 and normalized_query in self._component_index:
            results = list(self._component_index[normalized_query])
            # 確保查詢字元本身也在結果中（如果存在於資料庫）
            if normalized_query in self.db and normalized_query not in results:
                results.insert(0, normalized_query)
            if charset is not None:
                results = [c for c in results if c in charset]
            return results

        # 慢速路徑：Unicode 查詢等非標準情況
        results = []
        query_lower = query.lower()

        for char, data in self.db.items():
            found = False

            # 1. 檢查字符本身
            if query_lower in char.lower():
                found = True

            # 2. 檢查 Unicode（轉為字符比對）
            elif query_lower in data.get("unicode", "").lower():
                found = True

            # 3. 檢查 IDS 結構中的部件（檢查所有變體）
            elif data.get("ids_1") or data.get("ids_2"):
                try:
                    ids_variants = []
                    if data.get("ids_1"):
                        ids_variants.append(data["ids_1"])
                    if data.get("ids_2"):
                        ids_variants.append(data["ids_2"])

                    for ids in ids_variants:
                        parsed_ids_list = self.parse_ids(ids)
                        for ids_sequence in parsed_ids_list:
                            for ids_part in ids_sequence:
                                if query_lower == ids_part.lower():
                                    found = True
                                    break
                            if found:
                                break
                        if found:
                            break
                except Exception:
                    for ids in ids_variants:
                        if query_lower in ids.lower():
                            found = True
                            break

            if found:
                results.append(char)

        if charset is not None:
            results = [c for c in results if c in charset]

        return results

    def search_all(
        self, queries: List[str], charset: Optional[Set[str]] = None
    ) -> List[str]:
        """
        多部件 AND 搜尋：回傳「遞迴展開到所有層級部件後，計數涵蓋查詢多重集」的字

        語意：
        - 遞迴：部件藏在更深層也算（如 淋=⿰氵林，木在林裡 → 視為含木）
        - 全層級：中間部件本身也可當查詢詞（如 童=⿱立里 → 視為含里；焚=⿱林火 → 視為含林）
        - 計數：重複部件代表「至少 N 個」（如 木木 = 至少兩個木，林/森入選）

        參數:
        queries (List[str]): 部件清單，保留重複（重複代表次數要求）
        charset (Optional[Set[str]]): 可選的字符集篩選（None = 搜尋全部）

        回傳:
        List[str]: 命中字，按 Unicode 碼位升序（確定性，使「前 N 個」可預期）
        """
        if not queries:
            return []

        # 查詢部件正規化後建多重集（與全層級索引正規化一致）
        query_counter = Counter(_normalize_cjk_variant(q) for q in queries)

        recursive_index = self._ensure_recursive_index()

        # 候選 = 同時（遞迴）含所有查詢部件的字，用全層級反向索引快速縮小交集
        unique_parts = list(query_counter)
        candidates = set(recursive_index.get(unique_parts[0], set()))
        for part in unique_parts[1:]:
            candidates &= recursive_index.get(part, set())
            if not candidates:
                return []

        # 計數驗證：每個查詢部件的全層級計數需 >= 要求次數
        results = []
        for char in candidates:
            components = self._recursive_components(char)
            if all(components.get(part, 0) >= n for part, n in query_counter.items()):
                results.append(char)

        if charset is not None:
            results = [c for c in results if c in charset]

        return sorted(results, key=ord)

    def _ensure_recursive_index(self) -> Dict[str, Set[str]]:
        """首次需要時建立全層級部件反向索引（部件 → 含該部件的字集合），建立後快取。

        收錄拆解樹中「所有層級的節點」（中間部件與葉部件皆是 key），
        故可比對如「里」「童」「林」這類本身可再拆的中間部件。
        """
        if self._recursive_index is None:
            index: Dict[str, Set[str]] = {}
            for char in self.db:
                for comp in self._recursive_components(char):
                    index.setdefault(comp, set()).add(char)
            self._recursive_index = index
        return self._recursive_index

    def _recursive_components(self, char: str, max_depth: int = 20) -> Counter:
        """遞迴展開字到所有層級部件，回傳多重集計數（Counter）。

        拆解樹中每個節點（含中間部件與葉部件、含根字自身）各計數一次；
        含循環防護與深度上限，部件做 CJK 變體正規化（與反向索引一致）。
        """
        counter: Counter = Counter()
        self._collect_recursive(char, 0, max_depth, frozenset(), counter)
        return counter

    def _collect_recursive(self, char, depth, max_depth, visiting, counter):
        """_recursive_components 的遞迴內部實作：對每個節點計數，再展開其子部件。"""
        counter[_normalize_cjk_variant(char)] += 1

        data = self.db.get(char)
        ids = data.get("ids_1") if data else None

        # 葉節點：超過深度 / 無資料 / 無 IDS / IDS 即自身 / 獨體字（無 IDC）
        if (
            depth >= max_depth
            or not ids
            or ids == char
            or all(idc not in ids for idc in IDC_CHARS)
        ):
            return

        components = [
            c
            for c in self.parse_ids(ids)[0]
            if c not in IDC_CHARS and not c.startswith("&")
        ]

        for comp in components:
            if comp == char or comp in visiting:
                counter[_normalize_cjk_variant(comp)] += 1
            else:
                self._collect_recursive(
                    comp, depth + 1, max_depth, visiting | {char}, counter
                )

    def format_position_label(
        self,
        idc: Optional[str],
        positions,
        nested: bool = False,
    ) -> str:
        """Format a position group label such as ⿰1, ⿱≡, ⿲3·, or ∅."""
        if not idc or idc not in IDC_ARITY:
            return UNCLASSIFIED_LABEL
        if positions is None:
            return UNCLASSIFIED_LABEL
        if isinstance(positions, int):
            marker = str(positions)
        else:
            unique_positions = []
            for pos in positions:
                if pos not in unique_positions:
                    unique_positions.append(pos)
            if not unique_positions:
                return UNCLASSIFIED_LABEL
            marker = (
                str(unique_positions[0])
                if len(unique_positions) == 1
                else MULTI_POSITION_MARKER
            )
        return f"{idc}{marker}{NESTED_POSITION_MARKER if nested else ''}"

    def _operand_directly_is(self, operand_tokens: List[str], query: str) -> bool:
        """True if a top-level operand itself is exactly the query component."""
        return (
            len(operand_tokens) == 1
            and _normalize_cjk_variant(operand_tokens[0]) == query
        )

    def _operand_contains(self, operand_tokens: List[str], query: str) -> bool:
        """True if query occurs anywhere in this operand subtree."""
        for token in operand_tokens:
            if token in IDC_CHARS or token.startswith("&"):
                continue
            if _normalize_cjk_variant(token) == query:
                return True
            if self._component_contains_query(token, query):
                return True
        return False

    def _top_position_contains(
        self, tokens: List[str], query: str
    ) -> Tuple[Optional[str], List[int], bool]:
        """Return top IDC, matching 1-based positions, and whether matches are nested."""
        if not tokens:
            return None, [], False
        idc = tokens[0]
        if idc not in IDC_ARITY:
            return None, [], False
        direct_positions: List[int] = []
        nested_positions: List[int] = []
        for index, operand in enumerate(_split_top_operands(tokens), start=1):
            if self._operand_directly_is(operand, query):
                direct_positions.append(index)
            elif self._operand_contains(operand, query):
                nested_positions.append(index)
        if direct_positions:
            return idc, direct_positions, False
        if nested_positions:
            return idc, nested_positions, True
        return idc, [], False

    def _component_contains_query(
        self, char: str, query: str, max_depth: int = 20
    ) -> bool:
        """Recursive containment check used for nested top-position classification."""
        if _normalize_cjk_variant(char) == query:
            return True
        return self._component_contains_query_inner(
            char, query, max_depth, frozenset()
        )

    def _component_contains_query_inner(self, char, query, depth, visiting) -> bool:
        if depth <= 0 or not char or char in visiting:
            return False
        data = self.db.get(char)
        if not data:
            return False
        for ids in self._selected_ids_list_for_tree(char, 0):
            if not ids or not self._ids_is_expandable(ids, char):
                continue
            for token in self.parse_ids(ids)[0]:
                if token in IDC_CHARS or token.startswith("&"):
                    continue
                norm = _normalize_cjk_variant(token)
                if norm == query:
                    return True
                if self._component_contains_query_inner(
                    norm, query, depth - 1, visiting | {char}
                ):
                    return True
        return False

    def _ids_variants_for_position_classification(
        self, char: str, variant_index: int = 0
    ) -> List[str]:
        data = self.db.get(char)
        if not data:
            return []
        ids_1 = data.get("ids_1") or ""
        ids_2 = data.get("ids_2") or ""
        if ids_2 == ids_1:
            ids_2 = ""
        if variant_index == -1:
            return [ids for ids in (ids_1, ids_2) if ids]
        if variant_index == 1:
            return [ids_2 or ids_1] if (ids_2 or ids_1) else []
        return [ids_1 or ids_2] if (ids_1 or ids_2) else []

    def classify_by_position(
        self, query: str, target_char: str, variant_index: int = 0
    ) -> str:
        """Classify where query appears in target_char's top-level IDS structure."""
        if not query or not target_char:
            return UNCLASSIFIED_LABEL
        normalized_query = _normalize_cjk_variant(query)
        for ids in self._ids_variants_for_position_classification(
            target_char, variant_index
        ):
            tokens = self.parse_ids(ids)[0]
            idc, positions, nested = self._top_position_contains(
                tokens, normalized_query
            )
            if positions:
                return self.format_position_label(idc, positions, nested)
            if (
                len(tokens) == 1
                and _normalize_cjk_variant(tokens[0]) == normalized_query
            ):
                return UNCLASSIFIED_LABEL
        return UNCLASSIFIED_LABEL

    def _position_label_sort_key(self, label: str):
        if label == UNCLASSIFIED_LABEL:
            return (len(IDC_ORDER), 99, 1, label)
        idc = label[0]
        order = IDC_ORDER.find(idc)
        if order < 0:
            order = len(IDC_ORDER)
        nested = label.endswith(NESTED_POSITION_MARKER)
        marker = label[1:-1] if nested else label[1:]
        if marker == MULTI_POSITION_MARKER:
            position = 98
        else:
            try:
                position = int(marker)
            except Exception:
                position = 99
        return (order, 1 if nested else 0, position, label)

    def group_by_position(
        self,
        query: str,
        chars: List[str],
        variant_index: int = 0,
        coarse_by_idc: bool = False,
    ) -> Dict[str, List[str]]:
        """Group chars by query position labels, preserving direct-before-nested ordering."""
        groups: Dict[str, List[str]] = {}
        for char in chars:
            label = self.classify_by_position(query, char, variant_index)
            if coarse_by_idc and label != UNCLASSIFIED_LABEL:
                label = label[0]
            groups.setdefault(label, []).append(char)
        return {
            label: groups[label]
            for label in sorted(groups.keys(), key=self._position_label_sort_key)
        }

    def compose_immediate_component_lines(
        self,
        query: str,
        chars: List[str],
        variant_index: int = 0,
        coarse_by_idc: bool = False,
    ) -> List[str]:
        """Return compact display lines: '<position-label> <chars>' for right pane."""
        return [
            f"{label} {''.join(group_chars)}"
            for label, group_chars in self.group_by_position(
                query, chars, variant_index, coarse_by_idc=coarse_by_idc
            ).items()
            if group_chars
        ]

    def find_sister_characters(
        self, char: str, charset: Optional[Set[str]] = None, variant_index: int = 0
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        搜尋同字根，根據結構和部件相似度分級，排除獨體字

        參數:
        char (str): 要搜尋同字根的字符
        charset (Optional[Set[str]]): 可選的字符集篩選
        variant_index (int): 使用第幾種拆法（0=ids_1, 1=ids_2, -1=合併所有）

        回傳:
        Dict[str, Dict[str, List[str]]]: 同字根資料
            格式: {'結構相同部件同位': {'木': ['林', '森']}, ...}
        """
        target_data = self.db.get(char)
        if not target_data:
            return {}

        # 如果是 variant_index == -1，合併所有拆法的結果
        if variant_index == -1:
            result_1 = self._find_sister_by_ids(
                char, target_data.get("ids_1", ""), charset
            )
            result_2 = self._find_sister_by_ids(
                char, target_data.get("ids_2", ""), charset
            )
            return self._merge_sister_results(result_1, result_2)

        # 根據 variant_index 選擇 IDS
        if variant_index == 0:
            target_ids = target_data.get("ids_1") or target_data.get("ids_2", "")
        elif variant_index == 1:
            target_ids = target_data.get("ids_2") or target_data.get("ids_1", "")
        else:
            target_ids = target_data.get("ids_1") or target_data.get("ids_2", "")

        if not target_ids:
            return {}

        return self._find_sister_by_ids(char, target_ids, charset)

    def _find_sister_by_ids(
        self, char: str, target_ids: str, charset: Optional[Set[str]] = None
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        根據指定的 IDS 搜尋同字根（內部方法）
        """
        if not target_ids:
            return {}

        target_structure = "".join([c for c in target_ids if c in IDC_CHARS])
        target_components = [
            c for c in self.parse_ids(target_ids)[0] if c not in IDC_CHARS
        ]

        # 檢查是否為獨體字
        if len(target_components) <= 1:
            return {"獨體字": {char: [char]}}

        sisters = {"結構相同部件同位": {}, "結構部件相同": {}, "部件相同": {}}

        for c, data in self.db.items():
            if c == char:
                continue

            # 套用字符集篩選（提前過濾）
            if charset is not None and c not in charset:
                continue

            # 收集所有 IDS 變體
            ids_variants = []
            if data.get("ids_1"):
                ids_variants.append(data["ids_1"])
            if data.get("ids_2"):
                ids_variants.append(data["ids_2"])

            if not ids_variants:
                continue

            # 遍歷所有拆法,找到匹配後停止(避免同一字符重複加入)
            found_sister = False
            for ids in ids_variants:
                if found_sister:
                    break

                structure = "".join([c for c in ids if c in IDC_CHARS])
                components = [c for c in self.parse_ids(ids)[0] if c not in IDC_CHARS]

                # 排除獨體字
                if len(components) == 1:
                    continue

                if structure == target_structure:
                    # 檢查每個位置的部件是否相同
                    same_position_components = []
                    for i, (target_comp, comp) in enumerate(
                        zip(target_components, components)
                    ):
                        if target_comp == comp:
                            same_position_components.append(i + 1)

                    if same_position_components:
                        key = ",".join(map(str, same_position_components))
                        key_hanzi = "".join(
                            [target_components[int(pos) - 1] for pos in key.split(",")]
                        )
                        sisters["結構相同部件同位"].setdefault(key_hanzi, []).append(c)
                        found_sister = True
                    elif set(target_components) & set(components):
                        common_components = "".join(
                            sorted(set(target_components) & set(components))
                        )
                        sisters["結構部件相同"].setdefault(
                            common_components, []
                        ).append(c)
                        found_sister = True
                elif set(target_components) & set(components):
                    common_components = "".join(
                        sorted(set(target_components) & set(components))
                    )
                    sisters["部件相同"].setdefault(common_components, []).append(c)
                    found_sister = True

        return sisters

    def _merge_sister_results(
        self,
        result_1: Dict[str, Dict[str, List[str]]],
        result_2: Dict[str, Dict[str, List[str]]],
    ) -> Dict[str, Dict[str, List[str]]]:
        """
        合併兩個 find_sister_characters 的結果
        """
        # 如果其中一個是獨體字,返回另一個
        if "獨體字" in result_1:
            return result_2 if result_2 and "獨體字" not in result_2 else result_1
        if "獨體字" in result_2:
            return result_1

        merged = {"拆法1結果": result_1, "拆法2結果": result_2}

        return merged

    def find_derived_characters(
        self, char: str, charset: Optional[Set[str]] = None
    ) -> Dict[str, List[str]]:
        """
        搜尋包含指定字符作為部件的所有字符，將結果按部件分組

        參數:
        char (str): 要搜尋衍生字的字符
        charset (Optional[Set[str]]): 可選的字符集篩選

        回傳:
        Dict[str, List[str]]: 以部件為 key、衍生字列表為 value 的字典
        """
        MAX_DEPTH = 4
        derived_groups: Dict[str, List[str]] = {}
        decomposed_parts = set()
        structure_patterns = set()
        component_groups = set()
        visited_components = set()
        special_chars = set(IDC_CHARS)

        def extract_structure(components):
            if len(components) < 2:
                return

            full_structure = "".join(comp for _, comp in components)
            structure_patterns.add(full_structure)

            for i in range(len(components)):
                for j in range(i + 2, len(components) + 1):
                    sub_structure = "".join(comp for _, comp in components[i:j])
                    if any(c not in special_chars for c in sub_structure):
                        component_groups.add(sub_structure)

        def process_component(component, depth=0):
            if depth >= MAX_DEPTH or component in visited_components:
                return
            visited_components.add(component)

            if component and component not in special_chars:
                decomposed_parts.add(component)

            sub_components = self.decompose(component, max_depth=1)
            if sub_components:
                extract_structure(sub_components)

                for op, comp in sub_components:
                    if comp not in special_chars:
                        decomposed_parts.add(comp)
                        if depth < MAX_DEPTH and comp not in visited_components:
                            process_component(comp, depth + 1)

        # 初始處理目標字符
        initial_components = self.decompose(char, max_depth=1)
        process_component(char)

        # 從反向索引收集候選字元（2 層查詢）
        # Level 1: 直接包含 part 的字元
        # Level 2: 包含「包含 part 的字元」作為部件的字元
        candidates = set()
        for part in decomposed_parts:
            # 正規化 key 以匹配索引（索引建立時已對 CJK 變體做正規化）
            lookup_key = _normalize_cjk_variant(part)
            direct = self._component_index.get(lookup_key, set())
            candidates.update(direct)
            for intermediate in direct:
                norm_inter = _normalize_cjk_variant(intermediate)
                candidates.update(self._component_index.get(norm_inter, set()))
        candidates.discard(char)

        if charset is not None:
            candidates &= charset

        # 只對候選字元做詳細比對
        for c in candidates:
            try:
                target_components = self.decompose(c, max_depth=1)

                matching_components = set()

                for _, comp in target_components:
                    if comp in decomposed_parts and comp not in special_chars:
                        matching_components.add(comp)
                        continue

                    sub_comps = self.decompose(comp, max_depth=1)
                    for _, sub_comp in sub_comps:
                        if (
                            sub_comp in decomposed_parts
                            and sub_comp not in special_chars
                        ):
                            matching_components.add(sub_comp)

                for matched_comp in matching_components:
                    if matched_comp not in derived_groups:
                        derived_groups[matched_comp] = []
                    derived_groups[matched_comp].append(c)

            except Exception:
                continue

        return derived_groups

    # === 字符拆解 ===

    def decompose(
        self, char: str, max_depth: int = 10, variant_index: int = 0
    ) -> List[Tuple[str, str]]:
        """
        遞迴分解字符，回傳適合 UI 顯示的緊湊樹狀列表。

        v1.6.2 起，樹線由「固定層級直線」改為依兄弟節點位置計算的
        現代 box-drawing connector，避免深層拆解時分支線斷裂或多餘延伸。

        參數:
        char (str): 要分解的字符
        max_depth (int): 最大遞迴深度
        variant_index (int): 使用第幾種拆法（0=ids_1, 1=ids_2, -1=全部顯示）

        回傳:
        List[Tuple[str, str]]: 分解後的結構列表，每個元素是一個元組 (tree_symbol, content)
        """
        return self._decompose_modern_tree(char, max_depth=max_depth, variant_index=variant_index)

    def _tree_prefix(self, ancestor_last_flags, is_last: bool) -> str:
        """Return compact, connected tree prefix for one visible row."""
        prefix = "".join("   " if last else "│  " for last in ancestor_last_flags)
        return prefix + ("└─ " if is_last else "├─ ")

    def _selected_ids_list_for_tree(self, char: str, variant_index: int) -> List[str]:
        """Return IDS variants selected by UI variant_index with fallback rules."""
        data = self.db.get(char)
        if not data:
            return []
        ids_1 = data.get("ids_1") or ""
        ids_2 = data.get("ids_2") or ""
        if ids_2 == ids_1:
            ids_2 = ""
        if variant_index == -1:
            return [ids for ids in (ids_1, ids_2) if ids]
        if variant_index == 1:
            return [ids_2 or ids_1] if (ids_2 or ids_1) else []
        return [ids_1 or ids_2] if (ids_1 or ids_2) else []

    def _ids_is_expandable(self, ids: str, char: str = "") -> bool:
        """True when IDS actually describes a structure rather than a standalone char."""
        if not ids or ids == char:
            return False
        return any(idc in ids for idc in IDC_CHARS)

    def _decompose_modern_tree(
        self, char: str, max_depth: int = 10, variant_index: int = 0
    ) -> List[Tuple[str, str]]:
        """Modern compact tree renderer used by decompose()."""
        if not char:
            return []

        data = self.db.get(char)
        if not data:
            return [("", char)]

        ids_list = [ids for ids in self._selected_ids_list_for_tree(char, variant_index) if ids]
        ids_list = [ids for ids in ids_list if self._ids_is_expandable(ids, char)]
        if not ids_list:
            return [("", char)]

        result: List[Tuple[str, str]] = [("", char)]
        for idx, ids in enumerate(ids_list):
            self._append_ids_tree_lines(
                result=result,
                owner_char=char,
                ids=ids,
                ancestor_last_flags=[],
                is_last=(idx == len(ids_list) - 1),
                depth=0,
                max_depth=max_depth,
                variant_index=variant_index,
            )
        return result

    def _append_ids_tree_lines(
        self,
        result: List[Tuple[str, str]],
        owner_char: str,
        ids: str,
        ancestor_last_flags,
        is_last: bool,
        depth: int,
        max_depth: int,
        variant_index: int,
    ) -> None:
        """Append one IDS operator node and all child components with connected branches."""
        if not ids:
            return

        parsed = self.parse_ids(ids)[0]
        if not parsed:
            return

        operator = parsed[0]
        components = parsed[1:]
        if operator not in IDC_CHARS:
            # Defensive fallback for unusual records; keep the UI compact.
            result.append((self._tree_prefix(ancestor_last_flags, is_last), ids))
            return

        result.append((self._tree_prefix(ancestor_last_flags, is_last), operator))

        child_ancestors = list(ancestor_last_flags) + [is_last]
        for comp_index, comp in enumerate(components):
            comp_is_last = comp_index == len(components) - 1
            comp_prefix = self._tree_prefix(child_ancestors, comp_is_last)
            result.append((comp_prefix, comp))

            if (
                depth + 1 >= max_depth
                or not comp
                or comp.startswith("&")
                or comp in IDC_CHARS
            ):
                # At max depth we stop cleanly at the component row rather than
                # adding a duplicate "reached max depth" child, keeping the list compact.
                continue

            sub_ids_list = [
                sub_ids
                for sub_ids in self._selected_ids_list_for_tree(comp, variant_index)
                if self._ids_is_expandable(sub_ids, comp)
            ]
            if not sub_ids_list:
                continue

            sub_ancestors = child_ancestors + [comp_is_last]
            for sub_index, sub_ids in enumerate(sub_ids_list):
                self._append_ids_tree_lines(
                    result=result,
                    owner_char=comp,
                    ids=sub_ids,
                    ancestor_last_flags=sub_ancestors,
                    is_last=(sub_index == len(sub_ids_list) - 1),
                    depth=depth + 1,
                    max_depth=max_depth,
                    variant_index=variant_index,
                )

    # === IDS 變體管理 ===

    def get_ids_variants(self, char: str) -> List[str]:
        """
        取得字符的所有 IDS 拆法變體

        參數:
        char (str): 要查詢的字符

        回傳:
        List[str]: IDS 拆法列表，例如 ['⿰木木', '⿱某某']
                   如果字符不存在或沒有拆法，返回空列表
        """
        data = self.db.get(char)
        if not data:
            return []

        variants = []
        if data.get("ids_1"):
            variants.append(data["ids_1"])
        if data.get("ids_2"):
            variants.append(data["ids_2"])

        return variants

    # === 工具函數 ===

    @staticmethod
    def clean_display_text(text: str) -> str:
        """
        直接返回原始文本，不進行任何過濾

        依賴字型的 fallback 機制來正確顯示所有字符，
        包括 CJK 擴展區罕用字（U+20000-U+3134F）

        參數:
        text (str): 原始文本

        回傳:
        str: 原始文本（不做任何修改）
        """
        return text

    @staticmethod
    def is_error_message(text: str) -> bool:
        """
        檢查文字是否為錯誤訊息

        參數:
        text (str): 要檢查的文字

        回傳:
        bool: 是否為錯誤訊息
        """
        if not text or not text.strip():
            return True

        error_indicators = [
            ERROR_NO_MATCH_FOUND,
            ERROR_UNKNOWN_CHAR,
            ERROR_SEARCH_FAILED,
            "未找到",
            "無法",
            "錯誤",
            "(達到最大深度)",
            "達到最大深度",
        ]
        return any(indicator in text for indicator in error_indicators)

    @staticmethod
    def is_valid_character(char: str) -> bool:
        """
        檢查字符是否適合進行分析

        參數:
        char (str): 要檢查的字符

        回傳:
        bool: 是否為有效字符
        """
        if not char or not char.strip():
            return False

        # 檢查是否為錯誤訊息
        if HanziCore.is_error_message(char):
            return False

        # 檢查是否為單個字符（排除多字符錯誤訊息）
        stripped_char = char.strip()
        if len(stripped_char) > 1:
            # 允許某些特殊情況，如 Unicode 格式
            if not stripped_char.startswith(("U+", "uni", "u")):
                return False

        return True

    @staticmethod
    def extract_character(text: str) -> Optional[str]:
        """
        從顯示文本中智能提取實際字符

        參數:
        text (str): 顯示的文本字符串

        回傳:
        Optional[str]: 提取的字符，如果無法提取則返回 None
        """
        if not text or not text.strip():
            return None

        # 處理特殊標記（如 "王 (達到最大深度)"）
        if " (達到最大深度)" in text:
            char = text.replace(" (達到最大深度)", "").strip()
            if char and not HanziCore.is_error_message(char):
                return char

        # 檢查是否為錯誤訊息（在特殊標記處理之後）
        if HanziCore.is_error_message(text):
            return None

        # 處理樹狀結構格式（如 "｜   └─ 王"）
        # 移除樹狀結構符號
        tree_symbols = ["｜", "│", "├─", "└─", "├", "└", "─", " ", "●", "○", "–", "★"]
        cleaned = text
        for symbol in tree_symbols:
            cleaned = cleaned.replace(symbol, " ")

        # 提取最後一個非空部分
        parts = [p.strip() for p in cleaned.split() if p.strip()]
        if parts:
            candidate = parts[-1]
            if not HanziCore.is_error_message(candidate):
                return candidate

        # 如果以上都失敗，嘗試直接返回清理後的字符串
        stripped = text.strip()
        if stripped and not HanziCore.is_error_message(stripped):
            return stripped

        return None


# === 搜尋輸入驗證 ===


def is_complete_search_input(text: str) -> bool:
    """
    檢查輸入是否為完整有效的搜尋格式

    只有完整有效的輸入才應觸發搜尋，避免輸入過程中的錯誤搜尋。

    有效格式：
    - 單個漢字（非 ASCII，Unicode > 127）
    - uni 前綴：uniXXXX（7 字符，如 uni6F22）
    - U+ 前綴：U+XXXX 或 U+XXXXX（6-7 字符，如 U+6F22）
    - u 前綴：uXXXXX（6 字符，如 u2F804）
    - 純十六進位碼：XXXX 或 XXXXX（4-5 位，如 6F22）

    參數:
    text (str): 搜尋輸入文字

    回傳:
    bool: 是否為完整有效的搜尋格式
    """
    if not text:
        return False

    # 漢字輸入（非 ASCII）- 接受單個或多個漢字（多字觸發 AND 組合搜尋）
    if ord(text[0]) > 127:
        return True

    HEX_CHARS = "0123456789ABCDEFabcdef"

    # uni 前綴：正好 uniXXXX 格式（7 字符）
    if text.lower().startswith("uni"):
        return len(text) == 7 and all(c in HEX_CHARS for c in text[3:])

    # U+ 前綴：U+XXXX 或 U+XXXXX（6-7 字符）
    if text.upper().startswith("U+"):
        hex_part = text[2:]
        return len(hex_part) in (4, 5) and all(c in HEX_CHARS for c in hex_part)

    # u 前綴（非 uni）：uXXXXX 或 uXXXXXX（6-7 字符，對應 SIP/TIP）
    if text.lower().startswith("u") and not text.lower().startswith("uni"):
        hex_part = text[1:]
        return len(hex_part) in (5, 6) and all(c in HEX_CHARS for c in hex_part)

    # 純十六進位碼：正好 4-5 位
    if len(text) in (4, 5) and all(c in HEX_CHARS for c in text):
        return True

    return False


# === 獨立執行測試 ===

if __name__ == "__main__":
    """測試核心引擎功能"""

    print("=== Hanzi Component Explorer RS+ - 核心引擎測試 ===\n")

    # 初始化核心引擎
    try:
        core = HanziCore("data/ids.pdata")
        print(f"✅ 資料庫載入成功：{len(core.db)} 個字符\n")
    except Exception as e:
        print(f"❌ 資料庫載入失敗：{e}")
        exit(1)

    # 測試 1：字符查詢
    print("【測試 1：字符查詢】")
    test_char = "木"
    data = core.get_data(test_char)
    if data:
        char_data = data[test_char]
        print(f"字符：{char_data['char']}")
        print(f"Unicode：{char_data['unicode']}")
        print(f"IDS 1：{char_data.get('ids_1', '')}")
        if char_data.get("ids_2"):
            print(f"IDS 2：{char_data['ids_2']}")
        print()

    # 測試 2：Unicode 查詢
    print("【測試 2：Unicode 查詢】")
    unicode_query = "U+6728"
    data = core.get_data(unicode_query)
    if data:
        char = list(data.keys())[0]
        print(f"查詢：{unicode_query} → 字符：{char}\n")

    # 測試 3：部件搜尋
    print("【測試 3：部件搜尋】")
    results = core.search("木")
    print(f"包含「木」的字符（前 10 個）：{' '.join(results[:10])}\n")

    # 測試 4：字符拆解
    print("【測試 4：字符拆解】")
    test_char = "森"
    decomposed = core.decompose(test_char, max_depth=3)
    print(f"字符「{test_char}」的拆解結構：")
    for tree, content in decomposed:
        print(f"{tree}{content}")
    print()

    # 測試 5：同字根搜尋
    print("【測試 5：同字根搜尋】")
    test_char = "林"
    sisters = core.find_sister_characters(test_char)
    for category, groups in sisters.items():
        if groups:
            print(f"{category}：")
            for key, chars in groups.items():
                print(f"  {key}：{' '.join(chars[:5])}")
    print()

    # 測試 6：衍生字搜尋
    print("【測試 6：衍生字搜尋】")
    test_char = "木"
    derived = core.find_derived_characters(test_char)
    if derived:
        print(f"包含「{test_char}」的衍生字（前 3 組）：")
        for i, (component, chars) in enumerate(list(derived.items())[:3]):
            print(f"  部件 {component}：{' '.join(chars[:8])}")
    print()

    print("✅ 所有測試完成！")
