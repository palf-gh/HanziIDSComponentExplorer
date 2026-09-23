[中文](#中文) | [English](#english) | [日本語](#日本語)

---

# 中文

# 漢字部件查詢 RS+

[Glyphs](https://glyphsapp.com/) 字型編輯器外掛，用於拆解漢字 IDS 結構、查詢相關字符，並在 Glyphs 目前開啟的字型檔中確認製作狀態。

<p align="center">
  <img src="screenshot.png" alt="漢字部件查詢 RS+截圖" width="500">
</p>

## 專案沿革與上游同步

此專案是 **fork 的 fork**，沿革如下：

```text
yintzuyuan/HanziIDSComponentExplorer
  → 0oma/HanziIDSComponentExplorer（漢字部件查詢 RS+）
  → palf-gh/HanziIDSComponentExplorer（目前儲存庫）
```

RS+ 保留原專案的 IDS 搜尋核心，並為 Glyphs 的實際製作流程加入日文介面、字磚、製作狀態、Yi Bai 字形資料與區域字形標記。上游功能會在確認能與 RS+ 的 UI、資料來源及授權共存後手動移植；不直接合併上游分支，以避免覆蓋 RS+ 的變更。

## 主要功能

- **漢字拆解** — 顯示漢字的 IDS 部件結構，支援簡潔的連線式樹狀圖。
- **多部件搜尋** — 輸入多個部件，例如「氵木」，找出同時包含這些部件的字。搜尋會遞迴比對深層部件，也支援可再拆的中間部件，例如「立里」可找到「童」。
- **相關字查詢** — 顯示同結構字、衍生字，以及和目前字符相關的其他字符。
- **Yi Bai 字形資料與地區字形** — 可在嚴格字形（lv0）、筆畫差統合（lv1）、Unicode 統合差（lv2）與 CHISE 之間切換；同字的多個地域字形可分頁檢視並標記來源。
- **字集篩選** — 可限制結果只顯示目前字型檔中的字符，或使用自訂字集。
- **製作狀態顯示** — 在列表與右側字磚中標示目前字型檔內的狀態：`●` 已製作、`○` 已有 glyph 但尚未製作、`–` 未建立、`★` 收藏。
- **自動折行字磚** — 右側相關字以字磚顯示，會依視窗寬度自動換行。
- **字磚操作** — 支援單選、多選、雙擊開啟新分頁、右鍵選單、複製、插入目前分頁、Unicode 複製與收藏。
- **Glyphs 預覽** — 若目前字型檔已有實際內容，可在左側或字磚內顯示該 glyph 的預覽。
- **只顯示已製作字符** — 可只顯示已完成內容的字符，方便檢查或整理進度。
- **筆畫數篩選** — 可依 CNS11643 筆畫資料，以目前字符或多部件總筆畫為基準縮小結果範圍。
- **搜尋履歷與收藏** — 可重複使用最近搜尋，並把常用字符加入收藏。
- **CNS11643 連結** — 可快速開啟全字庫查詢頁面。

## 安裝

### 手動安裝

1. 下載 `HanziComponentExplorerRSplus.glyphsPlugin`。
2. 雙擊外掛檔案進行安裝。
3. 重新啟動 Glyphs。
4. 從 *視窗 > 漢字部件查詢 RS+* 開啟。

### 外掛程式管理員

若此外掛已加入 Glyphs 外掛程式管理員，可從 *視窗 > 外掛程式管理員* 搜尋並安裝。

## 使用方式

1. 開啟 *視窗 > 漢字部件查詢 RS+*。
2. 在搜尋欄輸入漢字，例如「森」，或輸入 Unicode，例如「68EE」。
3. 左側查看目前字符與製作狀態，中間查看 IDS 樹狀拆解，右側查看相關字磚。
4. 輸入多個部件，例如「氵木」，即可搜尋同時包含所有部件的字符。
5. 在右側字磚中選取一個或多個字符，雙擊可在 Glyphs 新分頁開啟；右鍵可使用複製、插入、收藏等操作。

## 系統需求

- Glyphs 3.0 或以上
- macOS 10.9 或以上

## 資料來源

- **Yi Bai IDS** — [yi-bai/ids](https://github.com/yi-bai/ids) 的 lv0、lv1、lv2 資料，採 MIT License，隨外掛同梱。
- **CHISE IDS** — [CHISE IDS database](https://www.chise.org/ids/) 的 CNS 與 Unicode 資料，作為可切換資料來源與畫數補完來源。
- **筆畫數資料** — [CNS11643-OpenData](https://github.com/yintzuyuan/CNS11643-OpenData) 的 `Tables/Properties/CNS_stroke.txt`。

## 授權

程式碼以 [Apache License 2.0](LICENSE) 授權。

本儲存庫是 **yintzuyuan → 0oma → palf-gh** 的第二層 fork；原始著作權歸 **殷慈遠 TzuYuan Yin** 所有，RS+ 修改部分 © 2026 [Ooma Kobayashi](https://ooma.jp)，此儲存庫的後續修改由 palf-gh 維護。依 Apache License 2.0 第 4 條，已保留原始權利與出處標示，並在 [NOTICE](NOTICE) 中標明本 fork 可能包含修改。

本外掛內含的 `ids.pdata` 為 [CHISE IDS](https://www.chise.org/ids/) 衍生資料，受 [GPL-2.0-or-later](LICENSES/GPL-2.0-or-later.txt) 約束。CNS11643 資料依[政府資料開放授權條款](https://data.gov.tw/license)使用。

詳見 [NOTICE](NOTICE)。

## 作者與致謝

原作者：**殷慈遠 TzuYuan Yin** — [erikyin.net](https://erikyin.net)

本 fork 包含 2026 年 [Ooma Kobayashi](https://ooma.jp) 的修改。

感謝 [CHISE Project](https://www.chise.org/)、[全字庫](https://www.cns11643.gov.tw/) 與 [3type/EOD](https://github.com/3type/EOD)。

---

# English

# Hanzi Component Explorer RS+

A [Glyphs](https://glyphsapp.com/) plugin for decomposing Hanzi IDS structures, exploring related characters, and checking production status in the currently open Glyphs font.

<p align="center">
  <img src="screenshot.png" alt="Hanzi Component Explorer RS+ screenshot" width="500">
</p>

## Project lineage and upstream policy

This is a **fork of a fork**:

```text
yintzuyuan/HanziIDSComponentExplorer
  → 0oma/HanziIDSComponentExplorer (Hanzi Component Explorer RS+)
  → palf-gh/HanziIDSComponentExplorer (this repository)
```

RS+ retains the original IDS-search core and adds a Japanese interface, character tiles, production-status tools, Yi Bai shape data, and regional-form annotations for Glyphs production work. Upstream features are ported manually after they are checked against the RS+ UI, data sources, and licenses. The upstream branch is not merged directly because that could overwrite RS+-specific work.

## Features

- **Character decomposition** — View IDS component structures with a compact connected tree display.
- **Multi-component search** — Enter components such as “氵木” to find characters that contain all of them. Matching is recursive, so nested components count; decomposable intermediate components also work, for example “立里” can find “童”.
- **Related character lookup** — Browse characters with the same structure, derived characters, and other characters related to the current glyph.
- **Yi Bai shape data and regional forms** — Switch among strict-shape lv0, stroke-normalized lv1, Unicode-normalized lv2, and CHISE. Multiple regional forms for one character are paged and annotated.
- **Charset filtering** — Limit results to the current font or use a custom character set.
- **Production status** — Lists and tiles show the current font status: `●` designed, `○` glyph exists but is empty, `–` missing, and `★` favorite.
- **Responsive character tiles** — Related characters are shown as tiles that wrap automatically to the window width.
- **Tile actions** — Select one or more tiles, double-click to open them in a new Glyphs tab, or use the context menu to copy, insert, copy Unicode, search, or favorite them.
- **Glyph previews** — When the current font already contains outlines or components, the plugin can show a preview in the left pane and, optionally, inside tiles.
- **Designed-only filter** — Show only characters that already have glyph content in the current font.
- **Stroke count filtering** — Narrow related results using CNS11643 stroke-count data, based on the current character or the total stroke count of a multi-component query.
- **Search history and favorites** — Reuse recent searches and keep frequently used characters as favorites.
- **CNS11643 lookup** — Open the corresponding CNS11643 reference page quickly.

## Installation

### Manual installation

1. Download `HanziComponentExplorerRSplus.glyphsPlugin`.
2. Double-click the plugin file to install it.
3. Restart Glyphs.
4. Open it from *Window > Hanzi Component Explorer RS+*.

### Plugin Manager

If the plugin is available in Glyphs Plugin Manager, install it from *Window > Plugin Manager*.

## Usage

1. Open *Window > Hanzi Component Explorer RS+*.
2. Enter a Hanzi character, such as “森”, or a Unicode value, such as “68EE”.
3. Use the left pane for the current character and production status, the middle pane for IDS decomposition, and the right pane for related character tiles.
4. Enter multiple components, such as “氵木”, to find characters containing all of them.
5. Select one or more right-side tiles and double-click to open them in a new Glyphs tab. Right-click for copy, insert, Unicode, search, and favorite actions.

## Requirements

- Glyphs 3.0 or later
- macOS 10.9 or later

## Data sources

- **Yi Bai IDS** — lv0, lv1, and lv2 data from [yi-bai/ids](https://github.com/yi-bai/ids), bundled under its MIT License.
- **CHISE IDS** — CNS and Unicode data from the [CHISE IDS database](https://www.chise.org/ids/), available as a selectable source and used to supplement stroke counts.
- **Stroke-count data** — `Tables/Properties/CNS_stroke.txt` from [CNS11643-OpenData](https://github.com/yintzuyuan/CNS11643-OpenData).

## License

Source code is licensed under the [Apache License 2.0](LICENSE).

This repository is a second-level fork: **yintzuyuan → 0oma → palf-gh**. Original copyright remains with **TzuYuan Yin**; RS+ modifications are © 2026 [Ooma Kobayashi](https://ooma.jp), and subsequent changes are maintained by palf-gh. In accordance with Apache License 2.0 section 4, original rights and attribution notices are retained, and [NOTICE](NOTICE) states that this fork may contain modified files.

The bundled `ids.pdata` is derived from the [CHISE IDS](https://www.chise.org/ids/) database and is subject to [GPL-2.0-or-later](LICENSES/GPL-2.0-or-later.txt). CNS11643 data is used under the [Open Government Data License, Taiwan](https://data.gov.tw/license).

See [NOTICE](NOTICE) for details.

## Author and acknowledgments

Original author: **TzuYuan Yin** — [erikyin.net](https://erikyin.net)

This fork includes modifications made in 2026 by [Ooma Kobayashi](https://ooma.jp).

Thanks to the [CHISE Project](https://www.chise.org/), [CNS11643](https://www.cns11643.gov.tw/), and [3type/EOD](https://github.com/3type/EOD).

---

# 日本語

# 漢字部品検索 RS+

[Glyphs](https://glyphsapp.com/) 用のプラグインです。漢字の IDS 構造を分解し、関連字を検索しながら、現在開いている Glyphs フォント内での制作状況を確認できます。

<p align="center">
  <img src="screenshot.png" alt="漢字部品検索 RS+のスクリーンショット" width="500">
</p>

## フォークの系譜と上流同期

このリポジトリは **フォークのフォーク**です。系譜は次のとおりです。

```text
yintzuyuan/HanziIDSComponentExplorer
  → 0oma/HanziIDSComponentExplorer（漢字部品検索 RS+）
  → palf-gh/HanziIDSComponentExplorer（このリポジトリ）
```

RS+ は元の IDS 検索コアを維持しつつ、日本語UI、字形タイル、制作状況、Yi Bai の字形データ、地域字形の注記を Glyphs での制作向けに加えています。上流の機能は RS+ のUI・データソース・ライセンスと両立することを確認してから手動で移植します。RS+固有の変更を上書きしないため、上流ブランチをそのままマージする方針は取りません。

## 主な機能

- **漢字の分解表示** — IDS に基づく部品構造を、コンパクトな接続型ツリーで表示します。
- **複数部品検索** — 「氵木」のように複数の部品を入力し、それらをすべて含む字を検索できます。深い階層にある部品も対象になり、「立里」から「童」を見つけるような中間部品検索にも対応します。
- **関連字の検索** — 同じ構造の字、現在の字を部品として含む派生字、そのほか構造的に関連する字を確認できます。
- **Yi Bai字形データと地域字形** — 厳密字形のlv0、筆画差を統合するlv1、Unicode統合差を吸収するlv2、CHISEを切り替えられます。同じ字の複数の地域字形はページ切替で確認でき、出典注記も表示されます。
- **字集合フィルター** — 現在のフォントに含まれる字、または任意のカスタム字集合に結果を絞り込めます。
- **制作状況の表示** — 一覧とタイルに、現在のフォント内での状態を表示します：`●` 制作済み、`○` glyph はあるが未制作、`–` 未作成、`★` お気に入り。
- **自動折り返しタイル** — 右ペインの関連字をタイルで表示し、ウィンドウ幅に合わせて自動で折り返します。
- **タイル操作** — 単体選択・複数選択・ダブルクリックでの新規タブ展開・右クリックメニュー・コピー・挿入・Unicodeコピー・お気に入り登録に対応します。
- **Glyphsプレビュー** — 現在のフォントにアウトラインやコンポーネントがある場合、左ペインやタイル内に実際の glyph プレビューを表示できます。
- **制作済みのみ表示** — 現在のフォントで制作済みの字だけを表示できます。
- **画数フィルター** — CNS11643 の画数データを使い、現在字または複数部品検索時の合計画数を基準に結果を絞り込めます。
- **検索履歴とお気に入り** — 最近の検索を再利用し、よく使う字をお気に入りとして保存できます。
- **CNS11643 連携** — 対応する全字庫ページをすばやく開けます。

## インストール

### 手動インストール

1. `HanziComponentExplorerRSplus.glyphsPlugin` をダウンロードします。
2. プラグインファイルをダブルクリックしてインストールします。
3. Glyphs を再起動します。
4. *ウィンドウ > 漢字部品検索 RS+* から開きます。

### プラグインマネージャー

Glyphs のプラグインマネージャーに登録されている場合は、*ウィンドウ > プラグインマネージャー* から検索してインストールできます。

## 使い方

1. *ウィンドウ > 漢字部品検索 RS+* を開きます。
2. 「森」のような漢字、または「68EE」のような Unicode を検索欄に入力します。
3. 左ペインで現在字と制作状況、中ペインで IDS 分解、右ペインで関連字タイルを確認します。
4. 「氵木」のように複数部品を入力すると、それらをすべて含む字を検索できます。
5. 右ペインのタイルを1つまたは複数選択し、ダブルクリックすると Glyphs の新規タブで開きます。右クリックからコピー、挿入、Unicodeコピー、検索、お気に入り操作もできます。

## 動作環境

- Glyphs 3.0 以降
- macOS 10.9 以降

## データソース

- **Yi Bai IDS** — [yi-bai/ids](https://github.com/yi-bai/ids) の lv0・lv1・lv2データ。MIT Licenseに基づき同梱しています。
- **CHISE IDS** — [CHISE IDS database](https://www.chise.org/ids/) のCNSおよびUnicodeデータ。切替可能なデータソースとして利用し、画数情報の補完にも使います。
- **画数データ** — [CNS11643-OpenData](https://github.com/yintzuyuan/CNS11643-OpenData) の `Tables/Properties/CNS_stroke.txt`。

## ライセンス

ソースコードは [Apache License 2.0](LICENSE) でライセンスされています。

本リポジトリは **yintzuyuan → 0oma → palf-gh** と続く第2層のフォークです。原著作権は **TzuYuan Yin / 殷慈遠** に帰属し、RS+の変更部分は © 2026 [Ooma Kobayashi](https://ooma.jp)、以降の変更は palf-gh が保守します。Apache License 2.0 第 4 条に従い、原著作権表示・出所表示を保持し、[NOTICE](NOTICE) に本 fork が変更済みファイルを含み得ることを明記しています。

同梱の `ids.pdata` は [CHISE IDS](https://www.chise.org/ids/) 由来のデータで、[GPL-2.0-or-later](LICENSES/GPL-2.0-or-later.txt) の対象です。CNS11643 データは [台湾政府資料開放授權條款](https://data.gov.tw/license) に基づいて使用しています。

詳しくは [NOTICE](NOTICE) を参照してください。

## 作者・謝辞

原作者：**TzuYuan Yin / 殷慈遠** — [erikyin.net](https://erikyin.net)

本リポジトリには 2026 年の [Ooma Kobayashi](https://ooma.jp) によるRS+の変更と、palf-gh による継続的な保守・上流移植が含まれます。

[CHISE Project](https://www.chise.org/)、[全字庫 CNS11643](https://www.cns11643.gov.tw/)、[3type/EOD](https://github.com/3type/EOD) に感謝します。

---

Original copyright 2026 TzuYuan Yin; fork modifications copyright 2026 Ooma Kobayashi
