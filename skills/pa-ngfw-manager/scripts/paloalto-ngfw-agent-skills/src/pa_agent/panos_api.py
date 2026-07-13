"""PAN-OS XML API client.

Wraps the async HTTP client and provides typed methods for all
PAN-OS API operations including configuration, operational commands,
commit, and config import/export.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx

from pa_agent.config import Settings
from pa_agent.errors import APIError, AuthenticationError, CommitError
from pa_agent.http import PanosHttpClient
from pa_agent.log import get_logger


class PanosAPI:
    """Async client for the PAN-OS XML API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = PanosHttpClient(settings)
        self._api_key: str | None = settings.PANOS_API_KEY
        self._logger = get_logger("panos_api")

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def ensure_auth(self) -> str:
        """Return the API key, calling the keygen endpoint if needed.

        The key is cached in memory and never written to disk.

        Raises:
            AuthenticationError: If credentials are missing or keygen fails.
        """
        if self._api_key:
            return self._api_key

        username = self._settings.PANOS_USERNAME
        password = self._settings.PANOS_PASSWORD
        if not username or not password:
            raise AuthenticationError(
                "No API key configured and username/password not provided"
            )

        self._logger.info("Generating API key via keygen for user '%s'", username)
        resp = await self._client.post(
            data={},
            params={
                "type": "keygen",
                "user": username,
                "password": password.get_secret_value(),
            },
        )

        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as exc:
            raise AuthenticationError(
                f"Failed to parse keygen response: {exc}"
            ) from exc

        if root.attrib.get("status") != "success":
            msg = self._extract_error_message(root)
            raise AuthenticationError(f"Keygen failed: {msg}")

        key_el = root.find(".//key")
        if key_el is None or not key_el.text:
            raise AuthenticationError("Keygen response did not contain a key")

        self._api_key = key_el.text
        self._logger.info("API key obtained successfully")
        return self._api_key

    # ------------------------------------------------------------------
    # Core request / response helpers
    # ------------------------------------------------------------------

    async def _request(
        self,
        params: dict[str, str],
        data: dict[str, str] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
    ) -> ET.Element:
        """Make an authenticated API request and return the parsed XML root.

        Automatically injects the API key into *params*.

        Raises:
            APIError: If the PAN-OS response indicates an error.
        """
        key = await self.ensure_auth()
        params["key"] = key

        self._logger.debug(
            "API request type=%s action=%s",
            params.get("type"),
            params.get("action", "n/a"),
        )

        if data or files:
            resp = await self._client.post(data=data, params=params, files=files)
        else:
            resp = await self._client.get(params=params)

        return self._parse_response(resp)

    def _parse_response(self, resp: httpx.Response) -> ET.Element:
        """Parse an XML API response and raise on error status.

        Args:
            resp: The raw HTTP response from PAN-OS.

        Returns:
            The root ``<response>`` :class:`~xml.etree.ElementTree.Element`.

        Raises:
            APIError: If the response cannot be parsed or has
                ``status="error"``.
        """
        try:
            root = ET.fromstring(resp.text)
        except ET.ParseError as exc:
            raise APIError(f"Failed to parse API response XML: {exc}") from exc

        if root.attrib.get("status") == "error":
            msg = self._extract_error_message(root)
            raise APIError(msg)

        return root

    @staticmethod
    def _extract_error_message(root: ET.Element) -> str:
        """Extract a human-readable error message from a PAN-OS error response.

        Handles both ``<result><msg>…</msg></result>`` and
        ``<msg><line>…</line></msg>`` layouts.
        """
        # Try <result><msg>...</msg></result>
        msg_el = root.find(".//result/msg")
        if msg_el is not None and msg_el.text:
            return msg_el.text

        # Try <msg><line>...</line></msg>
        line_el = root.find(".//msg/line")
        if line_el is not None and line_el.text:
            return line_el.text

        # Try <msg> directly
        msg_el = root.find(".//msg")
        if msg_el is not None and msg_el.text:
            return msg_el.text

        return "Unknown PAN-OS error"

    # ------------------------------------------------------------------
    # Operational commands
    # ------------------------------------------------------------------

    async def op_command(self, cmd: str) -> ET.Element:
        """Execute an operational command.

        Args:
            cmd: XML command string, e.g.
                ``'<show><system><info/></system></show>'``.

        Returns:
            Parsed XML response element.
        """
        return await self._request({"type": "op", "cmd": cmd})

    # ------------------------------------------------------------------
    # Configuration CRUD
    # ------------------------------------------------------------------

    async def config_get(self, xpath: str) -> ET.Element:
        """Retrieve configuration at the given *xpath*.

        Args:
            xpath: PAN-OS configuration XPath.

        Returns:
            Parsed XML response element.
        """
        return await self._request(
            {"type": "config", "action": "get", "xpath": xpath}
        )

    async def config_set(self, xpath: str, element: str) -> ET.Element:
        """Set (merge) configuration at *xpath*.

        Args:
            xpath: Target configuration XPath.
            element: XML fragment to set.

        Returns:
            Parsed XML response element.
        """
        return await self._request(
            {"type": "config", "action": "set", "xpath": xpath, "element": element}
        )

    async def config_edit(self, xpath: str, element: str) -> ET.Element:
        """Edit (replace) configuration at *xpath*.

        Args:
            xpath: Target configuration XPath.
            element: XML fragment that replaces existing config.

        Returns:
            Parsed XML response element.
        """
        return await self._request(
            {"type": "config", "action": "edit", "xpath": xpath, "element": element}
        )

    async def config_delete(self, xpath: str) -> ET.Element:
        """Delete configuration at *xpath*.

        Args:
            xpath: Configuration XPath to delete.

        Returns:
            Parsed XML response element.
        """
        return await self._request(
            {"type": "config", "action": "delete", "xpath": xpath}
        )

    # ------------------------------------------------------------------
    # Commit
    # ------------------------------------------------------------------

    async def commit(
        self, comment: str | None = None, force: bool = False
    ) -> ET.Element:
        """Commit the candidate configuration.

        Args:
            comment: Optional commit description.
            force: If ``True``, force the commit even when no changes are
                pending.

        Returns:
            Parsed XML response element.

        Raises:
            CommitError: If the commit fails.
        """
        cmd = "<commit>"
        if force:
            cmd += "<force/>"
        if comment:
            cmd += f"<description>{comment}</description>"
        cmd += "</commit>"

        try:
            return await self._request({"type": "commit", "cmd": cmd})
        except APIError as exc:
            raise CommitError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Config import / export
    # ------------------------------------------------------------------

    async def export_config(self, category: str = "configuration") -> bytes:
        """Export configuration as raw XML bytes.

        Args:
            category: Export category (default ``"configuration"``).

        Returns:
            Raw XML content bytes.
        """
        key = await self.ensure_auth()
        self._logger.debug("Exporting config category=%s", category)
        resp = await self._client.get(
            params={"type": "export", "category": category, "key": key}
        )
        resp.raise_for_status()
        return resp.content

    async def import_config(self, filename: str, data: bytes) -> ET.Element:
        """Import a configuration file to the firewall.

        Args:
            filename: Name to assign to the uploaded configuration.
            data: Raw XML configuration bytes.

        Returns:
            Parsed XML response element.
        """
        return await self._request(
            params={"type": "import", "category": "configuration"},
            files={"file": (filename, data, "application/xml")},
        )

    async def load_config(self, filename: str) -> ET.Element:
        """Load a previously imported named configuration.

        Args:
            filename: Configuration file name on the firewall.

        Returns:
            Parsed XML response element.
        """
        cmd = f"<load><config><from>{filename}</from></config></load>"
        return await self.op_command(cmd)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    async def get_hostname(self) -> str:
        """Return the firewall hostname from system info.

        Returns:
            The hostname string, or ``"unknown"`` if unavailable.
        """
        result = await self.op_command("<show><system><info/></system></show>")
        hostname_el = result.find(".//hostname")
        if hostname_el is not None and hostname_el.text:
            return hostname_el.text
        return "unknown"

    @property
    def vsys(self) -> str:
        """The virtual system configured in settings."""
        return self._settings.PANOS_VSYS

    def security_rule_xpath(self, rule_name: str | None = None) -> str:
        """Build an XPath for security rules.

        Args:
            rule_name: Optional rule name.  When provided the XPath points
                to that specific rule entry; otherwise it points to the
                rules container.

        Returns:
            XPath string.
        """
        base = (
            f"/config/devices/entry[@name='localhost.localdomain']"
            f"/vsys/entry[@name='{self.vsys}']/rulebase/security/rules"
        )
        if rule_name:
            base += f"/entry[@name='{rule_name}']"
        return base

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()

    async def __aenter__(self) -> PanosAPI:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
