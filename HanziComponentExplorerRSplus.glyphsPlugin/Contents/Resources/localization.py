# encoding: utf-8
"""
Hanzi Component Explorer RS+ - 本地化字串模組

提供 UI 介面多語言支援，使用 Glyphs.localize() API
支援語言：en, zh-Hant, zh-Hans, ja

Original copyright © 2025 TzuYuan Yin
Fork modifications copyright © 2026 Ooma Kobayashi
Modified from the original upstream project.
"""

from __future__ import division, print_function, unicode_literals

LANGUAGES = ("en", "zh-Hant", "zh-Hans", "ja")

# 本地化字串字典
STRINGS = {
    # 視窗與標題
    "window_title": {
        "en": "Hanzi Component Explorer RS+",
        "zh-Hant": "漢字部件查詢 RS+",
        "zh-Hans": "汉字部件查询 RS+",
        "ja": "漢字部品検索 RS+",
    },
    "search_placeholder": {
        "en": "Enter character or Unicode",
        "zh-Hant": "輸入漢字或 Unicode 編碼",
        "zh-Hans": "输入汉字或 Unicode 编码",
        "ja": "漢字または Unicode を入力",
    },
    "hint_open_font": {
        "en": "Open a font file to search",
        "zh-Hant": "請先開啟字型檔案",
        "zh-Hans": "请先打开字体文件",
        "ja": "フォントファイルを開いてください",
    },
    "menu_ref_fonts_empty": {
        "en": "Reference Fonts: None",
        "zh-Hant": "參考字型：無",
        "zh-Hans": "参考字体：无",
        "ja": "参照フォント：なし",
    },
    "menu_ref_fonts_count": {
        "en": "Reference Fonts: {count} file(s)",
        "zh-Hant": "參考字型：{count} 個檔案",
        "zh-Hans": "参考字体：{count} 个文件",
        "ja": "参照フォント：{count} 個",
    },
    "menu_ref_fonts_count_failed": {
        "en": "Reference Fonts: {count} file(s), {failed} failed to load",
        "zh-Hant": "參考字型：{count} 個檔案（{failed} 個載入失敗）",
        "zh-Hans": "参考字体：{count} 个文件（{failed} 个加载失败）",
        "ja": "参照フォント：{count} 個（{failed} 個読み込み失敗）",
    },
    "menu_open_ref_fonts_folder": {
        "en": "Open Reference Fonts Folder...",
        "zh-Hant": "開啟參考字型資料夾...",
        "zh-Hans": "打开参考字体文件夹...",
        "ja": "参照フォントフォルダを開く...",
    },
    "tooltip_display_font": {
        "en": "Display font: {name} ({source})",
        "zh-Hant": "顯示字型：{name}（{source}）",
        "zh-Hans": "显示字体：{name}（{source}）",
        "ja": "表示フォント：{name}（{source}）",
    },
    "tooltip_font_missing": {
        "en": "No installed or reference font covers this character",
        "zh-Hant": "無已安裝或參考字型涵蓋此字",
        "zh-Hans": "无已安装或参考字体涵盖此字",
        "ja": "この文字を含むフォントがありません",
    },
    "font_source_folder": {
        "en": "reference folder", "zh-Hant": "參考資料夾", "zh-Hans": "参考文件夹", "ja": "参照フォルダ",
    },
    "font_source_family": {
        "en": "installed, matches current document", "zh-Hant": "已安裝・同當前文件", "zh-Hans": "已安装・同当前文件", "ja": "インストール済み・現在の書類と同名",
    },
    "font_source_covering": {
        "en": "installed", "zh-Hant": "已安裝", "zh-Hans": "已安装", "ja": "インストール済み",
    },
    "font_source_cascade": {
        "en": "system cascade", "zh-Hant": "系統自動選擇", "zh-Hans": "系统自动选择", "ja": "システム自動選択",
    },
    "font_source_system": {
        "en": "system font", "zh-Hant": "系統字型", "zh-Hans": "系统字体", "ja": "システムフォント",
    },
    # CheckBox
    "checkbox_deep_analysis": {
        "en": "Deep Analysis",
        "zh-Hant": "深度拆解",
        "zh-Hans": "深度拆解",
        "ja": "深層分解",
    },
    "checkbox_derived": {
        "en": "Derived",
        "zh-Hant": "衍生字",
        "zh-Hans": "衍生字",
        "ja": "派生字",
    },
    # 按鈕（參照 Glyphs 官方詞彙）
    "btn_select_all": {
        "en": "Select All",
        "zh-Hant": "全選",
        "zh-Hans": "全选",
        "ja": "すべてを選択",
    },
    "btn_clear": {
        "en": "Clear",
        "zh-Hant": "清除",
        "zh-Hans": "清除",
        "ja": "消去",
    },
    "btn_cancel": {
        "en": "Cancel",
        "zh-Hant": "取消",
        "zh-Hans": "取消",
        "ja": "キャンセル",
    },
    "btn_apply": {
        "en": "Apply",
        "zh-Hant": "套用",
        "zh-Hans": "应用",
        "ja": "適用",
    },
    # 下拉選單
    "charset_font": {
        "en": "Font File",
        "zh-Hant": "字型檔",
        "zh-Hans": "字体文件",
        "ja": "フォントファイル",
    },
    "charset_custom": {
        "en": "Custom Set...",
        "zh-Hant": "自訂字集...",
        "zh-Hans": "自定义字集...",
        "ja": "カスタムセット...",
    },
    # 顏色選擇器
    "color_picker_title": {
        "en": "Select Color",
        "zh-Hant": "選擇顏色",
        "zh-Hans": "选择颜色",
        "ja": "色を選択",
    },
    # 插入按鈕
    "btn_insert_tooltip": {
        "en": "Insert selected text in current tab",
        "zh-Hant": "將選取文字插入到目前分頁",
        "zh-Hans": "将选中文字插入到当前标签页",
        "ja": "選択テキストを現在のタブに挿入",
    },
    # 顏色篩選 Tooltip
    "tooltip_no_filter": {
        "en": "No color filter",
        "zh-Hant": "無顏色篩選",
        "zh-Hans": "无颜色筛选",
        "ja": "カラーフィルターなし",
    },
    "tooltip_filter_count": {
        "en": "{count} colors selected",
        "zh-Hant": "已選 {count} 個顏色",
        "zh-Hans": "已选 {count} 个颜色",
        "ja": "{count} 色選択中",
    },
    # 統一篩選選單
    "menu_color_filter": {
        "en": "Color Filter...",
        "zh-Hant": "顏色篩選...",
        "zh-Hans": "颜色筛选...",
        "ja": "カラーフィルター...",
    },
    "menu_color_filter_count": {
        "en": "Color Filter ({count})...",
        "zh-Hant": "顏色篩選 ({count})...",
        "zh-Hans": "颜色筛选 ({count})...",
        "ja": "カラーフィルター ({count})...",
    },
    # 筆畫數篩選滑桿
    "slider_stroke_label": {
        "en": "Strokes±",
        "zh-Hant": "筆畫±",
        "zh-Hans": "笔画±",
        "ja": "画数±",
    },
    "slider_stroke_off": {
        "en": "OFF",
        "zh-Hant": "關",
        "zh-Hans": "关",
        "ja": "OFF",
    },
    "tooltip_stroke_filter": {
        "en": "Filter related characters by stroke count difference from current character",
        "zh-Hant": "依與當前字的筆畫差篩選相關字",
        "zh-Hans": "依与当前字的笔画差筛选相关字",
        "ja": "現在の字との画数差で関連字をフィルター",
    },
    # Extended UI strings
    "btn_history_tooltip": {
        "en": "Search history",
        "zh-Hant": "搜尋履歷",
        "zh-Hans": "搜索历史",
        "ja": "検索履歴",
    },
    "btn_clear_search_tooltip": {
        "en": "Clear search and return to auto-follow",
        "zh-Hant": "清除搜尋並回到自動跟隨",
        "zh-Hans": "清除搜索并回到自动跟随",
        "ja": "検索を消去して自動追従へ戻る",
    },
    "btn_favorites_tooltip": {
        "en": "Favorites",
        "zh-Hant": "收藏字",
        "zh-Hans": "收藏字",
        "ja": "お気に入り",
    },
    "btn_tile_view_tooltip": {
        "en": "Toggle character tiles",
        "zh-Hant": "切換字符磁磚",
        "zh-Hans": "切换字符磁贴",
        "ja": "文字タイル表示を切り替え",
    },

    "btn_tile_density_tooltip": {
        "en": "Cycle tile density",
        "zh-Hant": "切換磁磚密度",
        "zh-Hans": "切换磁贴密度",
        "ja": "タイル密度を切り替え",
    },
    "btn_tile_density_tooltip_state": {
        "en": "Tile density: {density}",
        "zh-Hant": "磁磚密度：{density}",
        "zh-Hans": "磁贴密度：{density}",
        "ja": "タイル密度：{density}",
    },
    "menu_tile_density": {
        "en": "Tile Density: {density}",
        "zh-Hant": "磁磚密度：{density}",
        "zh-Hans": "磁贴密度：{density}",
        "ja": "タイル密度：{density}",
    },
    "density_compact": {
        "en": "Compact",
        "zh-Hant": "緊湊",
        "zh-Hans": "紧凑",
        "ja": "コンパクト",
    },
    "density_comfortable": {
        "en": "Comfortable",
        "zh-Hant": "標準",
        "zh-Hans": "标准",
        "ja": "標準",
    },
    "density_spacious": {
        "en": "Spacious",
        "zh-Hant": "寬鬆",
        "zh-Hans": "宽松",
        "ja": "ゆったり",
    },
    "summary_tile_density_changed": {
        "en": "Tile density changed to {density}.",
        "zh-Hant": "磁磚密度已切換為 {density}。",
        "zh-Hans": "磁贴密度已切换为 {density}。",
        "ja": "タイル密度を {density} にしました。",
    },
    "summary_tile_legend": {
        "en": "{density} · ●{designed} ○{exists} –{missing} ★{favorite} · {progress}% designed",
        "zh-Hant": "{density} · ●{designed} ○{exists} –{missing} ★{favorite} · 已設計 {progress}%",
        "zh-Hans": "{density} · ●{designed} ○{exists} –{missing} ★{favorite} · 已设计 {progress}%",
        "ja": "{density} · ●{designed} ○{exists} –{missing} ★{favorite} · 制作済み {progress}%",
    },
    "btn_cns_tooltip": {
        "en": "Open CNS11643 lookup",
        "zh-Hant": "開啟全字庫查詢",
        "zh-Hans": "打开全字库查询",
        "ja": "CNS11643 全字庫で開く",
    },
    "btn_filter_tooltip": {
        "en": "Filters and display options",
        "zh-Hant": "篩選與顯示選項",
        "zh-Hans": "筛选与显示选项",
        "ja": "フィルターと表示設定",
    },
    "btn_copy_related_tooltip": {
        "en": "Copy selected text, or all related characters",
        "zh-Hant": "複製選取文字；未選取時複製全部相關字",
        "zh-Hans": "复制选中文字；未选择时复制全部相关字",
        "ja": "選択文字、未選択なら関連字全体をコピー",
    },
    "btn_search_selected_tooltip": {
        "en": "Search selected character",
        "zh-Hant": "搜尋選取字符",
        "zh-Hans": "搜索选中字符",
        "ja": "選択した字を検索",
    },
    "btn_insert_all_tooltip": {
        "en": "Insert all related characters in current tab",
        "zh-Hant": "將所有相關字插入目前分頁",
        "zh-Hans": "将所有相关字插入当前标签页",
        "ja": "関連字をまとめて現在のタブに挿入",
    },
    "menu_history_empty": {
        "en": "No recent searches",
        "zh-Hant": "尚無搜尋履歷",
        "zh-Hans": "暂无搜索历史",
        "ja": "履歴はまだありません",
    },
    "menu_history_clear": {
        "en": "Clear History",
        "zh-Hant": "清除履歷",
        "zh-Hans": "清除历史",
        "ja": "履歴を消去",
    },
    "menu_favorites": {
        "en": "Favorites",
        "zh-Hant": "收藏字",
        "zh-Hans": "收藏字",
        "ja": "お気に入り",
    },
    "menu_favorites_empty": {
        "en": "No favorites yet",
        "zh-Hant": "尚無收藏字",
        "zh-Hans": "暂无收藏字",
        "ja": "まだ登録がありません",
    },
    "menu_favorites_clear": {
        "en": "Clear Favorites",
        "zh-Hant": "清除收藏",
        "zh-Hans": "清除收藏",
        "ja": "お気に入りを消去",
    },
    "menu_favorite_add": {
        "en": "Add {char} to Favorites",
        "zh-Hant": "收藏 {char}",
        "zh-Hans": "收藏 {char}",
        "ja": "{char} をお気に入りに追加",
    },
    "menu_favorite_remove": {
        "en": "Remove {char} from Favorites",
        "zh-Hant": "取消收藏 {char}",
        "zh-Hans": "取消收藏 {char}",
        "ja": "{char} をお気に入りから削除",
    },
    "menu_result_actions": {
        "en": "Display and Actions",
        "zh-Hant": "顯示與操作",
        "zh-Hans": "显示与操作",
        "ja": "表示と操作",
    },
    "menu_copy_chars_only": {
        "en": "Copy Characters Only",
        "zh-Hant": "只複製字符",
        "zh-Hans": "只复制字符",
        "ja": "字だけをコピー",
    },
    "menu_insert_all_related": {
        "en": "Insert All Related Characters",
        "zh-Hant": "插入所有相關字",
        "zh-Hans": "插入所有相关字",
        "ja": "関連字をすべて挿入",
    },
    "menu_tile_view": {
        "en": "Tile View",
        "zh-Hant": "磁磚顯示",
        "zh-Hans": "磁贴显示",
        "ja": "タイル表示",
    },
    "menu_tile_glyph_preview": {
        "en": "Preview in Tiles",
        "zh-Hant": "磁磚內預覽",
        "zh-Hans": "磁贴内预览",
        "ja": "タイル内プレビュー",
    },
    "menu_tile_color_labels": {
        "en": "Color Labels in Tiles",
        "zh-Hant": "磁磚顯示顏色標籤",
        "zh-Hans": "磁贴显示颜色标签",
        "ja": "タイルにカラーラベルを表示",
    },
    "menu_list_preview": {
        "en": "List Badges",
        "zh-Hant": "列表標記",
        "zh-Hans": "列表标记",
        "ja": "一覧バッジ",
    },

    "menu_designed_only_filter": {
        "en": "Show Designed Only",
        "zh-Hant": "只顯示已完成",
        "zh-Hans": "只显示已完成",
        "ja": "制作済みのみ表示",
    },
    "summary_filter_all": {
        "en": "All statuses",
        "zh-Hant": "全部狀態",
        "zh-Hans": "全部状态",
        "ja": "全ステータス",
    },
    "summary_filter_designed_only": {
        "en": "Designed only",
        "zh-Hant": "僅已設計",
        "zh-Hans": "仅已设计",
        "ja": "制作済みのみ",
    },
    "summary_designed_only_enabled": {
        "en": "Showing designed characters only.",
        "zh-Hant": "目前只顯示已完成字符。",
        "zh-Hans": "当前只显示已完成字符。",
        "ja": "制作済みのみ表示します。",
    },
    "summary_designed_only_disabled": {
        "en": "Showing all statuses.",
        "zh-Hant": "目前顯示全部狀態。",
        "zh-Hans": "当前显示全部状态。",
        "ja": "すべて表示します。",
    },
    "menu_tile_context_header": {
        "en": "Selected {count}: {text}",
        "zh-Hant": "已選 {count}：{text}",
        "zh-Hans": "已选 {count}：{text}",
        "ja": "選択 {count}：{text}",
    },
    "menu_tile_context_no_selection": {
        "en": "No tile selected",
        "zh-Hant": "尚未選取磁磚",
        "zh-Hans": "尚未选取磁贴",
        "ja": "タイル未選択",
    },
    "menu_open_selected_tiles": {
        "en": "Open Selected in New Tab",
        "zh-Hant": "在新分頁展開選取字",
        "zh-Hans": "在新标签页展开选中字",
        "ja": "選択字を新規タブで開く",
    },
    "menu_insert_selected_tiles": {
        "en": "Insert Selected in Current Tab",
        "zh-Hant": "插入選取字到目前分頁",
        "zh-Hans": "插入选中字到当前标签页",
        "ja": "選択字を現在タブに挿入",
    },
    "menu_copy_selected_tiles": {
        "en": "Copy Selected Characters",
        "zh-Hant": "複製選取字",
        "zh-Hans": "复制选中字",
        "ja": "選択字をコピー",
    },
    "menu_copy_selected_tile_unicode": {
        "en": "Copy Selected Unicode Values",
        "zh-Hant": "複製選取字 Unicode",
        "zh-Hans": "复制选中字 Unicode",
        "ja": "選択字のUnicodeをコピー",
    },
    "menu_search_selected_tile": {
        "en": "Search First Selected Character",
        "zh-Hant": "搜尋第一個選取字",
        "zh-Hans": "搜索第一个选中字",
        "ja": "先頭の選択字を検索",
    },
    "menu_add_selected_to_favorites": {
        "en": "Add Selected to Favorites",
        "zh-Hant": "將選取字加入收藏",
        "zh-Hans": "将选中字加入收藏",
        "ja": "選択字をお気に入りに追加",
    },
    "menu_remove_selected_from_favorites": {
        "en": "Remove Selected from Favorites",
        "zh-Hant": "從收藏移除選取字",
        "zh-Hans": "从收藏移除选中字",
        "ja": "選択字をお気に入りから削除",
    },
    "summary_inserted_selected_tiles": {
        "en": "Inserted {count} selected character(s): {text}",
        "zh-Hant": "已插入 {count} 個選取字：{text}",
        "zh-Hans": "已插入 {count} 个选中字：{text}",
        "ja": "選択した {count} 文字を挿入しました：{text}",
    },
    "summary_copied_selected_tiles": {
        "en": "Copied {count} selected character(s): {text}",
        "zh-Hant": "已複製 {count} 個選取字：{text}",
        "zh-Hans": "已复制 {count} 个选中字：{text}",
        "ja": "選択した {count} 文字をコピーしました：{text}",
    },
    "summary_copied_unicode": {
        "en": "Copied Unicode values: {text}",
        "zh-Hant": "已複製 Unicode：{text}",
        "zh-Hans": "已复制 Unicode：{text}",
        "ja": "Unicode値をコピーしました：{text}",
    },
    "summary_added_selected_favorites": {
        "en": "Added {count} selected character(s) to favorites.",
        "zh-Hant": "已將 {count} 個選取字加入收藏。",
        "zh-Hans": "已将 {count} 个选中字加入收藏。",
        "ja": "選択した {count} 文字をお気に入りに追加しました。",
    },
    "summary_removed_selected_favorites": {
        "en": "Removed {count} selected character(s) from favorites.",
        "zh-Hant": "已從收藏移除 {count} 個選取字。",
        "zh-Hans": "已从收藏移除 {count} 个选中字。",
        "ja": "選択した {count} 文字をお気に入りから削除しました。",
    },
    "preview_status_line": {
        "en": "{marker} {status} · {glyph}",
        "zh-Hant": "{marker} {status} · {glyph}",
        "zh-Hans": "{marker} {status} · {glyph}",
        "ja": "{marker} {status} · {glyph}",
    },
    "preview_meta_line": {
        "en": "{unicode} · Strokes {strokes}",
        "zh-Hant": "{unicode} · 筆畫 {strokes}",
        "zh-Hans": "{unicode} · 笔画 {strokes}",
        "ja": "{unicode} · 画数 {strokes}",
    },
    "summary_hint": {
        "en": "● Designed / ○ Exists / – Missing. Right-click tiles for actions.",
        "zh-Hant": "● 已完成 / ○ 已存在 / – 未建立。可右鍵操作磁磚。",
        "zh-Hans": "● 已完成 / ○ 已存在 / – 未建立。可右键操作磁贴。",
        "ja": "●制作済み / ○グリフあり / –未作成。タイルは右クリックで操作できます。",
    },
    "summary_hint_color_labels": {
        "en": "Color bar/background = Glyphs color label; neutral ●/○/– = design status. Right-click tiles for actions.",
        "zh-Hant": "色條/底色 = Glyphs 顏色標籤；中性色 ●/○/– = 設計狀態。可右鍵操作磁磚。",
        "zh-Hans": "色条/底色 = Glyphs 颜色标签；中性色 ●/○/– = 设计状态。可右键操作磁贴。",
        "ja": "色バー/背景 = Glyphsカラーラベル、中性色の●/○/– = 制作状態。タイルは右クリックで操作できます。",
    },
    "summary_multi_hint": {
        "en": "Showing characters that contain all selected components.",
        "zh-Hant": "顯示同時包含所有部件的字符。",
        "zh-Hans": "显示同时包含所有部件的字符。",
        "ja": "すべての部品を含む字を表示しています。",
    },
    "summary_copied": {
        "en": "Copied to clipboard.",
        "zh-Hant": "已複製到剪貼簿。",
        "zh-Hans": "已复制到剪贴板。",
        "ja": "クリップボードにコピーしました。",
    },
    "summary_auto_mode": {
        "en": "Auto-follow mode",
        "zh-Hant": "自動跟隨模式",
        "zh-Hans": "自动跟随模式",
        "ja": "自動追従モード",
    },
    "summary_no_focus": {
        "en": "No focus character",
        "zh-Hant": "尚無焦點字",
        "zh-Hans": "暂无焦点字",
        "ja": "フォーカス字なし",
    },
    "summary_strokes": {
        "en": "Strokes",
        "zh-Hant": "筆畫",
        "zh-Hans": "笔画",
        "ja": "画数",
    },
    "summary_charset": {
        "en": "Charset",
        "zh-Hant": "字集",
        "zh-Hans": "字集",
        "ja": "字集合",
    },
    "summary_related_count": {
        "en": "Related",
        "zh-Hant": "相關",
        "zh-Hans": "相关",
        "ja": "関連",
    },
    "summary_favorites_count": {
        "en": "Fav {count}",
        "zh-Hant": "收藏 {count}",
        "zh-Hans": "收藏 {count}",
        "ja": "お気に入り {count}",
    },
    "summary_tile_mode": {
        "en": "View",
        "zh-Hant": "顯示",
        "zh-Hans": "显示",
        "ja": "表示",
    },
    "summary_tile_enabled": {
        "en": "Tile view is on.",
        "zh-Hant": "已切換為磁磚顯示。",
        "zh-Hans": "已切换为磁贴显示。",
        "ja": "タイル表示に切り替えました。",
    },
    "summary_tile_disabled": {
        "en": "Text view is on.",
        "zh-Hant": "已切換為文字顯示。",
        "zh-Hans": "已切换为文字显示。",
        "ja": "テキスト表示に切り替えました。",
    },
    "summary_tile_glyph_preview_enabled": {
        "en": "Tile previews are shown.",
        "zh-Hant": "已顯示磁磚內預覽。",
        "zh-Hans": "已显示磁贴内预览。",
        "ja": "タイル内プレビューを表示します。",
    },
    "summary_tile_glyph_preview_disabled": {
        "en": "Tile previews are hidden.",
        "zh-Hant": "已隱藏磁磚內預覽。",
        "zh-Hans": "已隐藏磁贴内预览。",
        "ja": "タイル内プレビューを非表示にしました。",
    },
    "summary_tile_color_labels_enabled": {
        "en": "Tile color labels are shown.",
        "zh-Hant": "已在磁磚顯示顏色標籤。",
        "zh-Hans": "已在磁贴显示颜色标签。",
        "ja": "タイルにカラーラベルを表示します。",
    },
    "summary_tile_color_labels_disabled": {
        "en": "Tile color labels are hidden; status colors are shown.",
        "zh-Hant": "已隱藏磁磚顏色標籤，改顯示狀態色。",
        "zh-Hans": "已隐藏磁贴颜色标签，改显示状态色。",
        "ja": "カラーラベルを非表示にし、従来の状態色を表示します。",
    },
    "summary_list_preview_enabled": {
        "en": "List badges are shown.",
        "zh-Hant": "已顯示列表標記。",
        "zh-Hans": "已显示列表标记。",
        "ja": "一覧バッジを表示します。",
    },
    "summary_list_preview_disabled": {
        "en": "List badges are hidden.",
        "zh-Hant": "已隱藏列表標記。",
        "zh-Hans": "已隐藏列表标记。",
        "ja": "一覧バッジを非表示にしました。",
    },
    "summary_history_cleared": {
        "en": "Search history cleared.",
        "zh-Hant": "搜尋履歷已清除。",
        "zh-Hans": "搜索历史已清除。",
        "ja": "検索履歴を消去しました。",
    },
    "summary_favorite_added": {
        "en": "Added {char} to favorites.",
        "zh-Hant": "已收藏 {char}。",
        "zh-Hans": "已收藏 {char}。",
        "ja": "{char} をお気に入りに追加しました。",
    },
    "summary_favorite_removed": {
        "en": "Removed {char} from favorites.",
        "zh-Hant": "已取消收藏 {char}。",
        "zh-Hans": "已取消收藏 {char}。",
        "ja": "{char} をお気に入りから削除しました。",
    },
    "summary_favorites_cleared": {
        "en": "Favorites cleared.",
        "zh-Hant": "收藏已清除。",
        "zh-Hans": "收藏已清除。",
        "ja": "お気に入りを消去しました。",
    },
    "summary_chars_copied": {
        "en": "Copied {count} characters only.",
        "zh-Hant": "已只複製 {count} 個字符。",
        "zh-Hans": "已只复制 {count} 个字符。",
        "ja": "字だけを {count} 文字コピーしました。",
    },
    "summary_inserted_all": {
        "en": "Inserted {count} related characters into the current tab.",
        "zh-Hant": "已將 {count} 個相關字插入目前分頁。",
        "zh-Hans": "已将 {count} 个相关字插入当前标签页。",
        "ja": "関連字 {count} 文字を現在のタブに挿入しました。",
    },

    "tooltip_related_double_click": {
        "en": "Select one or more character tiles, then double-click to open them in a new Glyphs tab.",
        "zh-Hant": "選取一個或多個字符磁磚後，雙擊即可在新的 Glyphs 分頁展開。",
        "zh-Hans": "选取一个或多个字符磁贴后，双击即可在新的 Glyphs 标签页展开。",
        "ja": "文字タイルを1つ以上選択してダブルクリックすると、新規Glyphsタブで開きます。",
    },
    "tooltip_related_object_tiles": {
        "en": "Click to select. Shift/Command-click selects more. Double-click opens the selection in a new tab.",
        "zh-Hant": "點擊選取。Shift/Command 點擊可多選。雙擊可在新分頁展開。",
        "zh-Hans": "点击选取。Shift/Command 点击可多选。双击可在新标签页展开。",
        "ja": "クリックで選択、Shift/Commandクリックで複数選択。ダブルクリックで新規タブに開きます。",
    },
    "summary_opened_new_tab": {
        "en": "Opened {count} selected character(s) in a new Glyphs tab: {text}",
        "zh-Hant": "已在新的 Glyphs 分頁展開 {count} 個選取字符：{text}",
        "zh-Hans": "已在新的 Glyphs 标签页展开 {count} 个选取字符：{text}",
        "ja": "選択した {count} 文字を新規Glyphsタブで開きました：{text}",
    },
    "summary_open_new_tab_failed": {
        "en": "Could not open a new Glyphs tab.",
        "zh-Hant": "無法開啟新的 Glyphs 分頁。",
        "zh-Hans": "无法打开新的 Glyphs 标签页。",
        "ja": "新規Glyphsタブを開けませんでした。",
    },
    "summary_no_tile_selection": {
        "en": "Select one or more character tiles, then double-click again.",
        "zh-Hant": "請先選取一個或多個字符磁磚，再雙擊一次。",
        "zh-Hans": "请先选取一个或多个字符磁贴，再双击一次。",
        "ja": "文字タイルを1つ以上選択してから、もう一度ダブルクリックしてください。",
    },
    "tooltip_favorite_on": {
        "en": "{char} is in favorites",
        "zh-Hant": "{char} 已收藏",
        "zh-Hans": "{char} 已收藏",
        "ja": "{char} はお気に入り済み",
    },
    "tooltip_favorite_off": {
        "en": "Add {char} to favorites",
        "zh-Hant": "將 {char} 加入收藏",
        "zh-Hans": "将 {char} 加入收藏",
        "ja": "{char} をお気に入りに追加",
    },
    "preview_designed": {
        "en": "● Designed",
        "zh-Hant": "● 已完成",
        "zh-Hans": "● 已完成",
        "ja": "● 制作済み",
    },
    "preview_empty_glyph": {
        "en": "○ Exists",
        "zh-Hant": "○ 已存在",
        "zh-Hans": "○ 已存在",
        "ja": "○ グリフあり",
    },
    "preview_missing_glyph": {
        "en": "– Missing",
        "zh-Hant": "– 未建立",
        "zh-Hans": "– 未建立",
        "ja": "– 未作成",
    },
    # Refined status / clean UI
    "status_designed": {
        "en": "Designed",
        "zh-Hant": "已設計",
        "zh-Hans": "已设计",
        "ja": "制作済み",
    },
    "status_exists": {
        "en": "Glyph exists",
        "zh-Hant": "有 glyph",
        "zh-Hans": "有 glyph",
        "ja": "グリフあり",
    },
    "status_missing": {
        "en": "Missing",
        "zh-Hant": "缺字",
        "zh-Hans": "缺字",
        "ja": "未作成",
    },
    "summary_tile_on": {
        "en": "Tiles",
        "zh-Hant": "磁磚",
        "zh-Hans": "磁贴",
        "ja": "タイル",
    },
    "summary_tile_off": {
        "en": "Text",
        "zh-Hant": "文字",
        "zh-Hans": "文字",
        "ja": "テキスト",
    },
    "summary_preview_on": {
        "en": "Preview on",
        "zh-Hant": "預覽開",
        "zh-Hans": "预览开",
        "ja": "プレビューあり",
    },
    "summary_preview_off": {
        "en": "Preview off",
        "zh-Hant": "預覽關",
        "zh-Hans": "预览关",
        "ja": "プレビューなし",
    },
    "summary_color_labels_on": {
        "en": "Color labels on",
        "zh-Hant": "顏色標籤開",
        "zh-Hans": "颜色标签开",
        "ja": "カラーラベルあり",
    },
    "summary_color_labels_off": {
        "en": "Status colors",
        "zh-Hant": "狀態色",
        "zh-Hans": "状态色",
        "ja": "状態色",
    },
    "summary_list_preview_on": {
        "en": "Badges on",
        "zh-Hant": "列表標記開",
        "zh-Hans": "列表标记开",
        "ja": "一覧バッジあり",
    },
    "summary_list_preview_off": {
        "en": "Badges off",
        "zh-Hant": "列表標記關",
        "zh-Hans": "列表标记关",
        "ja": "一覧バッジなし",
    },
    "summary_focus_meta": {
        "en": "{unicode}\nStrokes {strokes} · {marker} {status}",
        "zh-Hant": "{unicode}\n筆畫 {strokes} · {marker} {status}",
        "zh-Hans": "{unicode}\n笔画 {strokes} · {marker} {status}",
        "ja": "{unicode}\n画数 {strokes} · {marker} {status}",
    },
    "summary_no_focus_meta": {
        "en": "{noFocus}\n{tileMode}: {tileState}",
        "zh-Hant": "{noFocus}\n{tileMode}: {tileState}",
        "zh-Hans": "{noFocus}\n{tileMode}: {tileState}",
        "ja": "{noFocus}\n{tileMode}: {tileState}",
    },
    "summary_stats_line": {
        "en": "Visible {related} · ●{designed} ○{exists} –{missing} · {progress}%\nCharset {charset} · Favorites {favorites}",
        "zh-Hant": "顯示 {related} · ●{designed} ○{exists} –{missing} · {progress}%\n字集 {charset} · 收藏 {favorites}",
        "zh-Hans": "显示 {related} · ●{designed} ○{exists} –{missing} · {progress}%\n字集 {charset} · 收藏 {favorites}",
        "ja": "表示 {related} · ●{designed} ○{exists} –{missing} · {progress}%\n字集合 {charset} · お気に入り {favorites}",
    },
    "summary_mode_line": {
        "en": "{tile} · {density} · {filter} · {glyphPreview} · {colorLabels}",
        "zh-Hant": "{tile} · {density} · {filter} · {glyphPreview} · {colorLabels}",
        "zh-Hans": "{tile} · {density} · {filter} · {glyphPreview} · {colorLabels}",
        "ja": "{tile} · {density} · {filter} · {glyphPreview} · {colorLabels}",
    },
    "summary_status_line": {
        "en": "Selected {selected} · Total {total} · ★{favorite} · ● designed / ○ exists / – missing",
        "zh-Hant": "已選 {selected} · 總數 {total} · ★{favorite} · ● 已完成 / ○ 已存在 / – 未建立",
        "zh-Hans": "已选 {selected} · 总数 {total} · ★{favorite} · ● 已完成 / ○ 已存在 / – 未建立",
        "ja": "選択 {selected} · 総数 {total} · ★{favorite} · ●制作済み / ○グリフあり / –未作成",
    },
    "summary_status_line_color_labels": {
        "en": "Selected {selected} · Total {total} · ★{favorite} · neutral ● designed / ○ exists / – missing",
        "zh-Hant": "已選 {selected} · 總數 {total} · ★{favorite} · 中性 ● 已完成 / ○ 已存在 / – 未建立",
        "zh-Hans": "已选 {selected} · 总数 {total} · ★{favorite} · 中性 ● 已完成 / ○ 已存在 / – 未建立",
        "ja": "選択 {selected} · 総数 {total} · ★{favorite} · 中性色 ●制作済み / ○グリフあり / –未作成",
    },
    # IDS data source
    "menu_ids_source": {
        "en": "IDS Data",
        "zh-Hant": "IDS 資料",
        "zh-Hans": "IDS 数据",
        "ja": "IDSデータ",
    },
    "ids_source_yibai_lv0": {
        "en": "Yi Bai lv0 (strict glyph form)",
        "zh-Hant": "白易 lv0（嚴格字形）",
        "zh-Hans": "白易 lv0（严格字形）",
        "ja": "白易 lv0（字形を厳密に区別）",
    },
    "ids_source_yibai_lv1": {
        "en": "Yi Bai lv1 (merge stroke variants)",
        "zh-Hant": "白易 lv1（合併筆畫差異）",
        "zh-Hans": "白易 lv1（合并笔画差异）",
        "ja": "白易 lv1（筆画差を統合）",
    },
    "ids_source_yibai_lv2": {
        "en": "Yi Bai lv2 (merge UCV variants)",
        "zh-Hant": "白易 lv2（合併 UCV 差異）",
        "zh-Hans": "白易 lv2（合并 UCV 差异）",
        "ja": "白易 lv2（UCV差も統合）",
    },
    "ids_source_chise": {
        "en": "CHISE (bundled)",
        "zh-Hant": "CHISE（內建）",
        "zh-Hans": "CHISE（内置）",
        "ja": "CHISE（同梱）",
    },
    "ids_variant_regional_form": {
        "en": "Regional form: {sources} ({indicators})",
        "zh-Hant": "地區字形：{sources}（{indicators}）",
        "zh-Hans": "地区字形：{sources}（{indicators}）",
        "ja": "地域字形: {sources}（{indicators}）",
    },
    "ids_variant_shape_note": {
        "en": "Glyph-form note: {indicators}",
        "zh-Hant": "字形注記：{indicators}",
        "zh-Hans": "字形注记：{indicators}",
        "ja": "字形注記: {indicators}",
    },
    "ids_variant_alternative": {
        "en": "alternative IDS",
        "zh-Hant": "替代 IDS",
        "zh-Hans": "替代 IDS",
        "ja": "代替IDS",
    },
    "ids_variant_source_default": {
        "en": "China (G form)",
        "zh-Hant": "中國（G 形）",
        "zh-Hans": "中国（G 形）",
        "ja": "中国（G系）",
    },
    "ids_variant_source_g": {
        "en": "China",
        "zh-Hant": "中國",
        "zh-Hans": "中国",
        "ja": "中国",
    },
    "ids_variant_source_h": {
        "en": "Hong Kong form",
        "zh-Hant": "香港形",
        "zh-Hans": "香港形",
        "ja": "香港系",
    },
    "ids_variant_source_j": {
        "en": "Japan form",
        "zh-Hant": "日本形",
        "zh-Hans": "日本形",
        "ja": "日本字形",
    },
    "ids_variant_source_k": {
        "en": "Korea form",
        "zh-Hant": "韓國形",
        "zh-Hans": "韩国形",
        "ja": "韓国字形",
    },
    "ids_variant_source_kp": {
        "en": "North Korea form",
        "zh-Hant": "北韓形",
        "zh-Hans": "朝鲜形",
        "ja": "北朝鮮字形",
    },
    "ids_variant_source_m": {
        "en": "Macao form",
        "zh-Hant": "澳門形",
        "zh-Hans": "澳门形",
        "ja": "マカオ字形",
    },
    "ids_variant_source_t": {
        "en": "Taiwan form",
        "zh-Hant": "臺灣形",
        "zh-Hans": "台湾形",
        "ja": "台湾字形",
    },
    "ids_variant_source_u": {
        "en": "US form",
        "zh-Hant": "美國形",
        "zh-Hans": "美国形",
        "ja": "米国字形",
    },
    "ids_variant_source_v": {
        "en": "Vietnam form",
        "zh-Hant": "越南形",
        "zh-Hans": "越南形",
        "ja": "ベトナム字形",
    },
    "summary_ids_source_changed": {
        "en": "IDS data source: {source}",
        "zh-Hant": "IDS 資料源：{source}",
        "zh-Hans": "IDS 数据源：{source}",
        "ja": "IDSデータを {source} に切り替えました。",
    },
    "summary_ids_source_fallback": {
        "en": "{source} could not be loaded; using bundled CHISE IDS.",
        "zh-Hant": "無法載入 {source}，已改用內建 CHISE IDS。",
        "zh-Hans": "无法载入 {source}，已改用内置 CHISE IDS。",
        "ja": "{source} を読み込めなかったため、同梱CHISE IDSを使用しています。",
    },
}



def L(key):
    """
    取得本地化字串

    參數:
        key (str): 字串鍵名

    回傳:
        str: 本地化後的字串，如果找不到則返回鍵名本身
    """
    try:
        from GlyphsApp import Glyphs

        return Glyphs.localize(STRINGS.get(key, {"en": key}))
    except Exception:
        # 測試環境 fallback：使用英文
        # 捕捉 ImportError 和 objc.nosuchclass_error 等
        return STRINGS.get(key, {"en": key}).get("en", key)


# === 測試程式碼 ===

if __name__ == "__main__":
    """測試本地化模組"""
    print("=== 本地化模組測試 ===\n")

    for key in STRINGS:
        value = L(key)
        print(f"{key}: {value}")

    print("\n=== 測試完成 ===")
