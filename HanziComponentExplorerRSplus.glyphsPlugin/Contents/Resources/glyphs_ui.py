# MenuTitle: 漢字部品検索 RS+
# -*- coding: utf-8 -*-
"""
Hanzi Component Explorer RS+ - Glyphs UI 層
使用 vanilla 框架的 Glyphs 外掛介面

Original copyright © 2025 TzuYuan Yin
Fork modifications copyright © 2026 Ooma Kobayashi
Modified from the original upstream project.
"""

from __future__ import division, print_function, unicode_literals

import os
import re
import time
from bisect import bisect_right
from typing import Optional, Set, List

import vanilla
from AppKit import (
    NSFont,
    NSAttributedString,
    NSMutableAttributedString,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSBackgroundColorAttributeName,
    NSKernAttributeName,
    NSParagraphStyleAttributeName,
    NSBaselineOffsetAttributeName,
    NSMutableParagraphStyle,
    NSColor,
    NSOpenPanel,
    NSObject,
    NSImage,
    NSNotificationCenter,
    NSPasteboard,
    NSTableViewNoColumnAutoresizing,
    NSLineBreakByClipping,
    NSBoxCustom,
    NSClickGestureRecognizer,
    NSView,
    NSScrollView,
    NSMakeRect,
    NSMakeSize,
    NSBezierPath,
    NSCompositeSourceOver,
    NSViewWidthSizable,
    NSViewHeightSizable,
)
import CoreText

from hanzi_core import HanziCore, is_complete_search_input, resolve_display_char
from glyphs_adapter import GlyphsAdapter, GlyphsSettings
from localization import L
from glyph_status import (
    STATUS_DESIGNED,
    STATUS_EXISTS,
    STATUS_MISSING,
    STATUS_FAVORITE,
    STATUS_MARKERS,
    status_payload,
    count_statuses,
    designed_percent,
    unique_related_chars,
)


# 字體大小設定
RELATED_CHARS_FONT_SIZE = 20  # 右側相關字區域
CONTENT_FONT_SIZE = 14  # 左側詳細資訊區
RESULT_LIST_FONT_SIZE = 13  # 中間結果列表

# 筆畫篩選滑桿設定
# tick 0..4 對應筆畫差 ±0/±1/±2/±3/±5；tick 5 為「關閉篩選」
STROKE_FILTER_VALUES = [0, 1, 2, 3, 5]
STROKE_FILTER_OFF_TICK = 5
STROKE_FILTER_TICK_COUNT = STROKE_FILTER_OFF_TICK + 1  # 6 個 tick 位置

# IDS 資料源。フォント制作向けに最も字形差を保持する Yi Bai lv0 を既定値とする。
IDS_SOURCE_OPTIONS = ("yibai_lv0", "yibai_lv1", "yibai_lv2", "chise")
DEFAULT_IDS_SOURCE = "yibai_lv0"

# Bai IDS uses trailing indicators to identify source-specific glyph forms.
# Codes outside this table remain visible as raw glyph-form annotations.
VARIANT_REGION_LABEL_KEYS = {
    ".": "ids_variant_source_default",
    "G": "ids_variant_source_g",
    "H": "ids_variant_source_h",
    "J": "ids_variant_source_j",
    "K": "ids_variant_source_k",
    "KP": "ids_variant_source_kp",
    "M": "ids_variant_source_m",
    "T": "ids_variant_source_t",
    "U": "ids_variant_source_u",
    "V": "ids_variant_source_v",
}

# 右側相關字區域排版設定
RELATED_CHARS_KERN = 0.0  # 字距（字符間距，單位：點）- 預設值
RELATED_CHARS_LINE_HEIGHT = 1.2  # 行高倍數（相對於字體大小）

# Glyphs 顏色 ID 到 RGB 值的映射（12 種顏色）
GLYPH_COLOR_MAP = {
    0: (0.85, 0.26, 0.26, 1.0),  # 紅
    1: (0.97, 0.56, 0.26, 1.0),  # 橘
    2: (0.65, 0.48, 0.32, 1.0),  # 棕
    3: (0.97, 0.90, 0.26, 1.0),  # 黃
    4: (0.67, 0.90, 0.26, 1.0),  # 淺綠
    5: (0.26, 0.60, 0.26, 1.0),  # 深綠
    6: (0.26, 0.90, 0.97, 1.0),  # 淺藍
    7: (0.26, 0.56, 0.90, 1.0),  # 深藍
    8: (0.51, 0.26, 0.90, 1.0),  # 紫
    9: (0.90, 0.26, 0.67, 1.0),  # 洋紅
    10: (0.75, 0.75, 0.75, 1.0),  # 淺灰
    11: (0.50, 0.50, 0.50, 1.0),  # 深灰
}


# 篩選選單處理器（使用獨立類別確保 ObjC 方法正確註冊）
filter_handler_class_name = f"FilterMenuHandler_{int(time.time() * 1000)}"


class _FilterMenuHandlerBase(NSObject):
    """篩選選單動作處理器"""

    def initWithTool_(self, tool):
        self.tool = tool
        return self

    def openColorSelector_(self, sender):
        self.tool.show_color_selector(None)

    def selectFontCharset_(self, sender):
        self.tool.selectFontCharset()

    def selectCustomCharset_(self, sender):
        self.tool.selectCustomCharset()

    def selectRecentSearch_(self, sender):
        query = sender.representedObject()
        if query:
            self.tool.run_recent_search(str(query))

    def clearHistory_(self, sender):
        self.tool.clear_recent_queries()

    def selectFavorite_(self, sender):
        char = sender.representedObject()
        if char:
            self.tool.run_favorite_search(str(char))

    def clearFavorites_(self, sender):
        self.tool.clear_favorites()

    def toggleCurrentFavorite_(self, sender):
        self.tool.toggle_current_favorite()

    def copyRelatedCharsOnly_(self, sender):
        self.tool.copy_related_chars_only(None)

    def insertAllRelated_(self, sender):
        self.tool.insert_all_related(None)

    def toggleTileView_(self, sender):
        self.tool.toggle_tile_view(None)

    def toggleListPreview_(self, sender):
        self.tool.toggle_list_preview(None)

    def cycleTileDensity_(self, sender):
        self.tool.cycle_tile_density(None)

    def toggleTileGlyphPreview_(self, sender):
        self.tool.toggle_tile_glyph_preview(None)

    def toggleTileColorLabels_(self, sender):
        self.tool.toggle_tile_color_labels(None)

    def toggleDesignedOnly_(self, sender):
        self.tool.toggle_designed_only(None)

    def selectIDSSource_(self, sender):
        source = sender.representedObject()
        if source:
            self.tool.select_ids_source(str(source))

    def openSelectedTiles_(self, sender):
        self.tool.open_selected_related_tile_objects()

    def insertSelectedTiles_(self, sender):
        self.tool.insert_selected_related_tiles(None)

    def copySelectedTiles_(self, sender):
        self.tool.copy_selected_related_tiles(None)

    def copySelectedTileUnicode_(self, sender):
        self.tool.copy_selected_tile_unicode(None)

    def searchSelectedTile_(self, sender):
        self.tool.search_selected_tile(None)

    def addSelectedTilesToFavorites_(self, sender):
        self.tool.add_selected_tiles_to_favorites(None)

    def removeSelectedTilesFromFavorites_(self, sender):
        self.tool.remove_selected_tiles_from_favorites(None)


# 使用動態名稱避免重複定義
FilterMenuHandler = type(filter_handler_class_name, (_FilterMenuHandlerBase,), {})


# 對話框色塊點擊處理器（用於顏色選擇對話框）
dialog_handler_class_name = f"DialogColorBlockHandler_{int(time.time() * 1000)}"

DialogColorBlockHandler = type(
    dialog_handler_class_name,
    (NSObject,),
    {
        "initWithTool_": lambda self, tool: setattr(self, "tool", tool) or self,
        "handleBlockClick_": lambda self, gesture: (
            self.tool.toggle_color_block_selection(
                self.tool.dialog_color_block_map.get(id(gesture.view()))
            )
            if id(gesture.view()) in self.tool.dialog_color_block_map
            else None
        ),
    },
)


# 選取變化監聽處理器（用於右側相關字區域）
selection_observer_class_name = f"SelectionObserverHandler_{int(time.time() * 1000)}"

SelectionObserverHandler = type(
    selection_observer_class_name,
    (NSObject,),
    {
        "initWithTool_": lambda self, tool: setattr(self, "tool", tool) or self,
        "textViewSelectionDidChange_": lambda self, notification: (
            self.tool.on_selection_changed(notification)
        ),
    },
)


# 右側タイル/関連字ペインのダブルクリック処理器
related_double_click_handler_class_name = f"RelatedDoubleClickHandler_{int(time.time() * 1000)}"

RelatedDoubleClickHandler = type(
    related_double_click_handler_class_name,
    (NSObject,),
    {
        "initWithTool_": lambda self, tool: setattr(self, "tool", tool) or self,
        "handleRelatedDoubleClick_": lambda self, gesture: (
            self.tool.open_selected_related_glyphs_in_new_tab(gesture)
        ),
    },
)


# 独自タイルエンジンの描画ビュー。NSTextViewの選択挙動から独立させる。
related_tile_view_class_name = f"RelatedTileObjectView_{int(time.time() * 1000)}"


def _related_tile_initWithTool_(self, tool):
    self = self.init()
    self.tool = tool
    return self


def _related_tile_isFlipped(self):
    return True


def _related_tile_acceptsFirstResponder(self):
    return True


def _related_tile_drawRect_(self, rect):
    try:
        self.tool.draw_related_tile_objects(self, rect)
    except Exception:
        import traceback
        print(traceback.format_exc())


def _related_tile_mouseDown_(self, event):
    try:
        try:
            self.window().makeFirstResponder_(self)
        except Exception:
            pass
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.tool.handle_related_tile_mouse_down(self, event, point)
    except Exception:
        import traceback
        print(traceback.format_exc())


def _related_tile_rightMouseDown_(self, event):
    try:
        try:
            self.window().makeFirstResponder_(self)
        except Exception:
            pass
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        self.tool.handle_related_tile_right_mouse_down(self, event, point)
    except Exception:
        import traceback
        print(traceback.format_exc())


RelatedTileObjectView = type(
    related_tile_view_class_name,
    (NSView,),
    {
        "initWithTool_": _related_tile_initWithTool_,
        "isFlipped": _related_tile_isFlipped,
        "acceptsFirstResponder": _related_tile_acceptsFirstResponder,
        "drawRect_": _related_tile_drawRect_,
        "mouseDown_": _related_tile_mouseDown_,
        "rightMouseDown_": _related_tile_rightMouseDown_,
    },
)


# ウィンドウ幅変更時にタイルを再レイアウトするための軽量通知ハンドラ
resize_observer_class_name = f"WindowResizeObserverHandler_{int(time.time() * 1000)}"

ResizeObserverHandler = type(
    resize_observer_class_name,
    (NSObject,),
    {
        "initWithTool_": lambda self, tool: setattr(self, "tool", tool) or self,
        "windowDidResize_": lambda self, notification: self.tool.on_window_resized(notification),
        "splitViewDidResizeSubviews_": lambda self, notification: self.tool.on_results_split_resized(notification),
    },
)


class HanziComponentSearchTool:
    """Glyphs 外掛主視窗"""

    # 字型快取（類別層級）
    _font_cache = {}  # key: (char, size), value: NSFont
    _CACHE_MAX_SIZE = 500  # 最大快取數量

    def __init__(self, title=None):
        # === 設定與 IDS 核心 ===
        self.settings = GlyphsSettings()
        self.ids_source = self.settings.get("idsSource", DEFAULT_IDS_SOURCE)
        if self.ids_source not in IDS_SOURCE_OPTIONS:
            self.ids_source = DEFAULT_IDS_SOURCE
        self.active_ids_source = None
        self.core = self._load_selected_core()

        # === 初始化 Glyphs 適配器 ===
        self.adapter = GlyphsAdapter()

        # === 初始化基本屬性 ===
        self.currentCharset: Set[str] = set()
        self.all_results = []  # 存儲 (tree, content) 格式的原始結果
        self.display_results = []  # 存儲顯示用的字符串
        self.current_char = None
        self.last_related_text = ""
        self.related_display_char = None
        self.last_result_count = 0
        self._glyph_status_cache = {}
        self._status_counts_cache_key = None
        self._status_counts_cache_value = None
        self.relatedDoubleClickRecognizer = None
        self.resizeObserver = None
        self.last_related_selection_chars = ""
        self.last_related_multi_selection_chars = ""
        self.last_related_multi_selection_time = 0
        self.recent_queries = list(self.settings.get("recentQueries", []) or [])[:12]
        self.favorite_chars = list(self.settings.get("favoriteChars", []) or [])[:64]
        self.tile_view_enabled = bool(self.settings.get("tileViewEnabled", True))
        self.list_preview_enabled = bool(self.settings.get("listPreviewEnabled", True))
        self.tile_glyph_preview_enabled = bool(self.settings.get("tileGlyphPreviewEnabled", False))
        self.tile_color_labels_enabled = bool(self.settings.get("tileColorLabelsEnabled", False))
        self.show_designed_only = bool(self.settings.get("showDesignedOnly", False))
        self.related_tile_items = []
        self.related_tile_rows = []
        self.related_tile_row_bottoms = []
        self.related_tile_selection = set()
        self.related_tile_anchor_index = None
        self.related_tile_layout_width = 0
        self.related_tile_content_height = 1
        self.relatedTileScrollView = None
        self.relatedTileView = None
        self.tile_density = self.settings.get("tileDensity", "comfortable")
        if self.tile_density not in ("compact", "comfortable", "spacious"):
            self.tile_density = "comfortable"
        self.visual_effects_enabled = bool(self.settings.get("visualEffectsEnabled", True))
        self.deep_analysis = self.settings.get("deepAnalysis", False)
        self.show_derived = False

        # 多部件 AND 搜尋模式狀態
        self.multi_component_mode = False  # 是否處於多部件模式
        self.multi_component_parts = []  # 當前輸入的部件清單（用於回到交集視角）
        self.saved_show_derived = False  # 進入多部件模式前的衍生字開關，離開時恢復
        self.saved_deep_analysis = False  # 進入多部件模式前的深度拆解開關，離開時恢復

        # 自動抓取設定（固定為 True）
        self.auto_fetch_enabled = True
        self.last_glyph_name = None

        # 模式切換：自動模式 vs 手動模式
        # 自動模式：選擇字符時清空搜尋框，使用多 Unicode 智能偵測
        # 手動模式：用戶輸入時觸發，直接搜尋輸入內容
        self.is_manual_mode = False

        # 顏色篩選設定
        self.filter_colors = self.settings.get("filterColors", [])
        self.dialog_color_block_map = {}  # 對話框色塊到 color_id 的映射
        self.color_blocks = {}  # 對話框 color_id 到色塊的映射
        self.color_block_states = {}  # 追蹤對話框色塊選取狀態

        # IDS 切換狀態
        self.current_ids_index = 0  # 目前顯示的 IDS 索引（0 或 1）
        self.available_ids = []  # 當前字符可用的 IDS 列表

        # === 字集管理（簡化版）===
        self.custom_charset_path = None  # 自訂字集檔案路徑
        self.custom_charset_name = None  # 自訂字集檔案名稱
        self.use_custom_charset = False  # 是否使用自訂字集

        # === 建立主視窗 ===
        window_title = title or L("window_title")
        self.w = vanilla.FloatingWindow(
            (880, 640),
            window_title,
            minSize=(720, 500),
            maxSize=(1600, 1200),
            autosaveName="com.HanziComponentExplorerRSplus.MainWindow",
        )

        # === 頂部搜尋區域 ===
        self.w.inputText = vanilla.SearchBox(
            (12, 12, -204, 24),
            placeholder=L("search_placeholder"),
            callback=self.search_callback,
        )

        history_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "clock.arrow.circlepath", None
        )
        self.w.historyButton = vanilla.ImageButton(
            (-194, 11, 24, 24),
            imageObject=history_icon,
            callback=self.show_history_menu,
            bordered=False,
        )
        self._style_icon_button(self.w.historyButton, L("btn_history_tooltip"))

        clear_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "xmark.circle", None
        )
        self.w.clearButton = vanilla.ImageButton(
            (-162, 11, 24, 24),
            imageObject=clear_icon,
            callback=self.clear_search,
            bordered=False,
        )
        self._style_icon_button(self.w.clearButton, L("btn_clear_search_tooltip"))

        favorite_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "star", None
        )
        self.w.favoritesButton = vanilla.ImageButton(
            (-130, 11, 24, 24),
            imageObject=favorite_icon,
            callback=self.show_favorites_menu,
            bordered=False,
        )
        self._style_icon_button(self.w.favoritesButton, L("btn_favorites_tooltip"))

        tile_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "square.grid.3x3", None
        )
        self.w.tileButton = vanilla.ImageButton(
            (-98, 11, 24, 24),
            imageObject=tile_icon,
            callback=self.toggle_tile_view,
            bordered=False,
        )
        self._style_icon_button(self.w.tileButton, L("btn_tile_view_tooltip"))

        density_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "textformat.size", None
        )
        self.w.tileDensityButton = vanilla.ImageButton(
            (-66, 11, 24, 24),
            imageObject=density_icon,
            callback=self.cycle_tile_density,
            bordered=False,
        )
        self._style_icon_button(self.w.tileDensityButton, L("btn_tile_density_tooltip"))

        insert_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "arrow.up.forward.square", None
        )
        self.w.insertButton = vanilla.ImageButton(
            (-34, 11, 24, 24),
            imageObject=insert_icon,
            callback=self.insert_selected_text,
            bordered=False,
        )
        self._style_icon_button(self.w.insertButton, L("btn_insert_tooltip"))
        self.w.insertButton.enable(False)

        self._install_visual_cards()

        self.w.summaryChar = vanilla.TextBox((12, 44, 92, 58), "—", alignment="center")
        self.w.summaryMeta = vanilla.TextBox((116, 46, 210, 52), "", sizeStyle="small")
        self.w.summaryStats = vanilla.TextBox((338, 46, 250, 34), "", sizeStyle="small")
        self.w.summaryMode = vanilla.TextBox((338, 82, 250, 18), "", sizeStyle="small")
        self.w.summaryHint = vanilla.TextBox((600, 46, -12, 32), L("summary_hint"), sizeStyle="small")
        self.w.summaryLegend = vanilla.TextBox((600, 82, -12, 18), "", sizeStyle="small")

        # === 讀取設定 ===
        self.show_derived = self.settings.get("showDerived", False)

        # 筆畫篩選 tick（0..4 為 ±0/±1/±2/±3/±5；5 為關閉），預設關閉
        raw_tick = self.settings.get("strokeFilterTick", STROKE_FILTER_OFF_TICK)
        try:
            self.stroke_filter_tick = int(raw_tick)
        except (TypeError, ValueError):
            self.stroke_filter_tick = STROKE_FILTER_OFF_TICK
        if not 0 <= self.stroke_filter_tick < STROKE_FILTER_TICK_COUNT:
            self.stroke_filter_tick = STROKE_FILTER_OFF_TICK

        # === 左側資訊區 ===
        # 預覽區
        self.w.preview = vanilla.TextBox((12, 114, 126, 126), "", alignment="center")
        try:
            self.w.previewImage = vanilla.ImageView((28, 124, 94, 94))
            self.w.previewImage.show(False)
        except Exception:
            self.w.previewImage = None
        self.w.previewStatus = vanilla.TextBox((12, 242, 126, 24), "", alignment="center", sizeStyle="small")
        self.w.previewMeta = vanilla.TextBox((12, 266, 126, 18), "", alignment="center", sizeStyle="small")

        # 詳細資訊區（向下擴展到視窗底部）
        self.w.content = vanilla.TextEditor((12, 292, 126, -50), "", readOnly=True)

        # === 可変のツリー／関連字ペイン ===
        # 深いIDSツリーは固定幅では読みにくいため、ネイティブの分割バーで
        # ツリーと関連字の幅を自由に調整できるようにする。
        self.treePane = vanilla.Group((0, 0, -0, -0))
        self.treePane.idsSwitcher = vanilla.Group((4, 0, -4, 20))
        self.treePane.idsSwitcher.prevButton = vanilla.Button(
            (0, 0, 35, 20), "◀", callback=self.prev_ids, sizeStyle="small"
        )
        self.treePane.idsSwitcher.indicator = vanilla.TextBox(
            (40, 0, -80, 20), "1/2", alignment="center", sizeStyle="small"
        )
        self.treePane.idsSwitcher.nextButton = vanilla.Button(
            (-35, 0, 35, 20), "▶", callback=self.next_ids, sizeStyle="small"
        )
        self.treePane.idsSwitcher.show(False)
        self.treePane.resultList = vanilla.List(
            (4, 24, -4, -0), [], selectionCallback=self.selection_callback
        )

        # 樹形図の枝線を揃えるため、可能なら等幅システムフォントを使う。
        try:
            result_list_font = NSFont.monospacedSystemFontOfSize_weight_(RESULT_LIST_FONT_SIZE, 0.0)
        except Exception:
            result_list_font = self.get_font_for_char("漢", RESULT_LIST_FONT_SIZE)
        tableView = self.treePane.resultList.getNSTableView()
        for column in tableView.tableColumns():
            column.dataCell().setFont_(result_list_font)

        # 啟用橫向捲軸：禁用欄位自動調整，讓欄位可以超出視窗寬度
        tableView.setColumnAutoresizingStyle_(NSTableViewNoColumnAutoresizing)
        for column in tableView.tableColumns():
            column.setMinWidth_(250)
            column.setMaxWidth_(2000)
            # 停用文字省略，改為裁切（搭配橫向捲軸使用）
            column.dataCell().setLineBreakMode_(NSLineBreakByClipping)

        # === 右側関連字エリア ===
        # 旧TextEditorはテキストモード/フォールバック用に保持。
        self.relatedPane = vanilla.Group((0, 0, -0, -0))
        self.relatedPane.relatedChars = vanilla.TextEditor((4, 4, -4, -4), "", readOnly=True)
        self.relatedPane.relatedTileHost = vanilla.Group((4, 4, -4, -4))

        self.w.resultsSplit = vanilla.SplitView(
            (150, 108, -8, -46),
            [
                dict(
                    view=self.treePane,
                    identifier="idsTree",
                    size=258,
                    minSize=190,
                    canCollapse=False,
                    resizeFlexibility=False,
                ),
                dict(
                    view=self.relatedPane,
                    identifier="relatedCharacters",
                    minSize=280,
                    canCollapse=False,
                    resizeFlexibility=True,
                ),
            ],
            isVertical=True,
            # A standard splitter gives the divider a clear visual grip and a
            # comfortably wide hit target, including macOS's resize cursor.
            dividerStyle="splitter",
            dividerThickness=8,
            autosaveName="com.HanziComponentExplorerRSplus.ResultsSplit",
        )
        self._install_related_tile_engine()
        self._sync_related_display_mode()

        # 相關字區域の字型/タイルは update_related_display で動的に更新

        # === 底部控制列 ===
        # 全字庫連結按鈕（左側區域下方，SF Symbols 圖示）
        try:
            # 使用 .zh 後綴強制顯示中文字元，符合「全字庫」的定位
            cns_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
                "character.book.closed.zh", "CNS11643"
            )
        except Exception:
            cns_icon = None

        self.w.cnsLinkButton = vanilla.ImageButton(
            (12, -37, 24, 24),
            imageObject=cns_icon,
            callback=self.open_cns_link,
            bordered=False,
        )
        self._style_icon_button(self.w.cnsLinkButton, L("btn_cns_tooltip"))
        self.w.cnsLinkButton.enable(False)

        copy_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "doc.on.doc", None
        )
        self.w.copyRelatedButton = vanilla.ImageButton(
            (44, -37, 24, 24),
            imageObject=copy_icon,
            callback=self.copy_related_text,
            bordered=False,
        )
        self._style_icon_button(self.w.copyRelatedButton, L("btn_copy_related_tooltip"))
        self.w.copyRelatedButton.enable(False)

        search_selected_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "magnifyingglass.circle", None
        )
        self.w.searchSelectedButton = vanilla.ImageButton(
            (76, -37, 24, 24),
            imageObject=search_selected_icon,
            callback=self.search_selected_text,
            bordered=False,
        )
        self._style_icon_button(self.w.searchSelectedButton, L("btn_search_selected_tooltip"))
        self.w.searchSelectedButton.enable(False)

        insert_all_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "rectangle.stack.badge.plus", None
        )
        self.w.insertAllButton = vanilla.ImageButton(
            (108, -37, 24, 24),
            imageObject=insert_all_icon,
            callback=self.insert_all_related,
            bordered=False,
        )
        self._style_icon_button(self.w.insertAllButton, L("btn_insert_all_tooltip"))
        self.w.insertAllButton.enable(False)

        # 深度拆解開關（中間區域下方）
        self.w.deepAnalysisCheckbox = vanilla.CheckBox(
            (154, -36, 92, 22),
            L("checkbox_deep_analysis"),
            callback=self.toggle_deep_analysis,
            value=self.deep_analysis,
        )

        # 衍生字勾選框（右側區域左下角）
        self.w.showDerivedCheckbox = vanilla.CheckBox(
            (252, -36, 72, 22),
            L("checkbox_derived"),
            callback=self.toggle_derived_display,
            value=self.show_derived,
        )

        # 筆畫篩選滑桿（與衍生字 checkbox 之間，右側留空間給狀態文字）
        # tickMarkCount=6 對應 [±0, ±1, ±2, ±3, ±5, OFF]
        self.w.strokeFilterSlider = vanilla.Slider(
            (334, -34, -112, 18),
            minValue=0,
            maxValue=STROKE_FILTER_OFF_TICK,
            value=self.stroke_filter_tick,
            tickMarkCount=STROKE_FILTER_TICK_COUNT,
            stopOnTickMarks=True,
            sizeStyle="small",
            callback=self.on_stroke_filter_changed,
        )

        # 筆畫篩選當前值顯示（滑桿右側，常駐可見）
        # 使用 left 對齊讓文字緊貼滑桿右緣，不會因 OFF/±N 長度不同產生視覺空隙
        self.w.strokeFilterValue = vanilla.TextBox(
            (-108, -33, 34, 17),
            "",
            alignment="left",
            sizeStyle="small",
        )
        self._refresh_stroke_filter_display()

        # 篩選按鈕（右下角）
        filter_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "line.3.horizontal.decrease.circle", None
        )
        self.w.filterButton = vanilla.ImageButton(
            (-34, -37, 24, 24),
            imageObject=filter_icon,
            callback=self.show_filter_menu,
            bordered=False,
        )
        self._style_icon_button(self.w.filterButton, L("btn_filter_tooltip"))

        # === 載入字集設定 ===
        # 載入上次的自訂字集設定（如果有）
        saved_path = self.settings.get("customCharsetPath")
        if saved_path and os.path.exists(saved_path):
            self.custom_charset_path = saved_path
            self.custom_charset_name = os.path.basename(saved_path)
            self.use_custom_charset = True
            self.loadCustomCharset(saved_path)
        # 若無自訂字集，由下方 loadFontCharset 統一處理

        # 註：移除 setFrameUsingName_ 以避免載入舊版本的視窗尺寸設定
        # 未來可以考慮使用 GlyphsSettings 自行管理視窗位置和尺寸
        # 註：暫時也移除 setResizeIncrements_ 以避免視窗自動擴張問題
        # self.w.getNSWindow().setResizeIncrements_((1.0, 1.0))

        # 綁定視窗關閉事件
        self.w.bind("close", self.windowWillClose)

        # 綁定視窗焦點事件（Issue #31：視窗聚焦模式）
        self.w.bind("became key", self.on_window_became_key)
        self.w.bind("resigned key", self.on_window_resigned_key)

        # 建立事件處理器
        self.selectionObserver = SelectionObserverHandler.alloc().initWithTool_(self)
        self.filterMenuHandler = FilterMenuHandler.alloc().initWithTool_(self)
        self.dialogColorBlockHandler = DialogColorBlockHandler.alloc().initWithTool_(
            self
        )
        self.relatedDoubleClickHandler = RelatedDoubleClickHandler.alloc().initWithTool_(
            self
        )
        self.resizeObserver = ResizeObserverHandler.alloc().initWithTool_(self)

        # 初始化顏色篩選 tooltip
        self.update_color_display()

        self.w.open()
        self._refresh_results_split_interaction(initial_layout=True)
        # 在視窗開啟後更新相關顯示
        self.update_related_display()
        # 設定右側相關字區域的選取監聽 / ダブルクリック動作
        self.setup_selection_observer()
        self.setup_related_double_click_handler()
        self.setup_window_resize_observer()

        # 註冊 Glyphs 回調以監聽字符變化
        self.adapter.register_callback(self.on_glyph_changed)

        # 如果沒有自訂字集，才載入字型檔字集作為預設篩選
        if not self.use_custom_charset:
            self.loadFontCharset(trigger_search=False)

        # 開啟時立即抓取當前字符並執行搜尋
        self.on_glyph_changed()

    def _style_icon_button(self, button, tooltip=None):
        """Apply compact macOS toolbar button styling."""
        try:
            ns_button = button.getNSButton()
            ns_button.setBezelStyle_(11)
            ns_button.setButtonType_(0)
            ns_button.setShowsBorderOnlyWhileMouseInside_(True)
            ns_button.setBordered_(True)
            if tooltip:
                ns_button.setToolTip_(tooltip)
        except Exception:
            pass

    def _semantic_color(self, name, fallback_name="labelColor"):
        try:
            return getattr(NSColor, name)()
        except Exception:
            try:
                return getattr(NSColor, fallback_name)()
            except Exception:
                return NSColor.blackColor()

    def _card_fill_color(self):
        """Lightweight card fill: enough separation without heavy boxed UI."""
        return self._with_alpha(
            self._semantic_color("controlBackgroundColor", "windowBackgroundColor"), 0.68
        )

    def _card_border_color(self):
        """Very subtle separator color for modern, quiet card edges."""
        return self._with_alpha(
            self._semantic_color("separatorColor", "secondaryLabelColor"), 0.22
        )

    def _install_visual_cards(self):
        """Install subtle card backgrounds before controls are added."""
        if not self.visual_effects_enabled:
            return
        specs = [
            ("summaryCard", (8, 40, -8, 66), 12.0),
            ("previewCard", (8, 108, 134, 170), 14.0),
            ("contentCard", (8, 288, 134, -46), 10.0),
        ]
        for attr, rect, radius in specs:
            try:
                box = vanilla.Box(rect)
                setattr(self.w, attr, box)
                ns_box = box.getNSBox()
                ns_box.setTitle_("")
                ns_box.setBoxType_(NSBoxCustom)
                ns_box.setCornerRadius_(radius)
                ns_box.setFillColor_(self._card_fill_color())
                ns_box.setBorderType_(1)
                ns_box.setBorderWidth_(0.35)
                ns_box.setBorderColor_(self._card_border_color())
            except Exception:
                pass

    def _with_alpha(self, color, alpha):
        """Return color with alpha when available, otherwise the original color."""
        try:
            return color.colorWithAlphaComponent_(alpha)
        except Exception:
            return color

    def _install_related_tile_engine(self):
        """Create the object-tile scroll view.

        This replaces tile selection implemented through NSTextView selection. The
        old TextEditor remains available as a safe fallback and for non-tile mode.
        """
        try:
            host_view = self.relatedPane.relatedTileHost.getNSView()
            scroll = NSScrollView.alloc().initWithFrame_(host_view.bounds())
            scroll.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
            scroll.setHasVerticalScroller_(True)
            scroll.setHasHorizontalScroller_(False)
            scroll.setAutohidesScrollers_(True)
            scroll.setDrawsBackground_(False)
            scroll.setBorderType_(0)

            tile_view = RelatedTileObjectView.alloc().initWithTool_(self)
            tile_view.setFrame_(NSMakeRect(0, 0, max(1, host_view.bounds().size.width), 1))
            try:
                tile_view.setAutoresizingMask_(NSViewWidthSizable)
            except Exception:
                pass
            scroll.setDocumentView_(tile_view)
            host_view.addSubview_(scroll)
            self.relatedTileScrollView = scroll
            self.relatedTileView = tile_view
            try:
                tile_view.setToolTip_(L("tooltip_related_object_tiles"))
            except Exception:
                pass
        except Exception:
            import traceback
            print(traceback.format_exc())
            self.relatedTileScrollView = None
            self.relatedTileView = None

    def _tile_engine_available(self):
        return bool(getattr(self, "relatedTileView", None) is not None and getattr(self, "relatedTileScrollView", None) is not None)

    def _sync_related_display_mode(self):
        """Show object tiles when possible; otherwise fall back to text."""
        use_object_tiles = bool(self.tile_view_enabled and self._tile_engine_available())
        try:
            self.relatedPane.relatedTileHost.show(use_object_tiles)
        except Exception:
            pass
        try:
            self.relatedPane.relatedChars.show(not use_object_tiles)
        except Exception:
            pass
        return use_object_tiles

    def _related_tile_available_width(self):
        """現在の右ペイン幅を取得し、タイル折り返し幅として使う。"""
        try:
            if self.relatedTileScrollView is not None:
                return max(1, int(self.relatedTileScrollView.contentView().bounds().size.width))
        except Exception:
            pass
        try:
            if self.relatedTileView is not None:
                return max(1, int(self.relatedTileView.bounds().size.width))
        except Exception:
            pass
        return 420

    def _relayout_related_tiles_to_scroll_width(self):
        """ウィンドウ幅に追従して右タイルを再折り返しする。"""
        if not self._tile_engine_available() or not self.related_tile_items:
            return
        try:
            width = self._related_tile_available_width()
            height = self._layout_related_tile_items(width)
            self.relatedTileView.setFrameSize_(NSMakeSize(width, height))
            self.relatedTileView.setNeedsDisplay_(True)
        except Exception:
            pass

    def _refresh_results_split_interaction(self, initial_layout=False):
        """Make the divider's resize cursor available on its first display."""
        try:
            split_view = self.w.resultsSplit.getNSSplitView()
            if initial_layout:
                split_view.adjustSubviews()
            split_view.setNeedsDisplay_(True)
            window = split_view.window()
            if window is not None:
                window.invalidateCursorRectsForView_(split_view)
            split_view.resetCursorRects()
        except Exception:
            pass

    def _tile_geometry_config(self):
        """Tile dimensions tuned for each density."""
        configs = {
            "compact": {
                "tile_w": 54, "tile_h": 48, "gap": 7, "pad": 10,
                "char_size": 22, "badge_size": 12, "preview_size": 25,
                "label_h": 24, "separator_h": 16, "corner": 9,
            },
            "comfortable": {
                "tile_w": 68, "tile_h": 62, "gap": 9, "pad": 12,
                "char_size": 27, "badge_size": 13, "preview_size": 34,
                "label_h": 26, "separator_h": 18, "corner": 11,
            },
            "spacious": {
                "tile_w": 84, "tile_h": 78, "gap": 12, "pad": 14,
                "char_size": 34, "badge_size": 15, "preview_size": 46,
                "label_h": 30, "separator_h": 20, "corner": 13,
            },
        }
        return configs.get(self.tile_density, configs["comfortable"])

    def _invalidate_status_cache(self):
        """Clear cached glyph status used by lists, tiles, and summary badges."""
        self._glyph_status_cache = {}
        self._status_counts_cache_key = None
        self._status_counts_cache_value = None

    def _raw_glyph_status(self, char):
        """Fetch Glyphs design status once per character for the current render pass."""
        if not char:
            return {}
        cache_key = char
        if cache_key in self._glyph_status_cache:
            return self._glyph_status_cache[cache_key]
        try:
            status = self.adapter.get_glyph_design_status(self.adapter.get_current_font(), char) or {}
        except Exception:
            status = {}
        self._glyph_status_cache[cache_key] = status
        return status

    def _glyph_status_payload(self, char):
        """Canonical status payload shared by result rows, tiles, and summaries."""
        return status_payload(
            char,
            self._raw_glyph_status(char),
            favorite=char in self.favorite_chars,
        )

    def _glyph_status_key(self, char):
        return self._glyph_status_payload(char).get("status", STATUS_MISSING)

    def _glyph_color_id(self, char):
        """Return the Glyphs color-label id for char, preserving color 0 as valid."""
        try:
            color_id = self._raw_glyph_status(char).get("color")
            if color_id is None:
                return None
            return int(color_id)
        except Exception:
            return None

    def _color_label_nscolor(self, color_id):
        """Convert a Glyphs color-label id to NSColor; color 0 is a valid label."""
        try:
            color_id = int(color_id)
        except Exception:
            return None
        rgba = GLYPH_COLOR_MAP.get(color_id)
        if rgba is None:
            return None
        try:
            return NSColor.colorWithCalibratedRed_green_blue_alpha_(*rgba)
        except Exception:
            return None

    def _glyph_label_color(self, char):
        """Return an NSColor for a Glyphs color label, or None when unlabeled."""
        return self._color_label_nscolor(self._glyph_color_id(char))

    def _tile_status_payload(self, char):
        payload = self._glyph_status_payload(char)
        color_id = self._glyph_color_id(char)
        return {
            "status": payload["status"],
            "marker": payload["marker"],
            "favorite": payload["favorite"],
            "color": color_id,
        }

    def _apply_related_status_filter(self, text):
        """右ペイン用の状態フィルター。現在は「制作済みのみ」を提供する。"""
        if not self.show_designed_only:
            return text
        lines = []
        for raw_line in (text or "").splitlines():
            line = raw_line.strip()
            if not line or set(line) == {"-"}:
                continue
            label = None
            payload = line
            if " " in line:
                label, payload = line.split(" ", 1)
            filtered = []
            for ch in payload:
                try:
                    if self.core.is_valid_character(ch) and self._glyph_status_key(ch) == STATUS_DESIGNED:
                        filtered.append(ch)
                except Exception:
                    pass
            if filtered:
                lines.append((f"{label} {''.join(filtered)}") if label else "".join(filtered))
        return "\n".join(lines)

    def _build_related_tile_items(self, text):
        """Build semantic tile objects from the canonical related text.

        The tile engine stores each character in an object dictionary so selection
        and double-click actions never depend on NSTextView ranges or status glyphs.
        """
        items = []
        order = 0
        for raw_line in (text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if set(line) == {"-"}:
                items.append({"kind": "separator", "text": ""})
                continue
            label = None
            payload = line
            if " " in line:
                label, payload = line.split(" ", 1)
                if label:
                    items.append({"kind": "label", "text": label})
            for ch in payload:
                try:
                    if self.core.is_valid_character(ch):
                        status_payload = self._tile_status_payload(ch)
                        items.append({
                            "kind": "tile",
                            "char": ch,
                            "order": order,
                            "status": status_payload["status"],
                            "marker": status_payload["marker"],
                            "favorite": status_payload["favorite"],
                            "color": status_payload.get("color"),
                            "rect": (0, 0, 0, 0),
                        })
                        order += 1
                except Exception:
                    pass
        return items

    def _layout_related_tile_items(self, width=None):
        if not self.related_tile_items:
            self.related_tile_content_height = 1
            self.related_tile_rows = []
            self.related_tile_row_bottoms = []
            return 1
        cfg = self._tile_geometry_config()
        pad, gap = cfg["pad"], cfg["gap"]
        tile_w, tile_h = cfg["tile_w"], cfg["tile_h"]
        width = int(width or 360)
        width = max(width, tile_w + pad * 2)
        x = pad
        y = pad
        row_open = False
        for item in self.related_tile_items:
            kind = item.get("kind")
            if kind == "label":
                if row_open:
                    y += tile_h + gap
                    row_open = False
                item["rect"] = (pad, y, max(1, width - pad * 2), cfg["label_h"])
                y += cfg["label_h"] + max(4, gap // 2)
                x = pad
            elif kind == "separator":
                if row_open:
                    y += tile_h + gap
                    row_open = False
                item["rect"] = (pad, y + cfg["separator_h"] / 2.0, max(1, width - pad * 2), 1)
                y += cfg["separator_h"]
                x = pad
            else:
                if x + tile_w > width - pad and x > pad:
                    x = pad
                    y += tile_h + gap
                item["rect"] = (x, y, tile_w, tile_h)
                x += tile_w + gap
                row_open = True
        if row_open:
            y += tile_h
        y += pad
        self.related_tile_content_height = max(1, int(y))
        self.related_tile_layout_width = width
        self._rebuild_related_tile_row_index()
        return self.related_tile_content_height

    def _rebuild_related_tile_row_index(self):
        """Index tile rows so scrolling does not scan every result item."""
        rows = []
        for index, item in enumerate(self.related_tile_items):
            x, y, width, height = item.get("rect", (0, 0, 0, 0))
            if rows and abs(rows[-1]["y"] - y) < 0.5:
                row = rows[-1]
            else:
                row = {"y": y, "bottom": y + height, "indexes": []}
                rows.append(row)
            row["bottom"] = max(row["bottom"], y + height)
            row["indexes"].append(index)
        self.related_tile_rows = rows
        self.related_tile_row_bottoms = [row["bottom"] for row in rows]

    def _tile_indexes_in_dirty_rect(self, dirty_rect):
        """Return only the rows AppKit has asked the tile view to repaint."""
        try:
            minimum_y = float(dirty_rect.origin.y)
            maximum_y = minimum_y + float(dirty_rect.size.height)
        except Exception:
            return range(len(self.related_tile_items))
        start = bisect_right(self.related_tile_row_bottoms, minimum_y)
        visible_indexes = []
        for row in self.related_tile_rows[start:]:
            if row["y"] >= maximum_y:
                break
            visible_indexes.extend(row["indexes"])
        return visible_indexes

    def _render_related_tiles_from_display_text(self, text):
        """Render current related output into the object-tile engine."""
        self.related_tile_items = self._build_related_tile_items(text)
        self.related_tile_selection = set()
        self.related_tile_anchor_index = None
        if not self._tile_engine_available():
            return False
        width = self._related_tile_available_width()
        height = self._layout_related_tile_items(width)
        try:
            self.relatedTileView.setFrameSize_(NSMakeSize(width, height))
            self.relatedTileView.setNeedsDisplay_(True)
        except Exception:
            pass
        self._sync_related_display_mode()
        return True

    def _set_related_text_fallback(self, display_text):
        rendered_text = self._tile_lines_from_display_text(display_text)
        attr_string = self.create_related_attributed_string(
            rendered_text,
            self._tile_density_config()["font_size"] if self.tile_view_enabled else RELATED_CHARS_FONT_SIZE,
        )
        text_view = self.relatedPane.relatedChars.getNSTextView()
        text_view.textStorage().setAttributedString_(attr_string)

    def _set_related_output(self, display_text, focus_char=None, result_count=None, hint=None):
        """Single rendering gateway for right-pane text fallback and object tiles."""
        self._invalidate_status_cache()
        display_text = self.core.clean_display_text(display_text or "")
        display_text = self._apply_related_status_filter(display_text)
        self.last_related_text = display_text
        filtered_count = len(self._related_characters_only(display_text))
        self.last_result_count = filtered_count if (self.show_designed_only or result_count is None) else result_count
        if self.tile_view_enabled and self._tile_engine_available():
            self._render_related_tiles_from_display_text(display_text)
        else:
            self._sync_related_display_mode()
            self._set_related_text_fallback(display_text)
        self._refresh_result_action_buttons()
        self._refresh_summary_panel(focus_char=focus_char, result_count=self.last_result_count, hint=hint)

    def _tile_item_at_point(self, point):
        try:
            px, py = float(point.x), float(point.y)
        except Exception:
            return None
        for idx, item in enumerate(self.related_tile_items):
            if item.get("kind") != "tile":
                continue
            x, y, w, h = item.get("rect", (0, 0, 0, 0))
            if x <= px <= x + w and y <= py <= y + h:
                return idx
        return None

    def _select_related_tile_index(self, idx, event=None):
        """Update tile selection; Command toggles, Shift range-selects."""
        if idx is None:
            self.related_tile_selection = set()
            self.related_tile_anchor_index = None
            return
        flags = 0
        try:
            flags = int(event.modifierFlags()) if event is not None else 0
        except Exception:
            flags = 0
        shift_down = bool(flags & (1 << 17))
        command_down = bool(flags & (1 << 20))
        if shift_down and self.related_tile_anchor_index is not None:
            a, b = sorted((self.related_tile_anchor_index, idx))
            self.related_tile_selection = {
                i for i in range(a, b + 1)
                if i < len(self.related_tile_items) and self.related_tile_items[i].get("kind") == "tile"
            }
        elif command_down:
            if idx in self.related_tile_selection:
                self.related_tile_selection.remove(idx)
            else:
                self.related_tile_selection.add(idx)
            self.related_tile_anchor_index = idx
        else:
            self.related_tile_selection = {idx}
            self.related_tile_anchor_index = idx

    def handle_related_tile_mouse_down(self, view, event, point):
        idx = self._tile_item_at_point(point)
        click_count = 1
        try:
            click_count = int(event.clickCount())
        except Exception:
            pass
        if idx is None:
            if click_count < 2:
                self.related_tile_selection = set()
                self.related_tile_anchor_index = None
                self._refresh_result_action_buttons()
                try:
                    view.setNeedsDisplay_(True)
                except Exception:
                    pass
            return
        if click_count >= 2:
            # If the tile is outside the current multi-selection, use the clicked tile.
            if idx not in self.related_tile_selection:
                self.related_tile_selection = {idx}
                self.related_tile_anchor_index = idx
            self.open_selected_related_tile_objects()
        else:
            self._select_related_tile_index(idx, event)
            self._refresh_result_action_buttons()
            try:
                view.setNeedsDisplay_(True)
            except Exception:
                pass

    def handle_related_tile_right_mouse_down(self, view, event, point):
        """タイル右クリック：選択を保ったままコンテキストメニューを出す。"""
        idx = self._tile_item_at_point(point)
        if idx is not None:
            # 既存の複数選択上で右クリックした場合は選択を維持。
            if idx not in self.related_tile_selection:
                self.related_tile_selection = {idx}
                self.related_tile_anchor_index = idx
        self._refresh_result_action_buttons()
        try:
            view.setNeedsDisplay_(True)
        except Exception:
            pass
        self.show_related_tile_context_menu(view, event)

    def _selected_or_all_tile_chars_for_menu(self):
        chars = self._selected_tile_chars()
        return chars or self._related_characters_only()

    def show_related_tile_context_menu(self, view, event):
        """選択タイル用の右クリックメニュー。"""
        from AppKit import NSMenu, NSMenuItem
        menu = NSMenu.alloc().init()
        selected_chars = self._selected_tile_chars()
        has_selection = bool(selected_chars)
        header_title = L("menu_tile_context_header").format(count=len(selected_chars), text=selected_chars) if has_selection else L("menu_tile_context_no_selection")
        header = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(header_title, None, "")
        header.setEnabled_(False)
        menu.addItem_(header)

        entries = [
            (L("menu_open_selected_tiles"), "openSelectedTiles:"),
            (L("menu_insert_selected_tiles"), "insertSelectedTiles:"),
            (L("menu_copy_selected_tiles"), "copySelectedTiles:"),
            (L("menu_copy_selected_tile_unicode"), "copySelectedTileUnicode:"),
            (L("menu_search_selected_tile"), "searchSelectedTile:"),
        ]
        for title, action in entries:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
            item.setTarget_(self.filterMenuHandler)
            item.setEnabled_(has_selection)
            menu.addItem_(item)
        menu.addItem_(NSMenuItem.separatorItem())
        add_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_add_selected_to_favorites"), "addSelectedTilesToFavorites:", "")
        add_item.setTarget_(self.filterMenuHandler)
        add_item.setEnabled_(has_selection)
        menu.addItem_(add_item)
        remove_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_remove_selected_from_favorites"), "removeSelectedTilesFromFavorites:", "")
        remove_item.setTarget_(self.filterMenuHandler)
        remove_item.setEnabled_(has_selection)
        menu.addItem_(remove_item)
        try:
            NSMenu.popUpContextMenu_withEvent_forView_(menu, event, view)
        except Exception:
            try:
                menu.popUpMenuPositioningItem_atLocation_inView_(None, event.locationInWindow(), view)
            except Exception:
                pass

    def _selected_tile_chars(self):
        if not self.related_tile_selection:
            return ""
        pairs = []
        for idx in self.related_tile_selection:
            if 0 <= idx < len(self.related_tile_items):
                item = self.related_tile_items[idx]
                if item.get("kind") == "tile" and item.get("char"):
                    pairs.append((item.get("order", idx), item.get("char")))
        pairs.sort(key=lambda p: p[0])
        seen = set()
        chars = []
        for _, ch in pairs:
            if ch not in seen:
                seen.add(ch)
                chars.append(ch)
        return "".join(chars)

    def _tile_status_colors(self):
        return {
            STATUS_DESIGNED: self._semantic_color("systemGreenColor", "labelColor"),
            STATUS_EXISTS: self._semantic_color("systemBlueColor", "labelColor"),
            STATUS_MISSING: self._semantic_color("tertiaryLabelColor", "secondaryLabelColor"),
            STATUS_FAVORITE: self._semantic_color("systemOrangeColor", "labelColor"),
            "accent": self._semantic_color("controlAccentColor", "systemBlueColor"),
        }

    def _draw_rounded_rect(self, rect, fill_color, stroke_color=None, line_width=1.0, radius=8.0):
        try:
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, radius, radius)
            fill_color.setFill()
            path.fill()
            if stroke_color is not None:
                stroke_color.setStroke()
                path.setLineWidth_(line_width)
                path.stroke()
        except Exception:
            pass

    def _draw_text_in_rect(self, text, rect, font, color, align="center"):
        try:
            paragraph = NSMutableParagraphStyle.alloc().init()
            align_map = {"left": 0, "center": 1, "right": 2}
            paragraph.setAlignment_(align_map.get(align, 1))
            attrs = {
                NSFontAttributeName: font,
                NSForegroundColorAttributeName: color,
                NSParagraphStyleAttributeName: paragraph,
            }
            NSAttributedString.alloc().initWithString_attributes_(str(text), attrs).drawInRect_(rect)
        except Exception:
            pass

    def _draw_image_in_rect(self, image, rect):
        try:
            image.drawInRect_(rect)
            return True
        except Exception:
            pass
        try:
            image.drawInRect_fromRect_operation_fraction_(rect, NSMakeRect(0, 0, 0, 0), NSCompositeSourceOver, 1.0)
            return True
        except Exception:
            return False

    def _tile_preview_image(self, char, size):
        if not self.tile_glyph_preview_enabled:
            return None
        try:
            return self.adapter.draw_glyph_preview_image(self.adapter.get_current_font(), char, int(size))
        except Exception:
            return None

    @staticmethod
    def _tile_item_intersects_dirty_rect(item, dirty_rect):
        """Return whether a tile item overlaps AppKit's requested repaint area.

        A broad component search can yield thousands of result tiles. AppKit asks
        a scroll view to repaint only the visible strip, so skipping items outside
        that strip keeps scrolling proportional to the number of visible tiles.
        """
        try:
            x, y, width, height = item.get("rect", (0, 0, 0, 0))
            dirty_x, dirty_y = float(dirty_rect.origin.x), float(dirty_rect.origin.y)
            dirty_width, dirty_height = float(dirty_rect.size.width), float(dirty_rect.size.height)
            return (
                x < dirty_x + dirty_width
                and x + width > dirty_x
                and y < dirty_y + dirty_height
                and y + height > dirty_y
            )
        except Exception:
            # A conservative fallback avoids accidentally omitting a tile.
            return True

    def draw_related_tile_objects(self, view, dirty_rect):
        """Draw semantic tile objects. Called by RelatedTileObjectView.drawRect_."""
        if not self.related_tile_items:
            return
        try:
            width = self._related_tile_available_width()
            if width and abs(width - self.related_tile_layout_width) > 4:
                height = self._layout_related_tile_items(width)
                view.setFrameSize_(NSMakeSize(width, height))
        except Exception:
            pass

        cfg = self._tile_geometry_config()
        colors = self._tile_status_colors()
        label_color = self._semantic_color("secondaryLabelColor", "labelColor")
        separator_color = self._with_alpha(label_color, 0.35)
        normal_text = NSColor.labelColor()
        base_bg = self._semantic_color("controlBackgroundColor", "windowBackgroundColor")
        window_bg = self._semantic_color("windowBackgroundColor", "controlBackgroundColor")
        selected_bg = self._with_alpha(colors["accent"], 0.14)
        selected_stroke = self._with_alpha(colors["accent"], 0.72)
        current_stroke = self._with_alpha(colors["accent"], 0.55)

        for idx in self._tile_indexes_in_dirty_rect(dirty_rect):
            item = self.related_tile_items[idx]
            if not self._tile_item_intersects_dirty_rect(item, dirty_rect):
                continue
            kind = item.get("kind")
            x, y, w, h = item.get("rect", (0, 0, 0, 0))
            if kind == "label":
                self._draw_text_in_rect(
                    "▸ " + item.get("text", ""),
                    NSMakeRect(x, y + 3, w, h - 3),
                    NSFont.boldSystemFontOfSize_(max(10, cfg["char_size"] - 12)),
                    label_color,
                    align="left",
                )
            elif kind == "separator":
                try:
                    separator_color.setFill()
                    path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(x, y, w, 1), 0.5, 0.5)
                    path.fill()
                except Exception:
                    pass
            elif kind == "tile":
                char = item.get("char", "")
                status_key = item.get("status", "missing")
                marker = item.get("marker", "–")
                is_selected = idx in self.related_tile_selection
                is_current = char == getattr(self, "current_char", None)
                is_favorite = item.get("favorite", False)
                color_label = self._color_label_nscolor(item.get("color")) if self.tile_color_labels_enabled else None
                status_color = colors[STATUS_FAVORITE] if is_favorite else colors.get(status_key, colors[STATUS_MISSING])
                neutral_status_color = self._semantic_color("secondaryLabelColor", "labelColor")
                if self.tile_color_labels_enabled:
                    # Color-label mode: Glyphs labels own the tile color; the status chip
                    # stays uniformly neutral so status differences do not masquerade as
                    # color labels. Status emphasis is applied to the tile panel instead.
                    status_badge_text = colors[STATUS_FAVORITE] if is_favorite else neutral_status_color
                    status_badge_fill = self._with_alpha(window_bg, 0.82)
                    status_badge_stroke = self._with_alpha(neutral_status_color, 0.26)
                    status_badge_line_width = 0.45
                else:
                    status_badge_text = status_color
                    status_badge_fill = self._with_alpha(status_color, 0.12)
                    status_badge_stroke = self._with_alpha(status_color, 0.32)
                    status_badge_line_width = 0.45

                if is_selected:
                    fill = selected_bg
                    stroke = selected_stroke
                    line_width = 2.0
                elif self.tile_color_labels_enabled:
                    if color_label is not None:
                        fill = self._with_alpha(color_label, 0.16)
                        stroke_alpha = 0.72 if status_key in (STATUS_DESIGNED, STATUS_EXISTS) else 0.62
                        stroke = self._with_alpha(color_label, stroke_alpha)
                    else:
                        fill = self._with_alpha(base_bg, 0.72)
                        neutral_alpha = 0.28 if status_key in (STATUS_DESIGNED, STATUS_EXISTS) else 0.18
                        stroke = self._with_alpha(neutral_status_color, neutral_alpha)
                    line_width = 1.6 if status_key == STATUS_DESIGNED else 0.6
                else:
                    if status_key == STATUS_DESIGNED:
                        fill = self._with_alpha(colors[STATUS_DESIGNED], 0.075)
                    elif status_key == STATUS_EXISTS:
                        fill = self._with_alpha(colors[STATUS_EXISTS], 0.065)
                    else:
                        fill = self._with_alpha(base_bg, 0.72)
                    stroke = self._with_alpha(status_color, 0.22)
                    line_width = 0.6
                if is_current and not is_selected:
                    stroke = current_stroke
                    line_width = max(line_width, 1.2)

                rect = NSMakeRect(x, y, w, h)
                self._draw_rounded_rect(rect, fill, stroke, line_width=line_width, radius=cfg["corner"])

                badge_y = y + 5
                badge_rect = NSMakeRect(x + 5, badge_y, cfg["badge_size"] + 8, cfg["badge_size"] + 5)
                self._draw_rounded_rect(
                    badge_rect,
                    status_badge_fill,
                    status_badge_stroke,
                    line_width=status_badge_line_width,
                    radius=cfg["badge_size"] / 2.0,
                )
                self._draw_text_in_rect(
                    marker,
                    NSMakeRect(badge_rect.origin.x, badge_rect.origin.y + 1, badge_rect.size.width, badge_rect.size.height),
                    NSFont.boldSystemFontOfSize_(cfg["badge_size"]),
                    status_badge_text,
                )

                if is_favorite:
                    self._draw_text_in_rect(
                        "★",
                        NSMakeRect(x + w - 22, y + 5, 16, 16),
                        NSFont.boldSystemFontOfSize_(12),
                        colors[STATUS_FAVORITE],
                    )

                char_label_alpha = 1.0
                if is_current:
                    char_color = colors["accent"]
                elif self.tile_color_labels_enabled and status_key == STATUS_MISSING:
                    char_color = self._with_alpha(normal_text, 0.42)
                else:
                    char_color = normal_text
                    char_label_alpha = 0.82

                preview_margin_x = 7
                preview_top = 13
                preview_bottom = 4
                preview_size = min(int(w - preview_margin_x * 2), int(h - preview_top - preview_bottom))
                preview_img = self._tile_preview_image(char, preview_size)
                if preview_img is not None:
                    img_x = x + (w - preview_size) / 2.0
                    img_y = y + preview_top
                    self._draw_image_in_rect(preview_img, NSMakeRect(img_x, img_y, preview_size, preview_size))

                    # Keep the fallback character as a small edge label so it does not
                    # compete with the larger real-glyph preview.
                    label_size = max(9, min(12, cfg["badge_size"] - 1))
                    label_h = label_size + 5
                    self._draw_text_in_rect(
                        char,
                        NSMakeRect(x + 6, y + h - label_h - 3, w - 12, label_h),
                        self.get_font_for_char(char, label_size),
                        self._with_alpha(char_color, char_label_alpha),
                        align="right",
                    )
                else:
                    char_size = cfg["char_size"]
                    char_rect_y = y + max(16, (h - char_size) / 2.0 + 2)
                    self._draw_text_in_rect(
                        char,
                        NSMakeRect(x + 5, char_rect_y, w - 10, char_size + 12),
                        self.get_font_for_char(char, char_size),
                        char_color,
                    )

                try:
                    (color_label or status_color).setFill()
                    NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                        NSMakeRect(x + 8, y + h - 6, w - 16, 2), 1, 1
                    ).fill()
                except Exception:
                    pass

    def open_selected_related_tile_objects(self):
        chars = self._selected_tile_chars()
        if not chars:
            self._refresh_summary_panel(hint=L("summary_no_tile_selection"))
            return
        opened = self.adapter.open_text_in_new_tab(self.adapter.get_current_font(), chars)
        if opened:
            self._refresh_summary_panel(hint=L("summary_opened_new_tab").format(count=len(chars), text=chars))
        else:
            self._refresh_summary_panel(hint=L("summary_open_new_tab_failed"))

    def _find_data_path(self) -> str:
        """尋找既有 CHISE 資料庫路徑。"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "data", "ids.pdata")

    def _load_selected_core(self):
        """保存済み設定に従って IDS 資料源を読み込む。"""
        source = self.ids_source

        if source == "chise":
            self.active_ids_source = "chise"
            return HanziCore(
                self._find_data_path(),
                source_name="CHISE IDS",
            )

        level_map = {
            "yibai_lv0": 0,
            "yibai_lv1": 1,
            "yibai_lv2": 2,
        }
        level = level_map.get(source, 0)

        try:
            from yibai_ids import load as load_yibai_ids, source_label

            database = load_yibai_ids(
                level=level,
                stroke_data_path=self._find_data_path(),
            )
            self.active_ids_source = source
            return HanziCore(
                database=database,
                source_name=source_label(level=level),
            )
        except Exception as exc:
            # 外部資料源不能阻止外掛啟動。Glyphs Macro Panel 可看到原因。
            self.active_ids_source = "chise_fallback"
            print(
                "[Hanzi Component Explorer RS+] Yi Bai IDS lv%d unavailable; "
                "falling back to bundled CHISE IDS: %s" % (level, exc)
            )
            return HanziCore(
                self._find_data_path(),
                source_name="CHISE IDS (bundled fallback)",
            )

    def select_ids_source(self, source):
        """IDS 資料源を切り替え、現在の検索結果を再計算する。"""
        if source not in IDS_SOURCE_OPTIONS:
            return
        if source == self.ids_source and self.active_ids_source != "chise_fallback":
            return

        self.ids_source = source
        self.settings.set("idsSource", source)
        self.core = self._load_selected_core()

        # 現在の入力・選択字を新しい IDS で再評価する。
        try:
            self.perform_search()
        except Exception:
            import traceback
            print(traceback.format_exc())

        label_key = "ids_source_" + source
        if self.active_ids_source == "chise_fallback":
            hint = L("summary_ids_source_fallback").format(source=L(label_key))
        else:
            hint = L("summary_ids_source_changed").format(source=L(label_key))
        self._refresh_summary_panel(hint=hint)

    # === UI utilities ===

    def _copy_to_clipboard(self, text):
        if not text:
            return False
        try:
            pb = NSPasteboard.generalPasteboard()
            pb.clearContents()
            return bool(pb.setString_forType_(text, "public.utf8-plain-text"))
        except Exception:
            return False

    def _selected_related_text(self):
        if self.tile_view_enabled and self._tile_engine_available():
            return self._selected_tile_chars()
        try:
            text_view = self.relatedPane.relatedChars.getNSTextView()
            selected_range = text_view.selectedRange()
            if selected_range.length == 0:
                return ""
            return str(text_view.string().substringWithRange_(selected_range)).strip()
        except Exception:
            return ""

    def _related_characters_only(self, text=None):
        text = self.last_related_text if text is None else text
        return unique_related_chars(text, self.core.is_valid_character)

    def _glyph_badge(self, char):
        if not char:
            return "·"
        return self._glyph_status_payload(char).get("marker", STATUS_MARKERS[STATUS_MISSING])

    def _tile_density_config(self):
        """Return visual density settings for the related-character tile pane."""
        configs = {
            "compact": {"columns": 14, "font_size": 17, "gap": " ", "label": L("density_compact")},
            "comfortable": {"columns": 10, "font_size": 20, "gap": "  ", "label": L("density_comfortable")},
            "spacious": {"columns": 8, "font_size": 24, "gap": "   ", "label": L("density_spacious")},
        }
        return configs.get(self.tile_density, configs["comfortable"])

    def _tile_marker_for_char(self, char):
        """Favorite marker wins; otherwise use glyph design status marker."""
        return self._glyph_badge(char)

    def _selected_tile_count(self):
        try:
            return len(self._selected_tile_chars())
        except Exception:
            return 0

    def _related_status_counts(self, text=None):
        """Count visible result characters by current Glyphs design status."""
        source_text = self.last_related_text if text is None else text
        favorites_key = tuple(self.favorite_chars)
        cache_key = (source_text, favorites_key, id(self.adapter.get_current_font()))
        if cache_key == self._status_counts_cache_key and self._status_counts_cache_value is not None:
            return dict(self._status_counts_cache_value)
        chars = self._related_characters_only(source_text)
        counts = count_statuses(chars, self._raw_glyph_status, self.favorite_chars)
        self._status_counts_cache_key = cache_key
        self._status_counts_cache_value = dict(counts)
        return counts

    def _mode_status_text(self):
        density = self._tile_density_config()["label"]
        tile_mode = L("summary_tile_on") if self.tile_view_enabled else L("summary_tile_off")
        glyph_preview = L("summary_preview_on") if self.tile_glyph_preview_enabled else L("summary_preview_off")
        color_labels = L("summary_color_labels_on") if self.tile_color_labels_enabled else L("summary_color_labels_off")
        status_filter = L("summary_filter_designed_only") if self.show_designed_only else L("summary_filter_all")
        return L("summary_mode_line").format(
            tile=tile_mode,
            density=density,
            glyphPreview=glyph_preview,
            colorLabels=color_labels,
            filter=status_filter,
        )

    def _tile_legend_text(self):
        counts = self._related_status_counts()
        status_line_key = "summary_status_line_color_labels" if self.tile_color_labels_enabled else "summary_status_line"
        return L(status_line_key).format(
            total=counts["total"],
            designed=counts[STATUS_DESIGNED],
            exists=counts[STATUS_EXISTS],
            missing=counts[STATUS_MISSING],
            favorite=counts[STATUS_FAVORITE],
            selected=self._selected_tile_count(),
            progress=designed_percent(counts),
        )

    def _format_result_row(self, item):
        """Format center-list rows while preserving tree connector alignment.

        Older GUI+ builds prefixed preview rows with "char  badge  ...", which made
        branch lines start at different columns. v1.6.2 keeps the tree text first
        and appends the glyph-status marker at the end: "│  └─ 木  ●".
        """
        if isinstance(item, str):
            text = item
            char = self.core.extract_character(text)
        else:
            tree, content = item
            text = f"{tree}{content}"
            char = content if self.core.is_valid_character(content) else self.core.extract_character(text)
        if self.list_preview_enabled and char and self.core.is_valid_character(char):
            return f"{text}  {self._glyph_badge(char)}"
        return text

    def _result_row_to_source_text(self, row):
        """Remove UI-only list badges before character extraction/selection logic."""
        if self.list_preview_enabled and isinstance(row, str):
            marker_values = set(STATUS_MARKERS.values())
            parts = row.rsplit("  ", 1)
            if len(parts) == 2 and parts[1] in marker_values:
                return parts[0]
            # Backward compatibility for rows copied from older GUI+ versions.
            old_parts = row.split("  ", 2)
            if len(old_parts) == 3 and old_parts[1] in marker_values:
                return old_parts[2]
        return row

    def _tile_lines_from_display_text(self, text, columns=None):
        """Convert related display text into status-badged tile-grid lines while preserving group labels."""
        if not self.tile_view_enabled:
            return text
        config = self._tile_density_config()
        columns = columns or config["columns"]
        gap = config["gap"]
        output = []
        for raw_line in (text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if set(line) == {"-"}:
                output.append("────")
                continue
            if " " in line:
                label, payload = line.split(" ", 1)
                output.append(f"▸ {label}")
            else:
                payload = line
            chars = [ch for ch in payload if not ch.isspace()]
            tokens = [f"{self._tile_marker_for_char(ch)}{ch}" for ch in chars]
            for i in range(0, len(tokens), columns):
                output.append(gap.join(tokens[i:i + columns]))
        return "\n".join(output)

    def _refresh_summary_panel(self, focus_char=None, result_count=None, hint=None):
        char = focus_char or getattr(self, "current_char", None)
        if result_count is None:
            result_count = self.last_result_count
        if hint is None:
            hint = L("summary_hint_color_labels") if self.tile_color_labels_enabled else L("summary_hint")
        if char:
            strokes = self.core.get_stroke_count(char)
            strokes_text = str(strokes) if strokes is not None else "—"
            payload = self._glyph_status_payload(char)
            meta = L("summary_focus_meta").format(
                unicode=f"U+{ord(char):04X}",
                strokes=strokes_text,
                marker=payload.get("marker", "–"),
                status=L(f"status_{payload.get('status', STATUS_MISSING)}"),
            )
            char_text = char
        else:
            meta = L("summary_no_focus_meta").format(
                noFocus=L("summary_no_focus"),
                tileMode=L("summary_tile_mode"),
                tileState=L("summary_tile_on") if self.tile_view_enabled else L("summary_tile_off"),
            )
            char_text = "—"
        try:
            self.w.summaryChar.set(self.create_attributed_string(char_text, 42))
        except Exception:
            self.w.summaryChar.set(char_text)

        charset_count = len(self.currentCharset) if self.currentCharset else 0
        counts = self._related_status_counts()
        stats = L("summary_stats_line").format(
            charset=charset_count,
            favorites=len(self.favorite_chars),
            related=result_count,
            designed=counts[STATUS_DESIGNED],
            exists=counts[STATUS_EXISTS],
            missing=counts[STATUS_MISSING],
            progress=designed_percent(counts),
        )
        try:
            self.w.summaryMeta.set(meta)
            self.w.summaryStats.set(stats)
            if hasattr(self.w, "summaryMode"):
                self.w.summaryMode.set(self._mode_status_text())
            self.w.summaryHint.set(hint)
            if hasattr(self.w, "summaryLegend"):
                self.w.summaryLegend.set(self._tile_legend_text())
        except Exception:
            pass
        self._refresh_favorite_button()
        self._refresh_tile_button()
        self._refresh_density_button()

    def _refresh_result_action_buttons(self):
        chars = self._related_characters_only()
        selected_chars = self._selected_tile_chars() if self.tile_view_enabled and self._tile_engine_available() else ""
        try:
            self.w.insertButton.enable(bool(selected_chars))
        except Exception:
            pass
        try:
            self.w.searchSelectedButton.enable(bool(selected_chars))
        except Exception:
            pass
        for name in ("copyRelatedButton", "insertAllButton"):
            try:
                getattr(self.w, name).enable(bool(chars) or bool(selected_chars))
            except Exception:
                pass
        self._refresh_favorite_button()

    # === GUI+ actions / menus ===

    def _add_recent_query(self, query):
        query = (query or "").strip()
        if not query:
            return
        self.recent_queries = [q for q in self.recent_queries if q != query]
        self.recent_queries.insert(0, query)
        self.recent_queries = self.recent_queries[:12]
        self.settings.set("recentQueries", self.recent_queries)

    def show_history_menu(self, sender):
        from AppKit import NSMenu, NSMenuItem
        menu = NSMenu.alloc().init()
        if not self.recent_queries:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_history_empty"), None, "")
            item.setEnabled_(False)
            menu.addItem_(item)
        else:
            for query in self.recent_queries:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(query, "selectRecentSearch:", "")
                item.setTarget_(self.filterMenuHandler)
                item.setRepresentedObject_(query)
                menu.addItem_(item)
            menu.addItem_(NSMenuItem.separatorItem())
            clear_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_history_clear"), "clearHistory:", "")
            clear_item.setTarget_(self.filterMenuHandler)
            menu.addItem_(clear_item)
        button = sender.getNSButton()
        menu.popUpMenuPositioningItem_atLocation_inView_(None, (0, button.bounds().size.height), button)

    def run_recent_search(self, query):
        self.w.inputText.set(query)
        self.is_manual_mode = True
        self.perform_search()

    def clear_recent_queries(self):
        self.recent_queries = []
        self.settings.set("recentQueries", self.recent_queries)
        self._refresh_summary_panel(hint=L("summary_history_cleared"))

    def _active_or_selected_char(self):
        try:
            selected = self._selected_related_text()
            char = self.core.extract_character(selected) if selected else None
            if char and self.core.is_valid_character(char):
                return char
        except Exception:
            pass
        if self.current_char:
            return self.current_char
        return None

    def _save_favorites(self):
        self.favorite_chars = self.favorite_chars[:64]
        self.settings.set("favoriteChars", self.favorite_chars)

    def _set_button_symbol(self, button, symbol_name):
        try:
            image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol_name, None)
            if image:
                button.getNSButton().setImage_(image)
        except Exception:
            pass

    def _refresh_favorite_button(self):
        if not hasattr(self.w, "favoritesButton"):
            return
        char = self._active_or_selected_char()
        is_fav = bool(char and char in self.favorite_chars)
        self._set_button_symbol(self.w.favoritesButton, "star.fill" if is_fav else "star")
        try:
            if char:
                key = "tooltip_favorite_on" if is_fav else "tooltip_favorite_off"
                self.w.favoritesButton.getNSButton().setToolTip_(L(key).format(char=char))
            else:
                self.w.favoritesButton.getNSButton().setToolTip_(L("btn_favorites_tooltip"))
        except Exception:
            pass

    def _refresh_tile_button(self):
        if not hasattr(self.w, "tileButton"):
            return
        self._set_button_symbol(self.w.tileButton, "square.grid.3x3.fill" if self.tile_view_enabled else "square.grid.3x3")
        try:
            self.w.tileButton.getNSButton().setToolTip_(L("btn_tile_view_tooltip"))
        except Exception:
            pass

    def _refresh_density_button(self):
        if not hasattr(self.w, "tileDensityButton"):
            return
        symbols = {
            "compact": "textformat.size.smaller",
            "comfortable": "textformat.size",
            "spacious": "textformat.size.larger",
        }
        self._set_button_symbol(self.w.tileDensityButton, symbols.get(self.tile_density, "textformat.size"))
        try:
            self.w.tileDensityButton.getNSButton().setToolTip_(
                L("btn_tile_density_tooltip_state").format(density=self._tile_density_config()["label"])
            )
        except Exception:
            pass

    def show_favorites_menu(self, sender):
        from AppKit import NSMenu, NSMenuItem
        menu = NSMenu.alloc().init()
        active_char = self._active_or_selected_char()
        if active_char:
            key = "menu_favorite_remove" if active_char in self.favorite_chars else "menu_favorite_add"
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L(key).format(char=active_char), "toggleCurrentFavorite:", "")
            item.setTarget_(self.filterMenuHandler)
            menu.addItem_(item)
            menu.addItem_(NSMenuItem.separatorItem())
        title = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_favorites"), None, "")
        title.setEnabled_(False)
        menu.addItem_(title)
        if not self.favorite_chars:
            empty = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_favorites_empty"), None, "")
            empty.setEnabled_(False)
            menu.addItem_(empty)
        else:
            for char in self.favorite_chars[:20]:
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"★ {char}  U+{ord(char):04X}", "selectFavorite:", "")
                item.setTarget_(self.filterMenuHandler)
                item.setRepresentedObject_(char)
                menu.addItem_(item)
            menu.addItem_(NSMenuItem.separatorItem())
            clear = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(L("menu_favorites_clear"), "clearFavorites:", "")
            clear.setTarget_(self.filterMenuHandler)
            menu.addItem_(clear)
        button = sender.getNSButton()
        menu.popUpMenuPositioningItem_atLocation_inView_(None, (0, button.bounds().size.height), button)

    def toggle_current_favorite(self):
        char = self._active_or_selected_char()
        if not char:
            return
        if char in self.favorite_chars:
            self.favorite_chars = [c for c in self.favorite_chars if c != char]
            hint = L("summary_favorite_removed").format(char=char)
        else:
            self.favorite_chars = [c for c in self.favorite_chars if c != char]
            self.favorite_chars.insert(0, char)
            hint = L("summary_favorite_added").format(char=char)
        self._save_favorites()
        self._refresh_related_view()
        self._refresh_summary_panel(hint=hint)

    def run_favorite_search(self, char):
        self.w.inputText.set(char)
        self.is_manual_mode = True
        self.perform_search()

    def clear_favorites(self):
        self.favorite_chars = []
        self._save_favorites()
        self._invalidate_status_cache()
        self._refresh_related_view()
        self._refresh_summary_panel(hint=L("summary_favorites_cleared"))

    def _extract_chars_for_new_tab(self, text):
        """タイル/通常表示の選択文字列から、Glyphs に送る漢字だけを順序維持で抽出。

        タイル表示では見た目上 `●字` / `○字` / `★字` などの2文字トークンになるため、
        ステータス記号や `▸` ラベル、罫線を除去して実文字だけを取り出す。
        """
        if not text:
            return ""

        marker_chars = set("★●○–-")
        result = []
        seen_positions = set()
        raw_text = str(text)

        # Tile mode: marker + valid character tokens are the safest signal.
        for i, ch in enumerate(raw_text[:-1]):
            nxt = raw_text[i + 1]
            if ch in marker_chars:
                try:
                    if self.core.is_valid_character(nxt):
                        result.append(nxt)
                        seen_positions.add(i + 1)
                except Exception:
                    pass

        # Fallback / non-tile mode: parse line-by-line and skip visual labels.
        if not result:
            for raw_line in raw_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith("▸") or line.startswith("────") or set(line) == {"-"}:
                    continue
                # In non-tile grouped lines, the first token is a component label: "木 林森".
                payload = line.split(" ", 1)[1] if " " in line else line
                for ch in payload:
                    try:
                        if self.core.is_valid_character(ch):
                            result.append(ch)
                    except Exception:
                        pass

        # De-duplicate while preserving order. Related panes should not need repeated glyphs.
        unique = []
        seen = set()
        for ch in result:
            if ch not in seen:
                unique.append(ch)
                seen.add(ch)
        return "".join(unique)

    def _character_at_related_text_click(self, gesture):
        """ダブルクリック位置から近傍の有効文字を1字拾うフォールバック。"""
        try:
            text_view = self.relatedPane.relatedChars.getNSTextView()
            point = gesture.locationInView_(text_view)
            if hasattr(text_view, "characterIndexForInsertionAtPoint_"):
                index = text_view.characterIndexForInsertionAtPoint_(point)
            else:
                return ""
            text = str(text_view.string())
            # The click may land on a status marker. Check the clicked index and neighbors.
            for candidate_index in (index, index + 1, index - 1, index + 2, index - 2):
                if 0 <= candidate_index < len(text):
                    ch = text[candidate_index]
                    if self.core.is_valid_character(ch):
                        return ch
        except Exception:
            pass
        return ""

    def open_selected_related_glyphs_in_new_tab(self, gesture=None):
        """右ペインで選択されたタイル/文字を Glyphs の新規タブで開く。"""
        if self.tile_view_enabled and self._tile_engine_available():
            chars = self._selected_tile_chars()
            if chars:
                return self.open_selected_related_tile_objects()
        selected_text = self._selected_related_text()
        chars = self._extract_chars_for_new_tab(selected_text)

        # NSTextView may collapse a multi-character drag selection to the clicked tile
        # just before the double-click recognizer fires. Keep a very recent multi
        # selection as the intended target in that case.
        try:
            if (
                len(chars) <= 1
                and len(self.last_related_multi_selection_chars) > 1
                and time.time() - self.last_related_multi_selection_time < 4.0
            ):
                chars = self.last_related_multi_selection_chars
        except Exception:
            pass

        if not chars and gesture is not None:
            chars = self._character_at_related_text_click(gesture)
        if not chars:
            self._refresh_summary_panel(hint=L("summary_no_tile_selection"))
            return

        font = self.adapter.get_current_font()
        opened = self.adapter.open_text_in_new_tab(font, chars)
        if opened:
            self._refresh_summary_panel(
                hint=L("summary_opened_new_tab").format(count=len(chars), text=chars)
            )
        else:
            self._refresh_summary_panel(hint=L("summary_open_new_tab_failed"))

    def clear_search(self, sender):
        self.w.inputText.set("")
        self.is_manual_mode = False
        self._exit_multi_component_mode()
        self.on_glyph_changed()
        self._refresh_summary_panel(hint=L("summary_auto_mode"))

    def copy_related_text(self, sender):
        text = self._selected_related_text() or self.last_related_text
        if self._copy_to_clipboard(text):
            self._refresh_summary_panel(hint=L("summary_copied"))

    def copy_related_chars_only(self, sender):
        chars = self._related_characters_only()
        if self._copy_to_clipboard(chars):
            self._refresh_summary_panel(hint=L("summary_chars_copied").format(count=len(chars)))

    def insert_all_related(self, sender):
        chars = self._related_characters_only()
        if not chars:
            return
        self.adapter.insert_to_tab(self.adapter.get_current_font(), chars)
        self._refresh_summary_panel(hint=L("summary_inserted_all").format(count=len(chars)))

    def search_selected_text(self, sender):
        text = self._selected_related_text()
        if not text:
            return
        char = self.core.extract_character(text)
        query = char if char and self.core.is_valid_character(char) else text
        self.w.inputText.set(query)
        self.is_manual_mode = True
        self.perform_search()

    def toggle_designed_only(self, sender):
        self.show_designed_only = not self.show_designed_only
        self.settings.set("showDesignedOnly", self.show_designed_only)
        self._refresh_related_view()
        self._refresh_summary_panel(
            hint=L("summary_designed_only_enabled") if self.show_designed_only else L("summary_designed_only_disabled")
        )

    def insert_selected_related_tiles(self, sender):
        chars = self._selected_tile_chars()
        if chars:
            self.adapter.insert_to_tab(self.adapter.get_current_font(), chars)
            self._refresh_summary_panel(hint=L("summary_inserted_selected_tiles").format(count=len(chars), text=chars))

    def copy_selected_related_tiles(self, sender):
        chars = self._selected_tile_chars()
        if chars and self._copy_to_clipboard(chars):
            self._refresh_summary_panel(hint=L("summary_copied_selected_tiles").format(count=len(chars), text=chars))

    def copy_selected_tile_unicode(self, sender):
        chars = self._selected_tile_chars()
        if not chars:
            return
        values = " ".join(f"U+{ord(ch):04X}" for ch in chars)
        if self._copy_to_clipboard(values):
            self._refresh_summary_panel(hint=L("summary_copied_unicode").format(text=values))

    def search_selected_tile(self, sender):
        chars = self._selected_tile_chars()
        if not chars:
            return
        self.w.inputText.set(chars[0])
        self.is_manual_mode = True
        self.perform_search()

    def add_selected_tiles_to_favorites(self, sender):
        chars = self._selected_tile_chars()
        if not chars:
            return
        for ch in reversed(chars):
            self.favorite_chars = [c for c in self.favorite_chars if c != ch]
            self.favorite_chars.insert(0, ch)
        self._save_favorites()
        self._invalidate_status_cache()
        self._refresh_related_view()
        self._refresh_summary_panel(hint=L("summary_added_selected_favorites").format(count=len(chars)))

    def remove_selected_tiles_from_favorites(self, sender):
        chars = set(self._selected_tile_chars())
        if not chars:
            return
        self.favorite_chars = [c for c in self.favorite_chars if c not in chars]
        self._save_favorites()
        self._invalidate_status_cache()
        self._refresh_related_view()
        self._refresh_summary_panel(hint=L("summary_removed_selected_favorites").format(count=len(chars)))

    def toggle_tile_view(self, sender):
        self.tile_view_enabled = not self.tile_view_enabled
        self.settings.set("tileViewEnabled", self.tile_view_enabled)
        self._refresh_related_view()
        self._refresh_summary_panel(hint=L("summary_tile_enabled") if self.tile_view_enabled else L("summary_tile_disabled"))

    def cycle_tile_density(self, sender):
        order = ["compact", "comfortable", "spacious"]
        try:
            next_index = (order.index(self.tile_density) + 1) % len(order)
        except ValueError:
            next_index = 1
        self.tile_density = order[next_index]
        self.settings.set("tileDensity", self.tile_density)
        self._refresh_related_view()
        self._refresh_summary_panel(
            hint=L("summary_tile_density_changed").format(density=self._tile_density_config()["label"])
        )

    def toggle_tile_glyph_preview(self, sender):
        self.tile_glyph_preview_enabled = not self.tile_glyph_preview_enabled
        self.settings.set("tileGlyphPreviewEnabled", self.tile_glyph_preview_enabled)
        self._invalidate_status_cache()
        self._refresh_related_view()
        self._refresh_summary_panel(
            hint=L("summary_tile_glyph_preview_enabled") if self.tile_glyph_preview_enabled else L("summary_tile_glyph_preview_disabled")
        )

    def toggle_tile_color_labels(self, sender):
        self.tile_color_labels_enabled = not self.tile_color_labels_enabled
        self.settings.set("tileColorLabelsEnabled", self.tile_color_labels_enabled)
        self._invalidate_status_cache()
        self._refresh_related_view()
        self._refresh_summary_panel(
            hint=L("summary_tile_color_labels_enabled") if self.tile_color_labels_enabled else L("summary_tile_color_labels_disabled")
        )

    def toggle_list_preview(self, sender):
        self.list_preview_enabled = not self.list_preview_enabled
        self.settings.set("listPreviewEnabled", self.list_preview_enabled)
        self._refresh_result_list_rows()
        self._refresh_summary_panel(hint=L("summary_list_preview_enabled") if self.list_preview_enabled else L("summary_list_preview_disabled"))

    def _refresh_related_view(self):
        if self.multi_component_mode and self.multi_component_parts:
            self._render_intersection(self.multi_component_parts)
        else:
            self.update_related_display()

    def _refresh_result_list_rows(self):
        if self.multi_component_mode and self.multi_component_parts:
            original = "".join(self.multi_component_parts)
            self.display_results = [self._format_result_row(original)] + [self._format_result_row(p) for p in self.multi_component_parts]
        elif self.all_results:
            self.display_results = [self._format_result_row(item) for item in self.all_results]
        self.treePane.resultList.set(self.display_results)
        self._adjust_result_list_column_width()

    # === 統一篩選選單 ===

    def show_filter_menu(self, sender):
        """顯示統一篩選選單"""
        from AppKit import NSMenu, NSMenuItem, NSOnState, NSOffState

        menu = NSMenu.alloc().init()

        actions_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_result_actions"), None, ""
        )
        actions_item.setEnabled_(False)
        menu.addItem_(actions_item)

        copy_chars_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_copy_chars_only"), "copyRelatedCharsOnly:", ""
        )
        copy_chars_item.setTarget_(self.filterMenuHandler)
        copy_chars_item.setEnabled_(bool(self._related_characters_only()))
        menu.addItem_(copy_chars_item)

        insert_all_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_insert_all_related"), "insertAllRelated:", ""
        )
        insert_all_item.setTarget_(self.filterMenuHandler)
        insert_all_item.setEnabled_(bool(self._related_characters_only()))
        menu.addItem_(insert_all_item)

        tile_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_tile_view"), "toggleTileView:", ""
        )
        tile_item.setTarget_(self.filterMenuHandler)
        tile_item.setState_(NSOnState if self.tile_view_enabled else NSOffState)
        menu.addItem_(tile_item)

        density_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_tile_density").format(density=self._tile_density_config()["label"]), "cycleTileDensity:", ""
        )
        density_item.setTarget_(self.filterMenuHandler)
        menu.addItem_(density_item)

        tile_preview_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_tile_glyph_preview"), "toggleTileGlyphPreview:", ""
        )
        tile_preview_item.setTarget_(self.filterMenuHandler)
        tile_preview_item.setState_(NSOnState if self.tile_glyph_preview_enabled else NSOffState)
        menu.addItem_(tile_preview_item)

        tile_color_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_tile_color_labels"), "toggleTileColorLabels:", ""
        )
        tile_color_item.setTarget_(self.filterMenuHandler)
        tile_color_item.setState_(NSOnState if self.tile_color_labels_enabled else NSOffState)
        menu.addItem_(tile_color_item)

        preview_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_list_preview"), "toggleListPreview:", ""
        )
        preview_item.setTarget_(self.filterMenuHandler)
        preview_item.setState_(NSOnState if self.list_preview_enabled else NSOffState)
        menu.addItem_(preview_item)

        designed_only_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_designed_only_filter"), "toggleDesignedOnly:", ""
        )
        designed_only_item.setTarget_(self.filterMenuHandler)
        designed_only_item.setState_(NSOnState if self.show_designed_only else NSOffState)
        menu.addItem_(designed_only_item)

        # IDS 資料源
        ids_root_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("menu_ids_source"), None, ""
        )
        ids_submenu = NSMenu.alloc().initWithTitle_(L("menu_ids_source"))
        ids_entries = (
            ("yibai_lv0", "ids_source_yibai_lv0"),
            ("yibai_lv1", "ids_source_yibai_lv1"),
            ("yibai_lv2", "ids_source_yibai_lv2"),
            ("chise", "ids_source_chise"),
        )
        for source, label_key in ids_entries:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                L(label_key), "selectIDSSource:", ""
            )
            item.setTarget_(self.filterMenuHandler)
            item.setRepresentedObject_(source)
            item.setState_(NSOnState if self.ids_source == source else NSOffState)
            ids_submenu.addItem_(item)
        ids_root_item.setSubmenu_(ids_submenu)
        menu.addItem_(ids_root_item)

        menu.addItem_(NSMenuItem.separatorItem())

        # 顏色篩選項目
        color_count = len(self.filter_colors)
        if color_count > 0:
            color_title = L("menu_color_filter_count").format(count=color_count)
        else:
            color_title = L("menu_color_filter")
        color_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            color_title, "openColorSelector:", ""
        )
        color_item.setTarget_(self.filterMenuHandler)
        menu.addItem_(color_item)

        # 分隔線
        menu.addItem_(NSMenuItem.separatorItem())

        # 字型檔項目
        font_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            L("charset_font"), "selectFontCharset:", ""
        )
        font_item.setTarget_(self.filterMenuHandler)
        font_item.setState_(NSOnState if not self.use_custom_charset else NSOffState)
        menu.addItem_(font_item)

        # 自訂字集項目
        if self.use_custom_charset and self.custom_charset_path:
            custom_title = os.path.basename(self.custom_charset_path)
        else:
            custom_title = L("charset_custom")
        custom_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            custom_title, "selectCustomCharset:", ""
        )
        custom_item.setTarget_(self.filterMenuHandler)
        custom_item.setState_(NSOnState if self.use_custom_charset else NSOffState)
        menu.addItem_(custom_item)

        # 在按鈕下方顯示選單
        button = sender.getNSButton()
        menu.popUpMenuPositioningItem_atLocation_inView_(
            None, (0, button.bounds().size.height), button
        )

    # === 字集管理 ===

    def selectFontCharset(self):
        """切換到字型檔字集"""
        self.use_custom_charset = False
        self.settings.remove("customCharsetPath")  # 清除儲存的自訂字集路徑
        self.loadFontCharset()
        # 更新相關顯示
        self.update_related_display()

    def selectCustomCharset(self):
        """選擇自訂字集檔案"""
        panel = NSOpenPanel.openPanel()
        panel.setAllowedFileTypes_(["txt", "hex"])

        if panel.runModal() == 1:
            path = panel.URLs()[0].path()
            self.custom_charset_path = path
            self.custom_charset_name = os.path.basename(path)
            self.use_custom_charset = True

            # 載入字集
            self.loadCustomCharset(path)

            # 保存設定
            self.settings.set("customCharsetPath", path)

            # 更新相關顯示
            self.update_related_display()

    def loadCustomCharset(self, path):
        """載入自訂字集檔案"""
        self.currentCharset.clear()

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    code = line.split("#")[0].strip()
                    if code:
                        try:
                            if code.startswith("uni"):
                                code = code[3:]
                            self.currentCharset.add(chr(int(code, 16)))
                        except ValueError:
                            continue

            # 更新搜尋結果
            self.search_callback(None)

        except Exception:
            import traceback

            print(traceback.format_exc())
            # 載入失敗，切回字型檔
            self.use_custom_charset = False
            self.custom_charset_path = None
            self.custom_charset_name = None
            self.loadFontCharset()

    def loadFontCharset(self, trigger_search=True):
        """
        載入字型檔字符作為字集

        參數:
            trigger_search: 是否觸發搜尋更新（預設 True）
        """
        self.currentCharset.clear()

        # 取得目前字型的字符（透過 adapter）
        font = self.adapter.get_current_font()
        font_chars = self.adapter.get_font_characters(font)

        if font_chars:
            self.currentCharset.update(font_chars)

        # 更新搜尋結果（初始化時跳過，避免重複搜尋）
        if trigger_search:
            self.search_callback(None)

    def _adjust_result_list_column_width(self):
        """根據內容動態調整結果列表欄位寬度"""
        tableView = self.treePane.resultList.getNSTableView()
        if not self.display_results:
            return

        font = tableView.tableColumns()[0].dataCell().font()
        max_width = 250

        for item in self.display_results:
            attr_str = NSAttributedString.alloc().initWithString_attributes_(
                item, {NSFontAttributeName: font}
            )
            text_width = attr_str.size().width + 20
            if text_width > max_width:
                max_width = text_width

        for column in tableView.tableColumns():
            column.setWidth_(max_width)

    # === 自動抓取功能 ===

    def find_valid_unicode_for_char(self, glyph):
        """
        智能選擇資料庫中存在的 Unicode 值（多 Unicode 支援）

        參數:
        glyph: Glyphs glyph 物件

        回傳:
        str: 資料庫中存在的字符，如果都不存在則返回 None

        說明:
        1. 優先檢查 glyph.unicodes / glyph.unicode
        2. 如果沒有 Unicode 值，嘗試從 glyph name 解析（如 uni4FE1.001 → 4FE1）
        3. 返回第一個在資料庫中存在的字符
        """
        # 收集所有可能的 Unicode 值
        unicode_candidates = []

        # 優先使用 glyph.unicodes（如果存在）
        if hasattr(glyph, "unicodes") and glyph.unicodes:
            unicode_candidates = list(glyph.unicodes)
        elif glyph.unicode:
            # 降級到單值
            unicode_candidates = [glyph.unicode]
        else:
            # 沒有 Unicode 值，嘗試從 glyph name 提取
            # 格式：
            # - uni4FE1, uni4FE1.001 (4 位)
            # - uniF0000 (5 位，Private Use Area)
            # - u10000, u10000.001 (5 位，Supplementary Plane)
            if glyph.name:
                base_unicode = None

                if glyph.name.startswith("uni"):
                    # 格式：uni + 4-5 位十六進位
                    name_without_prefix = glyph.name[3:]  # 移除 'uni'
                    base_unicode = name_without_prefix.split(".")[0]  # 移除 .001 等後綴
                elif glyph.name.startswith("u") and not glyph.name.startswith("uni"):
                    # 格式：u + 5-6 位十六進位（用於 U+10000 以上）
                    name_without_prefix = glyph.name[1:]  # 移除 'u'
                    base_unicode = name_without_prefix.split(".")[0]  # 移除 .001 等後綴

                # 驗證格式（4-6 位十六進位）
                if (
                    base_unicode
                    and len(base_unicode) in [4, 5, 6]
                    and all(c in "0123456789ABCDEFabcdef" for c in base_unicode)
                ):
                    unicode_candidates = [base_unicode.upper()]

        # 遍歷所有候選值，找到第一個在資料庫中存在的
        for unicode_val in unicode_candidates:
            try:
                char = chr(int(unicode_val, 16))
                # 檢查資料庫中是否存在
                if self.core.get_data(char):
                    return char
            except (ValueError, OverflowError):
                continue

        return None

    def get_current_glyph(self):
        """
        取得目前正在編輯的字符（透過 adapter）

        回傳:
        str: 目前編輯的字符，如果沒有則返回空字符串
        """
        font = self.adapter.get_current_font()
        return self.adapter.get_selected_character(font) or ""

    def on_glyph_changed(self, notification=None):
        """
        當前字符變化時的回調函式（透過 UPDATEINTERFACE 通知觸發）

        自動模式行為：
        1. 清空搜尋框（不填入字符）
        2. 使用多 Unicode 智能偵測找到資料庫中存在的字符
        3. 設定 current_char 並觸發搜尋

        注意：手動模式時此方法會提前返回（Issue #31：視窗聚焦模式）

        參數:
        notification: 通知物件（可選）
        """
        try:
            if not self.auto_fetch_enabled:
                return

            # 手動模式時不自動跟隨（Issue #31：視窗聚焦模式）
            if self.is_manual_mode:
                return

            # 檢查 IME 輸入狀態，跳過未確認的注音/拼音輸入
            if self.adapter.is_ime_input_active():
                return

            # 取得當前字型
            font = self.adapter.get_current_font()
            if not font or not font.selectedLayers:
                return

            # 取得當前 glyph
            layer = font.selectedLayers[0]
            if not layer or not layer.parent:
                return

            glyph = layer.parent
            current_glyph_name = glyph.name  # 使用 glyph name 作為識別

            # 只在字符改變時執行（避免過度觸發）
            if current_glyph_name == self.last_glyph_name:
                return

            self.last_glyph_name = current_glyph_name

            # 多 Unicode 智能選擇：找到資料庫中存在的字符
            valid_char = self.find_valid_unicode_for_char(glyph)

            if valid_char:
                # 清空搜尋框
                self.w.inputText.set("")

                # 設定當前字符並觸發搜尋
                self.current_char = valid_char
                self.perform_search()

        except:
            import traceback

            print(traceback.format_exc())

    def toggle_auto_fetch(self, sender):
        """
        切換自動抓取功能

        參數:
        sender: 勾選框元件
        """
        self.auto_fetch_enabled = sender.get()

        # 如果開啟自動抓取，立即執行一次
        if self.auto_fetch_enabled:
            current_glyph = self.get_current_glyph()
            if current_glyph:
                self.w.inputText.set(current_glyph)
                self.perform_search()

    # === 搜尋功能 ===

    def search_callback(self, sender):
        """
        搜尋框輸入回調

        當用戶在搜尋框輸入時：
        1. 進入手動模式
        2. 只有輸入完整有效格式時才執行搜尋
        """
        # 用戶開始輸入 → 進入手動模式
        input_text = self.w.inputText.get().strip()
        if input_text:
            self.is_manual_mode = True

        # 只有完整有效的輸入才執行搜尋，否則保持原顯示
        if not is_complete_search_input(input_text):
            return

        self.perform_search()

    def perform_search(self):
        """
        執行搜尋

        自動模式：使用 self.current_char（已由 on_glyph_changed 設定）
        手動模式：使用搜尋框內容
        """
        input_text = self.w.inputText.get().strip()

        # 自動模式：搜尋框為空，使用 current_char
        if not input_text:
            if self.current_char:
                # 自動模式：使用已設定的 current_char
                input_text = self.current_char
            else:
                return  # 無輸入，保持原顯示
        else:
            # 手動模式：使用搜尋框內容
            self.current_char = None  # 清除自動模式的字符

            # 多部件 AND 搜尋：輸入多個漢字時，進入多部件模式（中欄列部件、右欄列交集）
            # 原本只取第一字（Issue #31），改為 AND 組合；無條件觸發，不受衍生字開關限制
            parts = [c for c in input_text if not c.isspace()]
            if len(parts) > 1 and all(ord(c) > 127 for c in parts):
                self._enter_multi_component_mode(parts)
                return

        # 非多部件輸入：若先前在多部件模式，退出以恢復衍生字開關狀態
        self._exit_multi_component_mode()
        if self.is_manual_mode:
            self._add_recent_query(input_text)

        # 處理 Unicode 格式
        if input_text.startswith(("uni", "UNI")) and len(input_text) == 7:
            input_text = "U+" + input_text[3:].upper()
        elif (
            input_text.startswith(("u", "U"))
            and len(input_text) == 6
            and not input_text.startswith(("U+", "u+"))
        ):
            input_text = "U+" + input_text[1:].upper()

        # Unicode 查詢
        if input_text.startswith(("U+", "u+")) or re.match(
            r"^[0-9A-Fa-f]{4,5}$", input_text
        ):
            if not input_text.upper().startswith("U+"):
                input_text = "U+" + input_text.upper()
            else:
                input_text = input_text.upper()

            char_data = self.core.get_data(input_text)
            if char_data:
                # 取得查詢到的字符
                found_char = list(char_data.keys())[0]
                # 根據深淺層狀態調整拆解深度
                depth = 10 if self.deep_analysis else 1
                self.all_results = self.core.decompose(found_char, max_depth=depth)
            else:
                return  # 找不到結果，保持原顯示
        else:
            # 字符查詢（優先嘗試拆解輸入的字本身）
            char_data = self.core.get_data(input_text)

            if char_data:
                # 找到字符，拆解它本身
                found_char = list(char_data.keys())[0]
                depth = 10 if self.deep_analysis else 1
                self.all_results = self.core.decompose(found_char, max_depth=depth)
            else:
                # 找不到字符，改為部件搜尋（顯示「顯示衍生字」時才執行）
                if self.show_derived:
                    charset = self.currentCharset if self.currentCharset else None
                    related_chars = self.core.search(input_text, charset)

                    if related_chars:
                        self.all_results = []
                        depth = 10 if self.deep_analysis else 1
                        for char in related_chars[:5]:  # 限制結果數量避免過慢
                            self.all_results.extend(
                                self.core.decompose(char, max_depth=depth)
                            )
                    else:
                        return  # 找不到結果，保持原顯示
                else:
                    return  # 找不到結果，保持原顯示

        self._render_results()

    def _render_results(self):
        """將 self.all_results 渲染到中欄列表，並以第一個有效字更新左/右欄。

        供單字、Unicode、多部件 AND 三條搜尋路徑共用。
        """
        # 生成顯示結果並同時存儲
        self.display_results = [self._format_result_row(item) for item in self.all_results]
        self.treePane.resultList.set(self.display_results)
        self._adjust_result_list_column_width()
        self.last_result_count = len(self.display_results)

        # 提取第一個有效字符，連動更新左欄（預覽+詳資）與右欄（同字根）
        if self.all_results:
            first_char = self._extract_valid_character_from_results(self.all_results)
            if first_char:
                self.update_char_info(first_char)

    # === 多部件 AND 搜尋模式 ===

    def _enter_multi_component_mode(self, parts):
        """進入多部件 AND 模式：中欄列輸入部件、右欄列交集、鎖定衍生字開關。

        中欄第一行為原始輸入（AND 交集錨點），其後一行一個部件；
        點選第一行回到交集、點選部件看該部件衍生字（見 selection_callback）。

        parts: 輸入部件清單，保留原始輸入（已過濾空白，如 ['氵', '木']）
        """
        # 鎖定衍生字與深度拆解開關：多部件搜尋本質為衍生字邏輯的 AND 版本，
        # 且交集以「遞迴展開到葉部件」為基礎，深度拆解恆為開啟
        if not self.multi_component_mode:
            self.saved_show_derived = self.show_derived
            self.saved_deep_analysis = self.deep_analysis
        self.multi_component_mode = True
        self.multi_component_parts = parts
        self.show_derived = True
        self.w.showDerivedCheckbox.set(True)
        self.w.showDerivedCheckbox.enable(False)
        self.deep_analysis = True
        self.w.deepAnalysisCheckbox.set(True)
        self.w.deepAnalysisCheckbox.enable(False)

        # 中欄：第一行原始輸入（交集錨點），其後一行一個部件
        original = "".join(parts)
        self._add_recent_query(original)
        self.display_results = [self._format_result_row(original)] + [self._format_result_row(p) for p in parts]
        self.treePane.resultList.set(self.display_results)
        self._adjust_result_list_column_width()
        self.last_result_count = len(self.display_results)

        # 右欄：AND 交集；左欄：清空，待點選中欄某字才填
        self._render_intersection(parts)
        self._clear_left_panel()

    def _exit_multi_component_mode(self):
        """離開多部件模式：解鎖並恢復衍生字與深度拆解開關的原設定。"""
        if not self.multi_component_mode:
            return
        self.multi_component_mode = False
        self.multi_component_parts = []
        self.show_derived = self.saved_show_derived
        self.w.showDerivedCheckbox.enable(True)
        self.w.showDerivedCheckbox.set(self.show_derived)
        self.deep_analysis = self.saved_deep_analysis
        self.w.deepAnalysisCheckbox.enable(True)
        self.w.deepAnalysisCheckbox.set(self.deep_analysis)

    def _render_intersection(self, parts):
        """將「同時包含所有 parts 部件」的交集字渲染到右欄。

        套用筆畫篩選時，基準為所有輸入部件的筆畫數加總（如 氵木 = 3+4 = 7）；
        任一部件無筆畫資料則不篩選（回退全顯示）。
        """
        charset = self.currentCharset if self.currentCharset else None
        related = self.core.search_all(parts, charset)

        # 筆畫篩選：基準 = 各輸入部件筆畫數加總
        max_diff = self._stroke_filter_max_diff()
        if max_diff is not None:
            part_strokes = [self.core.get_stroke_count(p) for p in parts]
            if None not in part_strokes:
                base = sum(s for s in part_strokes if s is not None)
                related = self.core.filter_by_stroke_value(related, base, max_diff)

        display_text = self.core.clean_display_text("".join(related))
        self._set_related_output(
            display_text,
            result_count=len(related),
            hint=L("summary_multi_hint"),
        )

    def _clear_left_panel(self):
        """清空左欄（預覽 + 詳資）；多部件模式無單一焦點字時使用。"""
        self.current_char = None
        self.w.preview.set("")
        try:
            if self.w.previewImage:
                self.w.previewImage.show(False)
        except Exception:
            pass
        self.w.previewStatus.set("")
        if hasattr(self.w, "previewMeta"):
            self.w.previewMeta.set("")
        self.w.content.set("")
        self.treePane.idsSwitcher.show(False)
        if hasattr(self.w, "cnsLinkButton"):
            self.w.cnsLinkButton.enable(False)

    def _extract_valid_character_from_results(self, results: List) -> Optional[str]:
        """從搜尋結果中提取有效字符"""
        idc_chars = "⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻〾"

        for tree, content in results:
            if not content.strip():
                continue
            if self.core.is_error_message(content):
                continue
            if content in idc_chars:
                continue
            if self.core.is_valid_character(content):
                return content

        return None

    def toggle_deep_analysis(self, sender):
        """切換深度拆解"""
        self.deep_analysis = sender.get()
        self.settings.set("deepAnalysis", self.deep_analysis)

        # 保存當前選中的 IDS 索引
        saved_ids_index = getattr(self, "current_ids_index", 0)

        # 重新執行搜尋以更新結果
        self.search_callback(None)

        # 恢復 IDS 索引並刷新顯示
        if hasattr(self, "available_ids") and len(self.available_ids) > saved_ids_index:
            self.current_ids_index = saved_ids_index
            self.refresh_ids_display()

    def prev_ids(self, sender):
        """切換到上一個 IDS"""
        if len(self.available_ids) > 1:
            self.current_ids_index = (self.current_ids_index - 1) % len(
                self.available_ids
            )
            self.refresh_ids_display()

    def _selected_ids_variant(self):
        if not self.available_ids:
            return None
        if not 0 <= self.current_ids_index < len(self.available_ids):
            self.current_ids_index = 0
        return self.available_ids[self.current_ids_index]

    def _ids_variant_note(self, variant):
        """Format Bai IDS regional indicators for the current UI language."""
        indicators = [str(value) for value in variant.get("indicators", []) if value]
        raw_indicators = ", ".join(indicators)
        sources = []
        for indicator in indicators:
            for code in indicator.split(","):
                label_key = VARIANT_REGION_LABEL_KEYS.get(code.strip())
                if label_key:
                    label = L(label_key)
                    if label not in sources:
                        sources.append(label)

        notes = []
        if sources:
            notes.append(
                L("ids_variant_regional_form").format(
                    sources=" · ".join(sources), indicators=raw_indicators
                )
            )
        elif raw_indicators:
            notes.append(L("ids_variant_shape_note").format(indicators=raw_indicators))
        if variant.get("group") == "alternative":
            notes.append(L("ids_variant_alternative"))
        return " · ".join(notes)

    def _format_ids_variant(self, variant):
        if not variant:
            return ""
        ids = str(variant.get("ids", ""))
        note = self._ids_variant_note(variant)
        return f"{ids}\n{note}" if note else ids

    def next_ids(self, sender):
        """切換到下一個 IDS"""
        if len(self.available_ids) > 1:
            self.current_ids_index = (self.current_ids_index + 1) % len(
                self.available_ids
            )
            self.refresh_ids_display()

    def refresh_ids_display(self):
        """重新整理 IDS 顯示"""
        if not self.current_char or not self.available_ids:
            return

        data = self.core.get_data(self.current_char)
        if data:
            char_data = data[self.current_char]
            ids_display = self._format_ids_variant(self._selected_ids_variant())

            focus_char = self.current_char
            strokes = self.core.get_stroke_count(focus_char)
            strokes_line = f"{L('summary_strokes')}: {strokes}" if strokes is not None else f"{L('summary_strokes')}: —"
            glyph_status = self.adapter.get_glyph_design_status(self.adapter.get_current_font(), focus_char)
            design_line = L("preview_designed") if glyph_status.get("designed") else (L("preview_empty_glyph") if glyph_status.get("exists") else L("preview_missing_glyph"))
            detail_text = (
                f"{char_data['char']}\nU+{char_data['unicode'].upper()}\n{strokes_line} · {design_line}\n{ids_display}"
            )
            detail_text = self.core.clean_display_text(detail_text)
            # 使用動態字型的 NSAttributedString
            attr_string = self.create_attributed_string(detail_text, CONTENT_FONT_SIZE)
            text_view = self.w.content.getNSTextView()
            text_view.textStorage().setAttributedString_(attr_string)

            # 更新指示器
            self.treePane.idsSwitcher.indicator.set(
                f"{self.current_ids_index + 1}/{len(self.available_ids)}"
            )

            # 重新生成拆解樹（基於當前選中的 IDS）
            depth = 10 if self.deep_analysis else 1
            self.all_results = self.core.decompose(
                self.current_char, max_depth=depth, variant_index=self.current_ids_index
            )

            # 更新結果列表顯示
            self.display_results = [self._format_result_row(item) for item in self.all_results]
            self.treePane.resultList.set(self.display_results)
            self._adjust_result_list_column_width()

            # 更新相關字顯示（基於當前選中的 IDS）
            self.related_display_char = self.current_char
            self.update_related_display()

    # === 選擇處理 ===

    def selection_callback(self, sender):
        """
        處理結果列表中的選擇事件

        - IDC 符號：不執行任何動作
        - 漢字：只更新右側相關字區域，左側保持不變
        """
        selection = sender.getSelection()
        if not selection:
            return
        selected_item = self._result_row_to_source_text(sender[selection[0]])

        # 多部件模式：第一行＝原始查詢（回到 AND 交集）；其餘行＝單一部件（看該部件衍生字）
        if self.multi_component_mode:
            if selected_item == "".join(self.multi_component_parts):
                self.related_display_char = None
                self._render_intersection(self.multi_component_parts)
                self._clear_left_panel()
            else:
                char = self.core.extract_character(selected_item)
                if char and self.core.is_valid_character(char):
                    # 更新左欄（該部件資訊）與右欄（該部件衍生字，因開關已鎖定為開）
                    self.update_char_info(char)
            return

        # 使用 core 的字符提取邏輯
        char = self.core.extract_character(selected_item)

        # IDC 符號不執行任何動作
        idc_chars = "⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻〾"
        if char in idc_chars:
            return

        if char and self.core.is_valid_character(char):
            # 只更新右側相關字區域，不更新左側
            self.update_related_display(char)

    def update_char_info(self, char):
        """更新字符資訊（支援 IDS 切換）"""
        self.current_char = char
        self.related_display_char = char
        data = self.core.get_data(char)

        if data:
            char_data = data[char]
            # Preserve every Bai IDS form (including source-specific variants).
            self.available_ids = self.core.get_ids_variant_records(char)

            # 重置索引
            self.current_ids_index = 0

            ids_display = self._format_ids_variant(self._selected_ids_variant())
            if not ids_display:
                # 無 IDS 資料時顯示本字
                ids_display = char_data["char"]

            strokes = self.core.get_stroke_count(char)
            strokes_line = f"{L('summary_strokes')}: {strokes}" if strokes is not None else f"{L('summary_strokes')}: —"
            glyph_status = self.adapter.get_glyph_design_status(self.adapter.get_current_font(), char)
            design_line = L("preview_designed") if glyph_status.get("designed") else (L("preview_empty_glyph") if glyph_status.get("exists") else L("preview_missing_glyph"))
            detail_text = (
                f"{char_data['char']}\nU+{char_data['unicode'].upper()}\n{strokes_line} · {design_line}\n{ids_display}"
            )
            # 清理可能造成顯示問題的字符
            detail_text = self.core.clean_display_text(detail_text)
            # 使用動態字型的 NSAttributedString
            attr_string = self.create_attributed_string(detail_text, CONTENT_FONT_SIZE)
            text_view = self.w.content.getNSTextView()
            text_view.textStorage().setAttributedString_(attr_string)

            # 控制切換器顯示
            if len(self.available_ids) > 1:
                self.treePane.idsSwitcher.show(True)
                self.treePane.idsSwitcher.indicator.set(
                    f"{self.current_ids_index + 1}/{len(self.available_ids)}"
                )
            else:
                self.treePane.idsSwitcher.show(False)

        # 更新相關顯示
        self.update_related_display()
        self.update_preview(char)

        # 更新全字庫按鈕狀態
        if hasattr(self.w, "cnsLinkButton"):
            self.w.cnsLinkButton.enable(bool(self.current_char))
        self._refresh_summary_panel(focus_char=char)

    # === 顏色選擇器 ===

    def show_color_selector(self, sender):
        """開啟顏色選擇對話框（符合 macOS HIG）"""
        from AppKit import NSBox, NSColor, NSBoxCustom, NSClickGestureRecognizer

        # 建立 Sheet 對話框（緊湊版）
        # 色塊：6 × 20px + 5 × 4px 間距 = 140px
        # 視窗寬度：140 + 左右邊距 16×2 = 172，取 175px
        self.colorSheet = vanilla.Sheet((175, 140), self.w)

        # 標題列：左側標題，右側輔助按鈕
        self.colorSheet.title = vanilla.TextBox(
            (16, 14, 60, 17), L("color_picker_title"), sizeStyle="small"
        )

        # 輔助按鈕（標題列右側，SF Symbol 圖示）
        # 統一邊距 16px，按鈕間距 4px
        select_all_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "checkmark.circle.fill", None
        )
        self.colorSheet.selectAllButton = vanilla.ImageButton(
            (-60, 12, 20, 20),
            imageObject=select_all_icon,
            callback=self.select_all_colors,
            bordered=False,
        )
        self.colorSheet.selectAllButton.getNSButton().setToolTip_(L("btn_select_all"))

        deselect_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "xmark.circle", None
        )
        self.colorSheet.deselectAllButton = vanilla.ImageButton(
            (-36, 12, 20, 20),
            imageObject=deselect_icon,
            callback=self.deselect_all_colors,
            bordered=False,
        )
        self.colorSheet.deselectAllButton.getNSButton().setToolTip_(L("btn_clear"))

        # 色塊容器（左對齊，與標題對齊）
        # 寬度：6 × 20 + 5 × 4 = 140px，高度：2 × 20 + 1 × 4 = 44px
        self.colorSheet.colorBlockGroup = vanilla.Group((16, 38, 140, 48))
        group_view = self.colorSheet.colorBlockGroup.getNSView()

        # 清空映射
        self.dialog_color_block_map = {}
        self.color_blocks = {}
        self.color_block_states = {}

        # 建立 12 色視覺色塊矩陣（6x2 佈局，緊湊間距）
        chip_size = 20
        spacing = 4

        for color_id in range(12):
            row = color_id // 6
            col = color_id % 6
            x = col * (chip_size + spacing)
            # 反轉 y 座標：row 0 在上方，row 1 在下方
            y = (1 - row) * (chip_size + spacing)

            # 判斷是否已選取
            selected = color_id in self.filter_colors
            self.color_block_states[color_id] = selected

            # 取得顏色
            r, g, b, _ = GLYPH_COLOR_MAP[color_id]

            # 建立 NSBox 作為色塊
            color_box = NSBox.alloc().initWithFrame_(((x, y), (chip_size, chip_size)))
            color_box.setBoxType_(NSBoxCustom)

            # 設定填充顏色
            fill_color = NSColor.colorWithRed_green_blue_alpha_(r, g, b, 1.0)
            color_box.setFillColor_(fill_color)

            # 設定圓角為完全圓形
            color_box.setCornerRadius_(chip_size / 2.0)

            # 儲存色塊映射
            self.dialog_color_block_map[id(color_box)] = color_id
            self.color_blocks[color_id] = color_box

            # 設定邊框（選取時顯示）
            self._set_color_block_border(color_box, selected)

            # 添加點擊手勢識別器
            click_recognizer = NSClickGestureRecognizer.alloc().initWithTarget_action_(
                self.dialogColorBlockHandler, "handleBlockClick:"
            )
            color_box.addGestureRecognizer_(click_recognizer)

            # 加入到 Group
            group_view.addSubview_(color_box)

        # 主要操作按鈕（底部居中，small size）
        # 兩按鈕寬 60*2 + 間距 6 = 126，起始 x = (175-126)/2 ≈ 25
        self.colorSheet.cancelButton = vanilla.Button(
            (25, -38, 60, 24),
            L("btn_cancel"),
            callback=self.cancel_color_selection,
            sizeStyle="small",
        )

        self.colorSheet.applyButton = vanilla.Button(
            (91, -38, 60, 24),
            L("btn_apply"),
            callback=self.apply_color_selection,
            sizeStyle="small",
        )

        self.colorSheet.open()

        # 設定快捷鍵
        cancel_ns_button = self.colorSheet.cancelButton.getNSButton()
        cancel_ns_button.setKeyEquivalent_(chr(27))  # ESC 鍵

        apply_ns_button = self.colorSheet.applyButton.getNSButton()
        apply_ns_button.setKeyEquivalent_("\r")  # Enter 鍵（預設按鈕）

    def _set_color_block_border(self, color_box, selected):
        """設定色塊邊框樣式（統一管理選取狀態的視覺呈現）"""
        if selected:
            color_box.setBorderType_(1)  # NSLineBorder
            color_box.setBorderWidth_(2.0)
            color_box.setBorderColor_(NSColor.secondaryLabelColor())
        else:
            color_box.setBorderType_(0)
            color_box.setBorderWidth_(0)

    def toggle_color_block_selection(self, color_id):
        """切換色塊選取狀態"""
        if color_id is None:
            return

        # 切換狀態
        current_state = self.color_block_states.get(color_id, False)
        new_state = not current_state
        self.color_block_states[color_id] = new_state

        # 更新色塊邊框
        color_box = self.color_blocks.get(color_id)
        if color_box:
            self._set_color_block_border(color_box, new_state)

    def select_all_colors(self, sender):
        """全選所有顏色"""
        for color_id in range(12):
            self.color_block_states[color_id] = True
            color_box = self.color_blocks.get(color_id)
            if color_box:
                self._set_color_block_border(color_box, True)

    def deselect_all_colors(self, sender):
        """取消全選所有顏色"""
        for color_id in range(12):
            self.color_block_states[color_id] = False
            color_box = self.color_blocks.get(color_id)
            if color_box:
                self._set_color_block_border(color_box, False)

    def apply_color_selection(self, sender):
        """套用顏色選擇（視覺色塊版本）"""
        # 收集已選顏色（從色塊狀態讀取）
        selected_colors = []
        for color_id, selected in self.color_block_states.items():
            if selected:
                selected_colors.append(color_id)

        # 更新 filter_colors
        self.filter_colors = selected_colors

        # 儲存設定
        self.settings.set("filterColors", self.filter_colors)

        # 更新色塊顯示
        self.update_color_display()

        # 更新相關字顯示
        self.update_related_display()

        # 關閉對話框
        self.colorSheet.close()

    def cancel_color_selection(self, sender):
        """取消顏色選擇"""
        self.colorSheet.close()

    def update_color_display(self):
        """更新篩選按鈕的 tooltip 顯示選取數量"""
        count = len(self.filter_colors)
        if count == 0:
            tooltip = L("tooltip_no_filter")
        else:
            tooltip = L("tooltip_filter_count").format(count=count)

        self.w.filterButton.getNSButton().setToolTip_(tooltip)

    # === 相關字顯示 ===

    def toggle_derived_display(self, sender):
        """處理衍生字顯示切換"""
        self.show_derived = sender.get()

        # 儲存設定
        self.settings.set("showDerived", self.show_derived)

        # 更新顯示
        self.update_related_display()

    # === 筆畫篩選 ===

    def _stroke_filter_max_diff(self) -> Optional[int]:
        """將目前 tick 轉換為 filter_by_strokes 的 max_diff 參數。

        OFF tick → None（不篩選）；其他 tick → STROKE_FILTER_VALUES 對應值。
        """
        if self.stroke_filter_tick >= STROKE_FILTER_OFF_TICK:
            return None
        return STROKE_FILTER_VALUES[self.stroke_filter_tick]

    def _format_stroke_filter_value(self) -> str:
        """回傳當前筆畫篩選的簡短顯示字串（給 inline 標籤用）。

        OFF → 本地化「關」/「OFF」
        其他 → ±N（如「±2」）
        """
        diff = self._stroke_filter_max_diff()
        if diff is None:
            return L("slider_stroke_off")
        return f"±{diff}"

    def _refresh_stroke_filter_display(self):
        """同步更新滑桿 tooltip 與右側 inline 狀態文字"""
        value_text = self._format_stroke_filter_value()
        label = L("slider_stroke_label")  # e.g. "筆畫±"
        # tooltip 顯示完整描述（含功能說明）
        tooltip = f"{label}{value_text} — {L('tooltip_stroke_filter')}"
        try:
            self.w.strokeFilterSlider.getNSSlider().setToolTip_(tooltip)
        except Exception:
            pass

        # inline 文字只顯示當前值（節省空間）
        try:
            self.w.strokeFilterValue.set(value_text)
        except Exception:
            pass

    def on_stroke_filter_changed(self, sender):
        """筆畫篩選滑桿 callback：四捨五入到最近的 tick"""
        new_tick = int(round(sender.get()))
        if not 0 <= new_tick < STROKE_FILTER_TICK_COUNT:
            return
        if new_tick == self.stroke_filter_tick:
            return

        self.stroke_filter_tick = new_tick
        self.settings.set("strokeFilterTick", new_tick)
        self._refresh_stroke_filter_display()
        if self.multi_component_mode:
            self._render_intersection(self.multi_component_parts)
        else:
            self.update_related_display()

    def update_related_display(self, char=None):
        """
        更新相關字符顯示

        參數:
        char: 可選，指定要顯示的字符。若為 None 則使用 self.current_char。
        """
        # Preserve an explicitly selected sub-component as the right-pane viewpoint
        # when filters or view settings refresh the pane without a new char.
        display_char = resolve_display_char(
            char,
            getattr(self, "related_display_char", None),
            getattr(self, "current_char", None),
        )
        if display_char is None:
            return
        self.related_display_char = display_char

        display_lines = []
        charset = self.currentCharset if self.currentCharset else None

        # 取得關聯字結果（透過 core），使用當前選中的 IDS 拆法。
        # v1.2 position-aware semantics: upper section groups characters that
        # contain the query by top-level IDC position (⿰1, ⿰2, ⿰1·, ⿱≡·, ∅).
        variant_index = getattr(self, "current_ids_index", 0)
        immediate_chars = [
            c for c in self.core.search(display_char, charset) if c != display_char
        ]
        related_chars = set()

        # 預先計算筆畫篩選參數（避免每次迴圈重複）
        stroke_max_diff = self._stroke_filter_max_diff()

        filtered_immediate = immediate_chars
        if hasattr(self, "filter_colors") and len(self.filter_colors) > 0:
            font = self.adapter.get_current_font()
            filtered_immediate = self.adapter.filter_by_color(
                filtered_immediate, font, self.filter_colors
            )
        if stroke_max_diff is not None:
            filtered_immediate = self.core.filter_by_strokes(
                filtered_immediate, display_char, stroke_max_diff
            )

        for line in self.core.compose_immediate_component_lines(
            display_char, filtered_immediate, variant_index
        ):
            display_lines.append(line)
            if " " in line:
                related_chars.update(
                    ch
                    for ch in line.split(" ", 1)[1]
                    if self.core.is_valid_character(ch)
                )

        # 檢查是否啟用衍生字顯示
        position_section_has_lines = bool(display_lines)
        if self.show_derived:
            derived_groups = self.core.find_derived_characters(display_char, charset)
            if derived_groups:
                # 先加入分隔線
                if position_section_has_lines:
                    display_lines.append("-" * 3)

                # 過濾並加入衍生字結果
                for component, chars in derived_groups.items():
                    # 過濾掉已在關聯字中的字符
                    filtered_chars = [c for c in chars if c not in related_chars]

                    # 套用顏色篩選（透過 adapter）
                    if hasattr(self, "filter_colors") and len(self.filter_colors) > 0:
                        font = self.adapter.get_current_font()
                        filtered_chars = self.adapter.filter_by_color(
                            filtered_chars, font, self.filter_colors
                        )

                    # 套用筆畫篩選
                    if stroke_max_diff is not None:
                        filtered_chars = self.core.filter_by_strokes(
                            filtered_chars, display_char, stroke_max_diff
                        )

                    if filtered_chars:
                        display_lines.append(f"{component} {''.join(filtered_chars)}")

        if not display_lines:
            display_lines.append(display_char)

        display_text = "\n".join(display_lines) if display_lines else display_char
        self._set_related_output(
            display_text,
            focus_char=display_char,
            result_count=len(self._related_characters_only(display_text)),
        )

    # === 預覽功能 ===

    def update_preview(self, char):
        """Update preview. Prefer the actual designed Glyphs layer when present."""
        font_obj = self.adapter.get_current_font()
        status = self.adapter.get_glyph_design_status(font_obj, char)
        image = self.adapter.draw_glyph_preview_image(font_obj, char, 96)
        if image is not None and getattr(self.w, "previewImage", None) is not None:
            try:
                self.w.previewImage.setImage(imageObject=image)
                self.w.previewImage.show(True)
                self.w.preview.set("")
            except Exception:
                image = None
        if image is None:
            try:
                if getattr(self.w, "previewImage", None) is not None:
                    self.w.previewImage.show(False)
            except Exception:
                pass
            font = self.get_font_for_char(char)
            baseline_offset = -4
            paragraph_style = NSMutableParagraphStyle.alloc().init()
            paragraph_style.setAlignment_(1)
            preview_text = NSAttributedString.alloc().initWithString_attributes_(
                char,
                {
                    NSFontAttributeName: font,
                    NSForegroundColorAttributeName: NSColor.labelColor(),
                    NSBaselineOffsetAttributeName: baseline_offset,
                    NSParagraphStyleAttributeName: paragraph_style,
                },
            )
            self.w.preview.set(preview_text)
        payload = self._glyph_status_payload(char)
        try:
            glyph_name = status.get("glyphName") or "—"
        except Exception:
            glyph_name = "—"
        try:
            self.w.previewStatus.set(
                L("preview_status_line").format(
                    marker=payload.get("marker", "–"),
                    status=L(f"status_{payload.get('status', STATUS_MISSING)}"),
                    glyph=glyph_name,
                )
            )
            if hasattr(self.w, "previewMeta"):
                strokes = self.core.get_stroke_count(char)
                strokes_text = str(strokes) if strokes is not None else "—"
                self.w.previewMeta.set(
                    L("preview_meta_line").format(unicode=f"U+{ord(char):04X}", strokes=strokes_text)
                )
        except Exception:
            pass

    def get_font_for_char(self, char, size=72):
        """
        使用 macOS 原生 CTFontCreateForString 自動選擇字型

        讓系統自動從 cascade list 尋找能顯示該字符的字型，
        無需硬編碼特定字型家族，支援不同區域使用者的系統字型。

        參數:
            char: 要顯示的字符
            size: 字型大小（預設 72pt）

        回傳:
            NSFont: 能顯示該字符的字型
        """
        if not char:
            return NSFont.systemFontOfSize_(size)

        # 查詢快取
        cache_key = (char, size)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        try:
            # 建立基礎 CTFont（系統 UI 字型包含完整的 cascade list）
            base_ct_font = CoreText.CTFontCreateWithName(
                ".AppleSystemUIFont", size, None
            )

            # 使用 CTFontCreateForString 尋找能顯示該字符的字型
            # range: (location, length)
            fallback_ct_font = CoreText.CTFontCreateForString(
                base_ct_font, char, (0, len(char))
            )

            # 釋放 base_ct_font（不再需要，避免記憶體洩漏）
            del base_ct_font

            # 取得 fallback 字型的 PostScript 名稱
            ps_name = CoreText.CTFontCopyPostScriptName(fallback_ct_font)

            # 檢查是否為 LastResort 字型（表示系統找不到適合的字型）
            is_last_resort = ps_name and "LastResort" in str(ps_name)

            # 釋放 ps_name（不再需要）
            del ps_name

            if is_last_resort:
                # 釋放 fallback_ct_font（不使用，改用系統字型）
                del fallback_ct_font
                font = NSFont.systemFontOfSize_(size)
            else:
                # CTFont 和 NSFont 可透過 toll-free bridging 互轉
                font = fallback_ct_font

            # 快取管理：超過上限時清除一半
            if len(self._font_cache) >= self._CACHE_MAX_SIZE:
                keys_to_remove = list(self._font_cache.keys())[
                    : self._CACHE_MAX_SIZE // 2
                ]
                for key in keys_to_remove:
                    del self._font_cache[key]

            # 快取結果
            self._font_cache[cache_key] = font
            return font

        except Exception:
            # 發生錯誤時 fallback 到系統字型
            return NSFont.systemFontOfSize_(size)

    def create_related_attributed_string(self, text, size):
        """Right pane renderer with tile/status styling.

        Tile mode renders each related character as a two-glyph token: status marker + character.
        By default this keeps the legacy status colors. When the color-label option
        is enabled, Glyphs color labels tint the character background and status
        markers switch to neutral contrast/opacity styling.
        """
        if not text:
            return NSAttributedString.alloc().initWithString_("")

        result = NSMutableAttributedString.alloc().init()
        system_font = NSFont.systemFontOfSize_(max(10, size - 7))
        marker_font = NSFont.boldSystemFontOfSize_(max(9, size - 8))
        label_font = NSFont.boldSystemFontOfSize_(max(10, size - 7))
        separator_font = NSFont.systemFontOfSize_(max(10, size - 7))
        paragraph_style = NSMutableParagraphStyle.alloc().init()
        line_height = size * (1.28 if self.tile_view_enabled else RELATED_CHARS_LINE_HEIGHT)
        paragraph_style.setMinimumLineHeight_(line_height)
        paragraph_style.setMaximumLineHeight_(line_height)

        label_color = self._semantic_color("secondaryLabelColor", "labelColor")
        separator_color = self._semantic_color("tertiaryLabelColor", "secondaryLabelColor")
        favorite_color = self._semantic_color("systemOrangeColor", "labelColor")
        designed_color = self._semantic_color("systemGreenColor", "labelColor")
        exists_color = self._semantic_color("systemBlueColor", "labelColor")
        neutral_marker_color = self._semantic_color("secondaryLabelColor", "labelColor")
        missing_color = self._semantic_color("tertiaryLabelColor", "secondaryLabelColor")
        accent_color = self._semantic_color("controlAccentColor", "systemBlueColor")
        designed_bg = self._semantic_color("selectedTextBackgroundColor", "controlBackgroundColor")
        exists_bg = self._semantic_color("textBackgroundColor", "controlBackgroundColor")
        missing_bg = self._semantic_color("controlBackgroundColor", "windowBackgroundColor")

        if self.tile_color_labels_enabled:
            marker_colors = {
                "★": favorite_color,
                "●": neutral_marker_color,
                "○": neutral_marker_color,
                "–": missing_color,
                "-": missing_color,
            }
        else:
            marker_colors = {
                "★": favorite_color,
                "●": designed_color,
                "○": exists_color,
                "–": missing_color,
                "-": missing_color,
            }

        def append(piece, attrs):
            result.appendAttributedString_(
                NSAttributedString.alloc().initWithString_attributes_(piece, attrs)
            )

        lines = text.splitlines()
        for line_index, line in enumerate(lines):
            stripped = line.strip()
            base = {NSParagraphStyleAttributeName: paragraph_style}
            if not stripped:
                pass
            elif stripped.startswith("────") or set(stripped) == {"-"}:
                attrs = dict(base)
                attrs.update({
                    NSFontAttributeName: separator_font,
                    NSForegroundColorAttributeName: separator_color,
                })
                append("────────", attrs)
            elif stripped.startswith("▸ ") or (
                "  " not in line
                and len(stripped) <= 14
                and not any(self.core.is_valid_character(ch) for ch in stripped)
            ):
                attrs = dict(base)
                attrs.update({
                    NSFontAttributeName: label_font,
                    NSForegroundColorAttributeName: label_color,
                })
                append(stripped, attrs)
            else:
                i = 0
                while i < len(line):
                    ch = line[i]
                    if ch.isspace():
                        append(ch, {NSFontAttributeName: system_font, NSParagraphStyleAttributeName: paragraph_style})
                        i += 1
                        continue

                    # Tile token: marker + valid CJK char.
                    if ch in marker_colors and i + 1 < len(line) and self.core.is_valid_character(line[i + 1]):
                        marker = ch
                        tile_char = line[i + 1]
                        status = self._raw_glyph_status(tile_char)
                        color_label = self._glyph_label_color(tile_char) if self.tile_color_labels_enabled else None
                        marker_attrs = dict(base)
                        marker_attrs.update({
                            NSFontAttributeName: marker_font,
                            NSForegroundColorAttributeName: marker_colors.get(marker, missing_color),
                            NSBaselineOffsetAttributeName: max(1, size * 0.08),
                        })
                        char_attrs = dict(base)
                        char_attrs.update({
                            NSFontAttributeName: self.get_font_for_char(tile_char, size),
                            NSForegroundColorAttributeName: (
                                favorite_color
                                if tile_char in self.favorite_chars
                                else self._with_alpha(NSColor.labelColor(), 0.42)
                                if self.tile_color_labels_enabled and not status.get("exists")
                                else NSColor.labelColor()
                            ),
                            NSKernAttributeName: 0.4,
                        })
                        if self.tile_view_enabled:
                            if self.tile_color_labels_enabled:
                                char_attrs[NSBackgroundColorAttributeName] = (
                                    self._with_alpha(color_label, 0.28) if color_label is not None else missing_bg
                                )
                            elif status.get("designed"):
                                char_attrs[NSBackgroundColorAttributeName] = designed_bg
                            elif status.get("exists"):
                                char_attrs[NSBackgroundColorAttributeName] = exists_bg
                            else:
                                char_attrs[NSBackgroundColorAttributeName] = missing_bg
                        if tile_char == getattr(self, "current_char", None):
                            char_attrs[NSForegroundColorAttributeName] = accent_color
                        append(marker, marker_attrs)
                        append(tile_char, char_attrs)
                        i += 2
                        continue

                    attrs = dict(base)
                    if self.core.is_valid_character(ch):
                        status = self._raw_glyph_status(ch)
                        color_label = self._glyph_label_color(ch) if self.tile_color_labels_enabled else None
                        attrs.update({
                            NSFontAttributeName: self.get_font_for_char(ch, size),
                            NSForegroundColorAttributeName: (
                                favorite_color
                                if ch in self.favorite_chars
                                else self._with_alpha(NSColor.labelColor(), 0.42)
                                if self.tile_color_labels_enabled and not status.get("exists")
                                else NSColor.labelColor()
                            ),
                            NSKernAttributeName: 0.8,
                        })
                        if self.tile_view_enabled:
                            if self.tile_color_labels_enabled:
                                attrs[NSBackgroundColorAttributeName] = (
                                    self._with_alpha(color_label, 0.28) if color_label is not None else missing_bg
                                )
                            elif status.get("designed"):
                                attrs[NSBackgroundColorAttributeName] = designed_bg
                            elif status.get("exists"):
                                attrs[NSBackgroundColorAttributeName] = exists_bg
                            else:
                                attrs[NSBackgroundColorAttributeName] = missing_bg
                    else:
                        attrs.update({NSFontAttributeName: system_font, NSForegroundColorAttributeName: label_color})
                    append(ch, attrs)
                    i += 1
            if line_index < len(lines) - 1:
                append("\n", {NSFontAttributeName: system_font, NSParagraphStyleAttributeName: paragraph_style})
        return result

    def create_attributed_string(self, text, size, use_enhanced_spacing=False):
        """
        建立帶有動態字型和顏色的 NSAttributedString

        為文字中的每個漢字字符自動選擇適當的字型（使用 CTFontCreateForString），
        非漢字字符使用系統字型。使用系統語義顏色支援深淺模式。

        參數:
            text: 要顯示的文字
            size: 字型大小
            use_enhanced_spacing: 是否使用加大的字距和行距（用於右側相關字區域）

        回傳:
            NSAttributedString: 帶有正確字型和顏色的富文本
        """
        if not text:
            return NSAttributedString.alloc().initWithString_("")

        result = NSMutableAttributedString.alloc().init()
        system_font = NSFont.systemFontOfSize_(size)
        # 使用系統語義顏色，自動適應深淺模式
        text_color = NSColor.labelColor()

        # 建立段落樣式（用於行距）
        paragraph_style = None
        if use_enhanced_spacing:
            paragraph_style = NSMutableParagraphStyle.alloc().init()
            # 設定行距：行高 = 字體大小 × 行高倍數
            line_height = size * RELATED_CHARS_LINE_HEIGHT
            paragraph_style.setMinimumLineHeight_(line_height)
            paragraph_style.setMaximumLineHeight_(line_height)

        for char in text:
            code_point = ord(char)
            # 為 CJK 相關字符使用 TW-Sung 字型
            # 包含完整的 CJK 區塊以確保一致性
            is_cjk_related = (
                0x2E80 <= code_point <= 0x2EFF  # CJK Radicals Supplement（部首補充）
                or 0x2F00 <= code_point <= 0x2FDF  # Kangxi Radicals（康熙部首）
                or 0x2FF0 <= code_point <= 0x2FFF  # IDC（表意文字描述字符 ⿰⿱⿲）
                or 0x3400 <= code_point <= 0x4DBF  # CJK Extension A
                or 0x4E00 <= code_point <= 0x9FFF  # CJK Unified Ideographs
                or 0xF900 <= code_point <= 0xFAFF  # CJK Compatibility Ideographs
                or code_point >= 0x20000  # CJK Extension B-H+
            )
            if is_cjk_related:
                font = self.get_font_for_char(char, size)
            else:
                font = system_font

            # 建立屬性字典
            attributes = {
                NSFontAttributeName: font,
                NSForegroundColorAttributeName: text_color,
            }

            # 加入字距和行距（僅用於右側相關字區域）
            if use_enhanced_spacing:
                attributes[NSKernAttributeName] = RELATED_CHARS_KERN
                if paragraph_style:
                    attributes[NSParagraphStyleAttributeName] = paragraph_style

            char_attr = NSAttributedString.alloc().initWithString_attributes_(
                char, attributes
            )
            result.appendAttributedString_(char_attr)

        return result

    # === 插入按鈕功能 ===

    def setup_window_resize_observer(self):
        """ウィンドウ／分割バー変更時にタイルを再折り返しする。"""
        try:
            window = self.w.getNSWindow()
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self.resizeObserver,
                "windowDidResize:",
                "NSWindowDidResizeNotification",
                window,
            )
        except Exception:
            pass
        try:
            split_view = self.w.resultsSplit.getNSSplitView()
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self.resizeObserver,
                "splitViewDidResizeSubviews:",
                "NSSplitViewDidResizeSubviewsNotification",
                split_view,
            )
        except Exception:
            pass

    def on_window_resized(self, notification=None):
        self._relayout_related_tiles_to_scroll_width()
        self._refresh_results_split_interaction()

    def on_results_split_resized(self, notification=None):
        self._relayout_related_tiles_to_scroll_width()
        self._refresh_results_split_interaction()

    def setup_selection_observer(self):
        """監聽右側相關字區域的選取變化，控制插入按鈕啟用狀態"""
        textView = self.relatedPane.relatedChars.getNSTextView()
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self.selectionObserver,
            "textViewSelectionDidChange:",
            "NSTextViewDidChangeSelectionNotification",
            textView,
        )

    def setup_related_double_click_handler(self):
        """右ペインのタイル/文字をダブルクリックで新規タブ展開できるようにする。"""
        try:
            textView = self.relatedPane.relatedChars.getNSTextView()
            recognizer = NSClickGestureRecognizer.alloc().initWithTarget_action_(
                self.relatedDoubleClickHandler, "handleRelatedDoubleClick:"
            )
            recognizer.setNumberOfClicksRequired_(2)
            recognizer.setDelaysPrimaryMouseButtonEvents_(False)
            textView.addGestureRecognizer_(recognizer)
            self.relatedDoubleClickRecognizer = recognizer
            try:
                textView.setToolTip_(L("tooltip_related_double_click"))
            except Exception:
                pass
        except Exception:
            self.relatedDoubleClickRecognizer = None
        self.resizeObserver = None
        self.last_related_selection_chars = ""
        self.last_related_multi_selection_chars = ""
        self.last_related_multi_selection_time = 0

    def on_selection_changed(self, notification):
        """當選取變化時更新插入按鈕狀態"""
        textView = self.relatedPane.relatedChars.getNSTextView()
        has_selection = textView.selectedRange().length > 0
        self.w.insertButton.enable(has_selection)
        if hasattr(self.w, "searchSelectedButton"):
            self.w.searchSelectedButton.enable(has_selection)
        if hasattr(self.w, "copyRelatedButton"):
            self.w.copyRelatedButton.enable(has_selection or bool(self._related_characters_only()))
        try:
            selected_text = self._selected_related_text() if has_selection else ""
            chars = self._extract_chars_for_new_tab(selected_text)
            self.last_related_selection_chars = chars
            if len(chars) > 1:
                self.last_related_multi_selection_chars = chars
                self.last_related_multi_selection_time = time.time()
        except Exception:
            pass
        self._refresh_favorite_button()

    def insert_selected_text(self, sender):
        """將選取的文字插入到編輯分頁"""
        if self.tile_view_enabled and self._tile_engine_available():
            selectedText = self._selected_tile_chars()
        else:
            textView = self.relatedPane.relatedChars.getNSTextView()
            selectedRange = textView.selectedRange()
            if selectedRange.length == 0:
                return
            selectedText = textView.string().substringWithRange_(selectedRange)
            selectedText = self._extract_chars_for_new_tab(str(selectedText).strip()) or str(selectedText).strip()
        if selectedText:
            font = self.adapter.get_current_font()
            self.adapter.insert_to_tab(font, selectedText)

    # === 全字庫連結 ===

    def open_cns_link(self, sender):
        """在瀏覽器開啟當前字符的全字庫頁面"""
        if not self.current_char:
            return

        unicode_hex = format(ord(self.current_char), "X")

        # 根據 Glyphs 介面語言決定全字庫語言
        # la=0 中文版（繁中/簡中/日文）, la=1 英文版（其他語言）
        try:
            from GlyphsApp import Glyphs

            glyphs_lang = Glyphs.defaults.get("AppleLanguages", ["en"])[0]
            # 中日文使用者使用中文版，其他使用英文版
            la = (
                0 if glyphs_lang.startswith("zh") or glyphs_lang.startswith("ja") else 1
            )
        except Exception:
            la = 1  # fallback 使用英文版

        url = f"https://www.cns11643.gov.tw/searchQ.jsp?WORD={unicode_hex}&la={la}"

        import webbrowser

        webbrowser.open(url)

    # === 視窗焦點事件（Issue #31）===

    def on_window_became_key(self, sender):
        """
        視窗獲得焦點時的回調（Issue #31）

        進入手動模式，暫停自動跟隨 Glyphs 選中字符
        """
        self.is_manual_mode = True

    def on_window_resigned_key(self, sender):
        """
        視窗失去焦點時的回調（Issue #31）

        進入自動模式，恢復跟隨 Glyphs 選中字符。
        只有當 Glyphs 當前字形與上次不同時才會刷新搜尋。
        """
        self.is_manual_mode = False

        # 觸發檢查，on_glyph_changed 會自動比較當前字形與 last_glyph_name
        # 只有字形改變時才會執行搜尋
        self.on_glyph_changed()

    # === 其他功能 ===

    def windowWillClose(self, sender):
        """
        視窗關閉時的清理方法

        參數:
        sender: 視窗物件
        """
        # 移除選取變化監聽
        try:
            NSNotificationCenter.defaultCenter().removeObserver_(self.selectionObserver)
        except Exception:
            pass
        try:
            if self.resizeObserver is not None:
                NSNotificationCenter.defaultCenter().removeObserver_(self.resizeObserver)
        except Exception:
            pass

        # 移除 Glyphs 回調（透過 adapter）
        try:
            self.adapter.unregister_callback(self.on_glyph_changed)
        except Exception:
            pass


# 作為腳本獨立執行時建立實例
if __name__ == "__main__":
    HanziComponentSearchTool()
