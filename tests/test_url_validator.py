# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
tests/test_url_validator.py

Tests for the shared structural URL validator (validation/url_validator.py).
Run with: pytest tests/test_url_validator.py
"""

import pytest

from validation.url_validator import URLValidator


@pytest.mark.parametrize("url", [
    "http://google.com",
    "https://sub.example.co.uk:8443/path?q=1#frag",
    "ftp://files.example.com/pub",
    "HTTP://GOOGLE.COM",                 # scheme/host case-insensitive
    "http://café.com",                   # unicode hostname (latin-1 datasets)
    "http://[::1]:8080/path",            # well-formed IPv6 literal
    "http://192.168.0.1/login",          # dotted-decimal IP host
    "http://2130706433/login",           # dword IP: MUST survive sanitization
    "http://0x7f000001/",                # hex IP: MUST survive sanitization
])
def test_valid_urls(url):
    assert URLValidator.is_valid(url) is True


@pytest.mark.parametrize("url", [
    "",                                  # empty
    "   ",                               # whitespace only
    None,                                # not a string
    123,                                 # not a string
    "google.com",                        # no scheme (normalised upstream)
    "http://",                           # scheme but no host
    "http://[::1/broken",                # unterminated IPv6 literal
    "http://a.com:notaport/",            # non-numeric port
    "http://hello world.com/",           # whitespace inside hostname
])
def test_invalid_urls(url):
    assert URLValidator.is_valid(url) is False


def test_does_not_judge_suspiciousness():
    """Suspicious-but-well-formed URLs are the extractor's job, not ours."""
    assert URLValidator.is_valid("http://paypal-secure.evil.tk/login.exe") is True
