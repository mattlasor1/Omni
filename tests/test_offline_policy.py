import socket
from types import SimpleNamespace

import pytest

from src.runtime import get_settings, install_network_guard, is_network_guard_installed
from src.runtime.network_guard import NetworkAccessBlocked, _host_allowed


def test_strict_offline_guard_is_installed():
    install_network_guard(get_settings())

    assert is_network_guard_installed()


def test_strict_offline_guard_blocks_external_socket():
    install_network_guard(get_settings())
    sock = socket.socket()
    try:
        with pytest.raises(NetworkAccessBlocked):
            sock.connect(("93.184.216.34", 80))
    finally:
        sock.close()


def test_strict_offline_guard_allows_loopback_attempts():
    install_network_guard(get_settings())
    sock = socket.socket()
    try:
        result = sock.connect_ex(("127.0.0.1", 9))
    finally:
        sock.close()

    assert isinstance(result, int)
    assert result != 10013


def test_offline_guard_supports_explicit_local_service_allowlist():
    settings = SimpleNamespace(allowed_network_hosts=("omnitwin-redis",), allow_lan=False)

    assert _host_allowed("omnitwin-redis", settings)
    assert not _host_allowed("example.com", settings)
