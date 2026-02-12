# 平台注意事項（通用）

## 合規與限制
- 僅在平台條款與授權允許下下載。
- 不得協助繞過 DRM、付費牆或任何技術保護。

## 登入/年齡/地區限制
- 若平台允許且使用者具備授權，可使用 cookies。
  ```bash
  --cookies-from-browser chrome
  ```
- 若遇到 403/429 等限制，先確認是否需要登入或權限。

## 播放清單與批次
- 預設可能會下載整個播放清單；需要單一影片時可加 `--no-playlist`。

## 下載穩定性
- 針對大型播放清單，建議加入重試：
  ```bash
  --retries 5 --fragment-retries 5
  ```
- 若平台限制頻率，可加入睡眠：
  ```bash
  --sleep-interval 2 --max-sleep-interval 5
  ```
