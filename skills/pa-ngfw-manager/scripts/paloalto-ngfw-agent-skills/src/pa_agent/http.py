from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from pa_agent.config import Settings
from pa_agent.errors import APIError, PanosConnectionError, RateLimitError
from pa_agent.log import get_logger

logger = get_logger(__name__)


class PanosHttpClient:
    """HTTP client wrapper for PAN-OS XML API.
    
    Features:
    - Async httpx client
    - Token bucket rate limiting
    - Automatic retry on connection errors
    - Async context manager support
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize HTTP client with settings.
        
        Args:
            settings: Configuration settings with PANOS host and credentials.
        """
        self.settings = settings
        self.client = httpx.AsyncClient(
            verify=settings.PANOS_VERIFY_TLS,
            timeout=settings.PANOS_TIMEOUT,
            base_url=settings.base_url,
        )
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()

    async def _rate_limit(self) -> None:
        """Apply token bucket rate limiting.
        
        Ensures requests are spaced according to the configured rate limit.
        """
        async with self._rate_limit_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            min_interval = 1.0 / self.settings.PANOS_RATE_LIMIT
            
            if elapsed < min_interval:
                sleep_time = min_interval - elapsed
                await asyncio.sleep(sleep_time)
            
            self._last_request_time = time.monotonic()

    async def request(
        self,
        method: str = "POST",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        retry_on_error: bool = True,
    ) -> httpx.Response:
        """Make HTTP request with retry and rate limiting.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Form data
            files: Files to upload
            retry_on_error: Whether to retry on connection errors (only for idempotent methods)
            
        Returns:
            HTTP response
            
        Raises:
            PanosConnectionError: On connection failures
            APIError: On API errors
        """
        await self._rate_limit()
        
        # Only retry GET requests (idempotent)
        should_retry = retry_on_error and method.upper() == "GET"
        
        if should_retry:
            return await self._request_with_retry(method, params, data, files)
        else:
            return await self._request_once(method, params, data, files)

    async def _request_once(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute single request without retry.
        
        Args:
            method: HTTP method
            params: Query parameters
            data: Form data
            files: Files to upload
            
        Returns:
            HTTP response
            
        Raises:
            PanosConnectionError: On connection failures
        """
        try:
            logger.debug(
                f"Request {method}",
                extra={
                    "method": method,
                    "params": self._sanitize_params(params),
                },
            )
            response = await self.client.request(
                method=method,
                url="",  # use base_url
                params=params,
                data=data,
                files=files,
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP connection error: {e}")
            raise PanosConnectionError(f"Connection failed: {e}") from e

    async def _request_with_retry(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute request with retry logic for connection errors.
        
        Retries on connection errors with exponential backoff.
        Does not retry on API/HTTP status errors.
        
        Args:
            method: HTTP method
            params: Query parameters
            data: Form data
            files: Files to upload
            
        Returns:
            HTTP response
            
        Raises:
            PanosConnectionError: On connection failures after retries
        """
        retry_config = AsyncRetrying(
            retry=retry_if_exception_type(PanosConnectionError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=4),
            reraise=True,
        )
        
        try:
            async for attempt in retry_config:
                with attempt:
                    return await self._request_once(method, params, data, files)
        except RetryError as e:
            logger.error(f"Request failed after retries: {e}")
            raise PanosConnectionError(f"Request failed after 3 retries") from e

    async def get(
        self, params: dict[str, Any] | None = None
    ) -> httpx.Response:
        """Perform GET request.
        
        Args:
            params: Query parameters
            
        Returns:
            HTTP response
        """
        return await self.request(method="GET", params=params, retry_on_error=True)

    async def post(
        self,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Perform POST request.
        
        Args:
            data: Form data
            params: Query parameters
            files: Files to upload
            
        Returns:
            HTTP response
        """
        return await self.request(
            method="POST", params=params, data=data, files=files, retry_on_error=False
        )

    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> PanosHttpClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    @staticmethod
    def _sanitize_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
        """Sanitize parameters for logging (remove sensitive data).
        
        Args:
            params: Original parameters
            
        Returns:
            Sanitized parameters safe for logging
        """
        if not params:
            return params
        
        sensitive_keys = {"key", "password", "token", "api_key", "secret"}
        sanitized = {}
        
        for key, value in params.items():
            if key.lower() in sensitive_keys:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        
        return sanitized
