---
name: video-downloader
description: 下載線上影片（YouTube 與其他平台），以 yt-dlp/ffmpeg 進行格式選擇、字幕與播放清單處理；在符合平台條款與版權下操作。
version: 0.1.0
metadata:
  short-description: 影片下載（YouTube 與其他平台）
---

# Video Downloader（zh-tw）

## Overview
下載線上影片（YouTube 與其他平台），以 yt-dlp/ffmpeg 進行格式選擇、字幕與播放清單處理。在符合平台條款與版權下操作。

## 使用時機
當使用者要求下載線上影片（YouTube 或其他平台）、需要最佳畫質/音質、字幕、播放清單、或批次下載時使用此技能。

## 核心原則
- **合規優先**：確認下載行為符合平台服務條款與版權授權；不得繞過 DRM、付費牆或其他技術保護。
- **先問清楚需求**：品質/格式、是否需要字幕、輸出目錄與檔名規則、是否為播放清單或多支影片。
- **使用 yt-dlp**：作為主要下載工具；必要時搭配 `ffmpeg` 進行合併與轉檔。

## Workflow
1. 確認授權與用途（合法性/授權）。
2. 蒐集下載需求：URL、輸出路徑、畫質/音質、字幕語言、是否為播放清單。
3. 檢查工具：`yt-dlp --version`、`ffmpeg -version`。
4. 生成指令並執行；若失敗，依錯誤訊息調整。
5. 驗證輸出（檔案存在、可播放、字幕正確）。

## 必要前置
- `yt-dlp`（主要下載器）
- `ffmpeg`（多數平台需要合併音訊/視訊）

## 指令模板
### 基本下載（單一影片）
```bash
yt-dlp -o "%(title)s.%(ext)s" "<URL>"
```

### 指定最佳品質（建議）
```bash
yt-dlp -f "bv*+ba/b" -o "%(title)s.%(ext)s" "<URL>"
```

### 指定輸出資料夾與檔名規則
```bash
yt-dlp -P "<輸出資料夾>" -o "%(uploader)s/%(title)s.%(ext)s" "<URL>"
```

### 只下載音訊（例如 mp3）
```bash
yt-dlp -x --audio-format mp3 -o "%(title)s.%(ext)s" "<URL>"
```

## 字幕
### 下載自動或人工字幕
```bash
yt-dlp --write-sub --sub-lang "zh-TW,zh-Hant,zh" --sub-format "vtt" "<URL>"
```

### 內嵌字幕（需 ffmpeg）
```bash
yt-dlp --embed-subs --sub-lang "zh-TW,zh-Hant,zh" "<URL>"
```

## 播放清單 / 頻道
```bash
yt-dlp -o "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s" "<播放清單URL>"
```

## 需要登入或受限內容
- 若平台允許且使用者具備授權帳號，可使用 cookies 或瀏覽器匯入：
```bash
yt-dlp --cookies-from-browser chrome "<URL>"
```
- **不得**協助繞過付費牆或 DRM。

## Error Handling / 常見問題排查
- **403/429 或地區限制**：確認是否需要登入、是否有地區限制；詢問使用者是否能提供合法 cookies。
- **格式不存在**：先列出可用格式：
```bash
yt-dlp -F "<URL>"
```
- **合併失敗**：檢查 `ffmpeg` 是否安裝與可用。

## 參考資料（按需閱讀）
- `references/format-selection.md`：格式選擇與排序的常用範例。
- `references/naming-templates.md`：輸出命名模板與常見欄位。
- `references/platform-notes.md`：平台常見限制與合規提醒。

## 腳本（可直接使用）
- `scripts/check_tools.sh`：檢查 `yt-dlp` 與 `ffmpeg` 是否可用。
- `scripts/download.sh`：標準化下載流程（格式/字幕/音訊/播放清單選項；預設輸出 mp4/H.264/AAC 到 `/Users/jeff/Downloads/`，會進行重新編碼並清理暫存/原始容器檔）。
- `scripts/cleanup_temp.sh`：清理由下載產生的暫存檔（`download.sh` 會自動呼叫；預設也會移除同名的 webm/mkv）。
- `scripts/install_ffmpeg.sh`：安裝 `ffmpeg`（macOS、Debian/Ubuntu、RHEL/Fedora、Windows）。
- `scripts/install_yt-dlp.sh`：安裝 `yt-dlp`（macOS、Debian/Ubuntu、RHEL/Fedora、Windows）。

## 驗證輸出
- 檢查檔案是否存在、大小合理、可播放。
- 若為字幕，確認語言與時間軸正確。

## 需要向使用者確認的資訊
- 影片 URL（單一/多個/播放清單）
- 目標畫質或檔案大小限制
- 輸出路徑與命名規則
- 是否需要字幕、語言偏好
- 是否需要音訊檔/指定格式
- 是否需要登入（合法授權）
