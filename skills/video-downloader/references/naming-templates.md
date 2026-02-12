# 命名與輸出模板

## 常用模板
- 影片標題
  ```bash
  -o "%(title)s.%(ext)s"
  ```
- 依上傳者分類
  ```bash
  -o "%(uploader)s/%(title)s.%(ext)s"
  ```
- 播放清單
  ```bash
  -o "%(playlist)s/%(playlist_index)02d - %(title)s.%(ext)s"
  ```

## 常見欄位
- `%(title)s`、`%(uploader)s`、`%(id)s`、`%(ext)s`
- `%(upload_date)s`（YYYYMMDD）
- `%(playlist)s`、`%(playlist_index)s`

## 檔名相容性
- 需要避免特殊字元時可加：
  ```bash
  --restrict-filenames
  ```
- Windows 相容檔名：
  ```bash
  --windows-filenames
  ```
