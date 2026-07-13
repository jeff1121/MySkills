"""finmind.check_usage — API 使用量查詢工具。"""

from __future__ import annotations

from typing import Any

from finmind_mcp.client import FinMindClient
from finmind_mcp.config import get_settings
from finmind_mcp.errors import AuthenticationError


async def check_usage() -> dict[str, Any]:
    """查詢 FinMind API 使用量與配額。

    Returns:
        包含使用次數、上限、剩餘次數的字典
    """
    settings = get_settings()

    if not settings.validate_token():
        raise AuthenticationError(
            "未設定 FINMIND_TOKEN。請先設定 API Token 才能查詢使用量。"
        )

    async with FinMindClient(settings) as client:
        raw = await client.check_usage()

    user_count = raw.get("user_count", 0)
    api_limit = raw.get("api_request_limit", 0)
    remaining = api_limit - user_count if api_limit > 0 else 0

    # 判斷會員等級
    tier = "Free"
    if api_limit > 600:
        tier = "Sponsor"
    elif api_limit > 300:
        tier = "Backer"

    return {
        "user_count": user_count,
        "api_request_limit": api_limit,
        "remaining": remaining,
        "usage_pct": round(user_count / api_limit * 100, 1) if api_limit > 0 else 0,
        "estimated_tier": tier,
        "note": f"已使用 {user_count}/{api_limit} 次（剩餘 {remaining} 次）",
    }
