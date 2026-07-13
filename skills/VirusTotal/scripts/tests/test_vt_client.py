"""
`vt_client.VirusTotalClient` 單元測試。

全程以 `unittest.mock` 注入假的 session / response，絕不實際連網。
測試檔開頭不需自行處理 sys.path（由 tests/conftest.py 負責）。
"""

from __future__ import annotations

import base64
from unittest.mock import MagicMock, patch

import pytest
import requests
from config import LARGE_FILE_THRESHOLD
from vt_client import (
    VirusTotalClient,
    VTApiError,
    VTAuthError,
    VTNetworkError,
    VTNotFoundError,
    VTTimeoutError,
)


def make_response(
    status_code: int = 200,
    json_data: dict | None = None,
    headers: dict | None = None,
    text: str = "",
) -> MagicMock:
    """建立假的 `requests.Response`。

    Args:
        status_code: HTTP 狀態碼。
        json_data: `response.json()` 的回傳值。
        headers: 回應標頭（例如 Retry-After）。
        text: `response.text` 內容（錯誤訊息用）。
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = text
    resp.json.return_value = json_data
    return resp


class TestUrlToId:
    """`url_to_id` 測試。"""

    def test_no_padding_and_reversible(self) -> None:
        """轉出的 base64url 無 `=` padding，且補回 padding 後可還原成原始 URL。"""
        url = "http://www.google.com/"
        vt_id = VirusTotalClient.url_to_id(url)

        assert "=" not in vt_id
        # 依 VirusTotal 慣例補回 padding 後還原
        decoded = base64.urlsafe_b64decode(vt_id + "==").decode()
        assert decoded == url


class TestScanUrl:
    """`scan_url` 測試。"""

    def test_returns_analysis_id_with_correct_request(self) -> None:
        """回傳分析 id，且以正確的方法與 URL 呼叫 API。"""
        session = MagicMock()
        session.request.return_value = make_response(200, {"data": {"id": "abc-123"}})
        client = VirusTotalClient("fake-key", session=session)

        result = client.scan_url("http://example.com")

        assert result == "abc-123"
        session.request.assert_called_once()
        call = session.request.call_args
        assert call.args == ("POST", "https://www.virustotal.com/api/v3/urls")
        assert call.kwargs["data"] == {"url": "http://example.com"}
        assert call.kwargs["timeout"] == 60


class TestRequestStatusCodes:
    """`_request` 的狀態碼錯誤對應測試。"""

    def test_401_raises_auth_error(self) -> None:
        """HTTP 401 → VTAuthError。"""
        session = MagicMock()
        session.request.return_value = make_response(401, text="unauthorized")
        client = VirusTotalClient("bad-key", session=session)

        with pytest.raises(VTAuthError):
            client.get_domain("example.com")

    def test_404_raises_not_found_error(self) -> None:
        """HTTP 404 → VTNotFoundError。"""
        session = MagicMock()
        session.request.return_value = make_response(404, text="not found")
        client = VirusTotalClient("k", session=session)

        with pytest.raises(VTNotFoundError):
            client.get_file("0" * 64)

    def test_500_raises_api_error(self) -> None:
        """HTTP 500 → VTApiError。"""
        session = MagicMock()
        session.request.return_value = make_response(500, text="internal error")
        client = VirusTotalClient("k", session=session)

        with pytest.raises(VTApiError):
            client.get_ip("8.8.8.8")

    def test_network_error_wrapped(self) -> None:
        """requests 網路層例外（如 ProxyError/ConnectionError）→ VTNetworkError。"""
        session = MagicMock()
        session.request.side_effect = requests.ConnectionError("proxy 403")
        client = VirusTotalClient("k", session=session)

        with pytest.raises(VTNetworkError):
            client.get_domain("example.com")


class TestRateLimitBackoff:
    """429 退避重試測試。"""

    def test_retries_after_429_then_succeeds(self) -> None:
        """首次回 429（Retry-After: 0），第二次回 200：最終成功且有退避重試。"""
        session = MagicMock()
        resp_429 = make_response(429, headers={"Retry-After": "0"})
        resp_200 = make_response(200, {"data": {"attributes": {}}})
        session.request.side_effect = [resp_429, resp_200]
        client = VirusTotalClient("k", session=session)
        # 換成假的 sleep，確保測試不會真的等待。
        client._sleep = MagicMock()

        result = client.get_domain("example.com")

        assert result == {"data": {"attributes": {}}}
        assert session.request.call_count == 2
        client._sleep.assert_called_once()


class TestWaitForAnalysis:
    """`wait_for_analysis` 測試。"""

    def test_returns_when_completed(self) -> None:
        """狀態由 queued 轉為 completed 時，回傳整包 completed dict。"""
        session = MagicMock()
        queued = make_response(200, {"data": {"attributes": {"status": "queued"}}})
        completed = make_response(200, {"data": {"id": "x", "attributes": {"status": "completed"}}})
        session.request.side_effect = [queued, completed]
        client = VirusTotalClient("k", session=session)
        client._sleep = MagicMock()
        client._clock = lambda: 0.0  # 固定時鐘，避免逾時

        result = client.wait_for_analysis("aid", interval=1, timeout=300)

        assert result["data"]["attributes"]["status"] == "completed"
        client._sleep.assert_called_once()

    def test_raises_timeout_when_never_completed(self) -> None:
        """狀態永遠不為 completed 且已逾時 → VTTimeoutError。"""
        session = MagicMock()
        session.request.return_value = make_response(200, {"data": {"attributes": {"status": "queued"}}})
        client = VirusTotalClient("k", session=session)
        client._sleep = MagicMock()
        # 第一次取 deadline（0.0），第二次檢查時已超過 deadline（1000.0）。
        client._clock = MagicMock(side_effect=[0.0, 1000.0])

        with pytest.raises(VTTimeoutError):
            client.wait_for_analysis("aid", interval=1, timeout=300)

        client._sleep.assert_not_called()


class TestScanFile:
    """`scan_file` 大檔 / 小檔分支測試。"""

    def test_large_file_uses_upload_url(self, tmp_path) -> None:
        """大檔：先取得 upload_url，再對該網址上傳。"""
        target = tmp_path / "big.bin"
        target.write_bytes(b"hello")  # 真實小檔，實際大小由 patch 覆寫
        session = MagicMock()
        upload_url_resp = make_response(200, {"data": "https://upload.example/vt"})
        analysis_resp = make_response(200, {"data": {"id": "analysis-xyz"}})
        session.request.side_effect = [upload_url_resp, analysis_resp]
        client = VirusTotalClient("k", session=session)

        with patch("os.path.getsize", return_value=LARGE_FILE_THRESHOLD):
            result = client.scan_file(str(target))

        assert result == "analysis-xyz"
        assert session.request.call_count == 2
        first_call = session.request.call_args_list[0]
        assert first_call.args == ("GET", "https://www.virustotal.com/api/v3/files/upload_url")
        second_call = session.request.call_args_list[1]
        assert second_call.args == ("POST", "https://upload.example/vt")
        assert "files" in second_call.kwargs

    def test_small_file_posts_to_files(self, tmp_path) -> None:
        """小檔：直接 POST /files。"""
        target = tmp_path / "small.bin"
        target.write_bytes(b"hi")
        session = MagicMock()
        session.request.return_value = make_response(200, {"data": {"id": "analysis-small"}})
        client = VirusTotalClient("k", session=session)

        with patch("os.path.getsize", return_value=10):
            result = client.scan_file(str(target))

        assert result == "analysis-small"
        session.request.assert_called_once()
        call = session.request.call_args
        assert call.args == ("POST", "https://www.virustotal.com/api/v3/files")
        assert "files" in call.kwargs
