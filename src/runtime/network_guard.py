from __future__ import annotations

import ipaddress
import os
import socket
from typing import Any

from src.runtime.settings import OmniSettings, get_settings


class NetworkAccessBlocked(RuntimeError):
    pass


_installed = False
_original_connect = socket.socket.connect
_original_connect_ex = socket.socket.connect_ex
_original_sendto = socket.socket.sendto
_original_create_connection = socket.create_connection


def _host_from_address(address: Any) -> str | None:
    if isinstance(address, tuple) and address:
        return str(address[0])
    if isinstance(address, str):
        return address
    return None


def _is_loopback_host(host: str | None) -> bool:
    if not host:
        return True
    normalized = host.strip().strip("[]").lower()
    if normalized in {"localhost", "127.0.0.1", "::1"}:
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def _is_lan_host(host: str | None) -> bool:
    if not host:
        return False
    normalized = host.strip().strip("[]").lower()
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return normalized.endswith(".local")
    return address.is_loopback or address.is_private or address.is_link_local


def _host_allowed(host: str | None, settings: OmniSettings) -> bool:
    if _is_loopback_host(host):
        return True
    if host and host.strip().strip("[]").lower() in settings.allowed_network_hosts:
        return True
    if settings.allow_lan and _is_lan_host(host):
        return True
    return False


def _assert_allowed(address: Any, settings: OmniSettings) -> None:
    host = _host_from_address(address)
    if _host_allowed(host, settings):
        return
    raise NetworkAccessBlocked(
        f"External network access blocked by Omni offline policy: {host or address}"
    )


def install_network_guard(settings: OmniSettings | None = None) -> bool:
    global _installed
    settings = settings or get_settings()
    if _installed:
        return False
    if not settings.offline_strict:
        return False
    if os.getenv("OMNI_ALLOW_EXTERNAL_NETWORK", "").strip().lower() in {"1", "true", "yes", "on"}:
        return False

    def guarded_connect(sock, address):
        _assert_allowed(address, settings)
        return _original_connect(sock, address)

    def guarded_connect_ex(sock, address):
        try:
            _assert_allowed(address, settings)
        except NetworkAccessBlocked:
            return 10013 if os.name == "nt" else 13
        return _original_connect_ex(sock, address)

    def guarded_sendto(sock, data, *args):
        address = args[-1] if args else None
        if address is not None:
            _assert_allowed(address, settings)
        return _original_sendto(sock, data, *args)

    def guarded_create_connection(address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None, *args, **kwargs):
        _assert_allowed(address, settings)
        return _original_create_connection(address, timeout=timeout, source_address=source_address, *args, **kwargs)

    socket.socket.connect = guarded_connect
    socket.socket.connect_ex = guarded_connect_ex
    socket.socket.sendto = guarded_sendto
    socket.create_connection = guarded_create_connection
    _installed = True
    return True


def is_network_guard_installed() -> bool:
    return _installed
