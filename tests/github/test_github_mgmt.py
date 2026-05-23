"""Tests for ww github github_mgmt module."""

import os
import pytest
from unittest.mock import patch


def test_get_token_missing():
    """Test that missing GITHUB_PAT_TOKEN raises exception."""
    with patch.dict(os.environ, {}, clear=True):
        from ww.github.github_mgmt import _get_token

        with pytest.raises(Exception, match="GITHUB_PAT_TOKEN not set"):
            _get_token()


def test_get_token_set():
    """Test that GITHUB_PAT_TOKEN is returned when set."""
    with patch.dict(os.environ, {"GITHUB_PAT_TOKEN": "test_token"}):
        from ww.github.github_mgmt import _get_token

        assert _get_token() == "test_token"


def test_fmt_count():
    """Test count formatting."""
    from ww.github.github_mgmt import _fmt_count

    assert _fmt_count(500) == "500"
    assert _fmt_count(1500) == "1.5K"
    assert _fmt_count(1500000) == "1.5M"
