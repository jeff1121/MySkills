"""
VirusTotal API v3 用戶端封裝。

以 `requests` 封裝掃描檔案 / URL 與查詢 file / domain / IP 報告的常用端點，
並提供分析輪詢、統一的錯誤處理與 429 退避重試。所有對外錯誤皆繼承自 `VTError`，
方便呼叫端一次攔截。
"""

from __future__ import annotations

import base64
import os
import time

import requests
from config import API_BASE_URL, LARGE_FILE_THRESHOLD, POLL_INTERVAL, POLL_TIMEOUT

__version__ = "0.1.0"


class VTError(Exception):
    """VirusTotal 用戶端錯誤基底類別。"""


class VTAuthError(VTError):
    """API 金鑰無效或未授權（HTTP 401）。請檢查 VT_API_KEY 是否正確。"""


class VTRateLimitError(VTError):
    """超過 VirusTotal API 使用額度（HTTP 429），且重試次數已用盡。"""


class VTNotFoundError(VTError):
    """找不到資源（HTTP 404），例如尚未被分析過的 hash。"""


class VTTimeoutError(VTError):
    """輪詢分析結果逾時。"""


class VTNetworkError(VTError):
    """網路連線層錯誤（連線失敗、逾時、Proxy 錯誤等）。"""


class VTApiError(VTError):
    """其他 HTTP 或回應解析錯誤。"""


class VirusTotalClient:
    """VirusTotal API v3 用戶端。

    封裝檔案 / URL 送掃、分析輪詢與 file / domain / IP 報告查詢。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = API_BASE_URL,
        session: requests.Session | None = None,
        max_retries: int = 3,
    ) -> None:
        """初始化用戶端。

        Args:
            api_key: VirusTotal API 金鑰。
            base_url: API 基底位址，預設為 config.API_BASE_URL。
            session: 可注入的 `requests.Session`（測試用）；未提供時自動建立。
            max_retries: 遇到 429 時的最大退避重試次數。
        """
        self.base_url = base_url
        self.max_retries = max_retries
        self.session = session or requests.Session()
        # 設定預設標頭；使用 update 以保留注入 session 既有的其他標頭。
        self.session.headers.update({"x-apikey": api_key, "accept": "application/json"})
        # 可注入的時間函式，讓測試不必真的等待或依賴真實時鐘。
        self._sleep = time.sleep
        self._clock = time.monotonic

    @staticmethod
    def url_to_id(url: str) -> str:
        """將 URL 轉為 VirusTotal 使用的 base64url 識別碼（去除 `=` padding）。"""
        return base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")

    def _request(self, method: str, path: str, *, absolute: bool = False, **kwargs) -> dict:
        """對 VirusTotal API 發出請求，並統一處理錯誤與 429 退避重試。

        Args:
            method: HTTP 方法（GET / POST 等）。
            path: 相對路徑；當 `absolute=True` 時視為完整網址（大檔上傳網址用）。
            absolute: `path` 是否為完整網址。
            **kwargs: 傳遞給 `requests` 的其他參數（params / data / files 等）。

        Returns:
            解析後的 JSON dict。

        Raises:
            VTAuthError: HTTP 401。
            VTNotFoundError: HTTP 404。
            VTRateLimitError: HTTP 429 且重試次數用盡。
            VTNetworkError: 連線失敗、逾時或 Proxy 錯誤等網路層問題。
            VTApiError: 其他 >=400 狀態碼或 JSON 解析失敗。
        """
        url = path if absolute else f"{self.base_url}/{path.lstrip('/')}"
        attempt = 0
        while True:
            try:
                response = self.session.request(method, url, timeout=60, **kwargs)
            except requests.RequestException as exc:
                # 連線、逾時、Proxy 等網路層錯誤：包裝為 VTError 供上層一致攜截。
                raise VTNetworkError(f"連線 VirusTotal 失敗：{exc}") from exc
            status = response.status_code

            if status == 401:
                raise VTAuthError("API 金鑰無效或未授權（401）。請確認 VT_API_KEY 設定是否正確。")
            if status == 404:
                raise VTNotFoundError(f"找不到資源（404）：{url}")
            if status == 429:
                # 超過額度：依 Retry-After 或指數退避後重試，仍失敗才丟出例外。
                if attempt >= self.max_retries:
                    raise VTRateLimitError("超過 VirusTotal API 使用額度（429），重試次數已用盡。")
                self._sleep(self._retry_after_seconds(response, attempt))
                attempt += 1
                continue
            if status >= 400:
                raise VTApiError(f"VirusTotal API 回應錯誤（{status}）：{response.text}")

            try:
                return response.json()
            except ValueError as exc:  # 含 json.JSONDecodeError；回應非合法 JSON。
                raise VTApiError(f"無法解析 VirusTotal 回應為 JSON：{exc}") from exc

    def _retry_after_seconds(self, response: requests.Response, attempt: int) -> float:
        """計算 429 的退避秒數。

        優先採用 `Retry-After` 標頭（整數秒）；缺少或非數值時，改用指數退避 2**attempt 秒
        （attempt 從 0 起算，即 1、2、4、…）。
        """
        retry_after = response.headers.get("Retry-After")
        if retry_after is not None and str(retry_after).strip().isdigit():
            return float(retry_after)
        return float(2**attempt)

    def scan_file(self, path: str) -> str:
        """上傳檔案送掃並回傳分析 id。

        小於門檻的檔案直接 `POST /files`；達到 `LARGE_FILE_THRESHOLD`（32MB）以上者，
        先向 `/files/upload_url` 取得專用上傳網址，再對該網址上傳。全程以
        `with open(...)` 確保檔案關閉。
        """
        size = os.path.getsize(path)
        if size >= LARGE_FILE_THRESHOLD:
            # 大檔：先取得專用上傳網址，再對該（絕對）網址上傳。
            upload_url = self._request("GET", "/files/upload_url")["data"]
            with open(path, "rb") as fh:
                resp = self._request("POST", upload_url, absolute=True, files={"file": fh})
        else:
            # 小檔：直接上傳至 /files。
            with open(path, "rb") as fh:
                resp = self._request("POST", "/files", files={"file": fh})
        return resp["data"]["id"]

    def scan_url(self, url: str) -> str:
        """提交 URL 送掃並回傳分析 id。"""
        resp = self._request("POST", "/urls", data={"url": url})
        return resp["data"]["id"]

    def get_analysis(self, analysis_id: str) -> dict:
        """取得分析結果（GET /analyses/{analysis_id}）。"""
        return self._request("GET", f"/analyses/{analysis_id}")

    def wait_for_analysis(
        self,
        analysis_id: str,
        interval: int = POLL_INTERVAL,
        timeout: int = POLL_TIMEOUT,
    ) -> dict:
        """輪詢分析直到完成並回傳整包結果。

        重複呼叫 `get_analysis`，直到 `data.attributes.status == "completed"` 為止；
        每輪之間等待 `interval` 秒。超過 `timeout` 秒仍未完成則丟出 `VTTimeoutError`。
        """
        deadline = self._clock() + timeout
        while True:
            result = self.get_analysis(analysis_id)
            status = result.get("data", {}).get("attributes", {}).get("status")
            if status == "completed":
                return result
            if self._clock() >= deadline:
                raise VTTimeoutError(f"等待分析 {analysis_id} 完成逾時（{timeout} 秒）。")
            self._sleep(interval)

    def get_file(self, file_hash: str) -> dict:
        """取得檔案報告（GET /files/{file_hash}）。"""
        return self._request("GET", f"/files/{file_hash}")

    def get_domain(self, domain: str) -> dict:
        """取得網域報告（GET /domains/{domain}）。"""
        return self._request("GET", f"/domains/{domain}")

    def get_ip(self, ip: str) -> dict:
        """取得 IP 報告（GET /ip_addresses/{ip}）。"""
        return self._request("GET", f"/ip_addresses/{ip}")
