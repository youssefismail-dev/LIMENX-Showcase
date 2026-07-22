# © 2026 Youssef Ismail. All rights reserved.
# LIMENX is proprietary software. Published for portfolio review only —
# not licensed for reuse, redistribution, or derivative works.
"""
validation/url_validator.py

Structural URL validation shared by every stage that ingests raw URLs
(the data pipeline today; the REST API later).

This is a purely *offline, structural* check: does the string look like
a well-formed URL at all? It deliberately does NOT check reachability,
DNS, or threat reputation (out of scope for Version 1), and it does NOT
judge suspiciousness -- that is the feature extractor's job. A URL like
'http://2130706433/login' (dword-encoded IP) is *valid* here on purpose:
dropping it during sanitization would silently erase exactly the
phishing signal `is_obfuscated_ip` exists to detect.
"""

from __future__ import annotations

import urllib.parse


class URLValidator:
    """Structural validity checks for raw URL strings."""

    @staticmethod
    def is_valid(url: object) -> bool:
        """
        Returns True if `url` is a structurally well-formed absolute URL.

        A URL is considered valid when all of the following hold:
        - it is a non-empty string,
        - it parses without error (e.g. 'http://[::1/broken' raises inside
          urllib on an unterminated IPv6 literal -> invalid),
        - it has an explicit scheme and a non-empty hostname
          (the sanitizer normalises scheme-less rows *before* this check),
        - its port, if present, is a valid integer (':abc' -> invalid),
        - its hostname contains no whitespace ('http://hello world' -> invalid).

        Parameters
        ----------
        url : object -- Candidate value; anything that is not a string
                        fails fast rather than raising.

        Returns
        -------
        bool -- True if structurally valid, False otherwise.
        """
        if not isinstance(url, str) or not url.strip():
            return False

        try:
            parsed = urllib.parse.urlparse(url)
            hostname = parsed.hostname   # can raise on malformed IPv6 literals
            _ = parsed.port              # raises ValueError on non-numeric ports
        except ValueError:
            return False

        if not parsed.scheme or not hostname:
            return False

        if any(ch.isspace() for ch in hostname):
            return False

        return True
