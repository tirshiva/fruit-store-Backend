from typing import Callable, Optional

from starlette.datastructures import URL
from starlette.types import ASGIApp, Receive, Scope, Send


class ProxyHeaderMiddleware:
    """
    Minimal middleware to honor X-Forwarded-* headers from a trusted proxy.

    Notes:
    - Only enable when behind a proxy that sets these headers correctly.
    - In production, validate the client IP is one of your proxy IPs before trusting headers.
    """

    def __init__(self, app: ASGIApp, trust: bool = True) -> None:
        self.app = app
        self.trust = trust

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or not self.trust:
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}

        forwarded_proto = headers.get("x-forwarded-proto")
        forwarded_host = headers.get("x-forwarded-host") or headers.get("host")
        forwarded_for = headers.get("x-forwarded-for")

        if forwarded_proto:
            scope["scheme"] = forwarded_proto.split(",")[0].strip()

        if forwarded_host:
            server_host = forwarded_host.split(",")[0].strip()
            # Preserve port if provided
            if ":" in server_host:
                host, port_str = server_host.rsplit(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    port = 443 if scope.get("scheme") == "https" else 80
                scope["server"] = (host, port)
                # Update Host header
                self._set_header(scope, b"host", server_host.encode())
            else:
                scope["server"] = (server_host, 443 if scope.get("scheme") == "https" else 80)
                self._set_header(scope, b"host", server_host.encode())

        # Optionally set client IP from X-Forwarded-For (first is original client)
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
            scope["client"] = (client_ip, scope.get("client", (None, 0))[1] or 0)

        await self.app(scope, receive, send)

    @staticmethod
    def _set_header(scope: Scope, key: bytes, value: bytes) -> None:
        headers = scope.get("headers") or []
        # Remove existing key
        headers = [(k, v) for (k, v) in headers if k.lower() != key.lower()]
        headers.append((key, value))
        scope["headers"] = headers


