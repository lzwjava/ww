import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

# Mock playwright before importing x_bulk_unfollow since it imports at module level
from unittest.mock import MagicMock as _MA

_pm = _MA()
sys.modules["playwright"] = _pm
sys.modules["playwright.sync_api"] = _pm.sync_api

from ww.social import x_bulk_unfollow  # noqa: E402


class TestConstants(unittest.TestCase):
    def test_following_url_template(self):
        self.assertIn("{username}", x_bulk_unfollow.FOLLOWING_URL_TEMPLATE)

    def test_default_delay(self):
        self.assertEqual(x_bulk_unfollow.DEFAULT_DELAY, 2)

    def test_default_scroll_pause(self):
        self.assertEqual(x_bulk_unfollow.DEFAULT_SCROLL_PAUSE, 1.5)

    def test_debug_port(self):
        self.assertEqual(x_bulk_unfollow.DEBUG_PORT, 9222)

    def test_report_file_path(self):
        self.assertTrue(x_bulk_unfollow.REPORT_FILE.endswith("unfollowed_report.json"))

    def test_llm_system_prompt(self):
        self.assertIn("unfollow", x_bulk_unfollow.LLM_SYSTEM_PROMPT.lower())
        self.assertIn("JSON", x_bulk_unfollow.LLM_SYSTEM_PROMPT)


class TestLaunchChrome(unittest.TestCase):
    @patch("socket.create_connection")
    @patch("ww.social.x_bulk_unfollow.time")
    @patch("ww.social.x_bulk_unfollow.subprocess")
    def test_launch_chrome(self, mock_subprocess, mock_time, mock_socket):
        mock_proc = MagicMock()
        mock_subprocess.Popen.return_value = mock_proc
        mock_subprocess.DEVNULL = -1
        mock_socket.return_value = MagicMock()

        result = x_bulk_unfollow.launch_chrome()
        self.assertEqual(result, mock_proc)
        mock_subprocess.Popen.assert_called_once()
        cmd = mock_subprocess.Popen.call_args[0][0]
        self.assertIn("--remote-debugging-port=9222", cmd)
        # Connection succeeds immediately, so sleep is never called
        mock_time.sleep.assert_not_called()


class TestExtractProfileInfo(unittest.TestCase):
    def test_extract_with_exception(self):
        cell = MagicMock()
        cell.locator.side_effect = Exception("not found")
        result = x_bulk_unfollow.extract_profile_info(cell)
        self.assertEqual(result["handle"], "unknown")
        self.assertEqual(result["name"], "")
        self.assertEqual(result["bio"], "")
        self.assertFalse(result["premium"])

    def test_extract_profile_full(self):
        cell = MagicMock()
        link_mock = MagicMock()
        link_mock.get_attribute.return_value = "/testuser"
        name_mock = MagicMock()
        name_mock.inner_text.return_value = "Test User"
        bio_first = MagicMock()
        bio_first.inner_text.return_value = "I am a test"

        def locator_side_effect(selector):
            mock = MagicMock()
            if selector == 'a[role="link"]':
                mock.first = link_mock
            elif selector == 'a[role="link"] span':
                mock.first = name_mock
            elif selector == '[data-testid="UserDescription"]':
                mock.count.return_value = 1
                mock.first = bio_first
            elif selector == '[data-testid="icon-verified"]':
                mock.count.return_value = 1
            return mock

        cell.locator.side_effect = locator_side_effect
        result = x_bulk_unfollow.extract_profile_info(cell)
        self.assertEqual(result["handle"], "testuser")
        self.assertEqual(result["name"], "Test User")
        self.assertEqual(result["bio"], "I am a test")
        self.assertTrue(result["premium"])


class TestAskLlmPickUnfollow(unittest.TestCase):
    """Tests for ask_llm_pick_unfollow which picks one profile from a batch."""

    def _make_profile(self, **overrides):
        return {
            "handle": "user1",
            "name": "User 1",
            "bio": "Engineer",
            "premium": False,
            "followers": 1000,
            **overrides,
        }

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_picks_first_profile(self, mock_api):
        mock_api.return_value = '{"index": 1, "reason": "spammy profile"}'
        profiles = [
            self._make_profile(handle="spam1"),
            self._make_profile(handle="good1"),
        ]
        idx, reason = x_bulk_unfollow.ask_llm_pick_unfollow(profiles)
        self.assertEqual(idx, 0)
        self.assertEqual(reason, "spammy profile")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_picks_second_profile(self, mock_api):
        mock_api.return_value = '{"index": 2, "reason": "low followers"}'
        profiles = [self._make_profile(handle="a"), self._make_profile(handle="b")]
        idx, reason = x_bulk_unfollow.ask_llm_pick_unfollow(profiles)
        self.assertEqual(idx, 1)
        self.assertEqual(reason, "low followers")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_api_error_returns_minus_one(self, mock_api):
        mock_api.side_effect = Exception("API error")
        profiles = [self._make_profile()]
        idx, reason = x_bulk_unfollow.ask_llm_pick_unfollow(profiles)
        self.assertEqual(idx, -1)
        self.assertEqual(reason, "llm_error")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_invalid_index_returns_minus_one(self, mock_api):
        mock_api.return_value = '{"index": 99, "reason": "out of range"}'
        profiles = [self._make_profile()]
        idx, reason = x_bulk_unfollow.ask_llm_pick_unfollow(profiles)
        self.assertEqual(idx, -1)
        self.assertEqual(reason, "invalid_index")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_profile_text_includes_premium(self, mock_api):
        mock_api.return_value = '{"index": 1, "reason": "verified"}'
        profiles = [self._make_profile(handle="vip", premium=True)]
        x_bulk_unfollow.ask_llm_pick_unfollow(profiles)
        user_msg = mock_api.call_args[0][0][1]["content"]
        self.assertIn("Premium: Yes", user_msg)

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_empty_profiles_returns_minus_one(self, mock_api):
        mock_api.return_value = '{"index": 1, "reason": "nobody"}'
        idx, reason = x_bulk_unfollow.ask_llm_pick_unfollow([])
        self.assertEqual(idx, -1)
        # With empty profiles, the API call is made with empty text, which
        # may return a valid-looking JSON with index=1. Since 1 > len([]),
        # it returns invalid_index.
        self.assertEqual(reason, "invalid_index")


class TestLoadReport(unittest.TestCase):
    @patch("os.path.exists")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"unfollowed": [], "kept": [], "run_date": "2024-01-01"}',
    )
    def test_load_existing(self, mock_file, mock_exists):
        mock_exists.return_value = True
        result = x_bulk_unfollow.load_report()
        self.assertIn("unfollowed", result)
        self.assertEqual(result["run_date"], "2024-01-01")

    @patch("os.path.exists")
    def test_load_nonexistent(self, mock_exists):
        mock_exists.return_value = False
        result = x_bulk_unfollow.load_report()
        self.assertEqual(result["unfollowed"], [])
        self.assertEqual(result["kept"], [])
        self.assertEqual(result["run_date"], "")


class TestSaveReport(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open)
    def test_save_report(self, mock_file):
        report = {
            "unfollowed": [{"handle": "user1"}],
            "kept": [],
            "run_date": "2024-01-01",
        }
        x_bulk_unfollow.save_report(report)
        mock_file.assert_called_once()


def _make_page_with_cells(cells_data):
    """Helper to create a mock page that returns the given cells."""
    page = MagicMock()

    def locator_side_effect(selector):
        m = MagicMock()
        if selector == '[data-testid="UserCell"]':
            m.count.return_value = len(cells_data)
            m.nth.side_effect = lambda i: cells_data[i]
        return m

    page.locator.side_effect = locator_side_effect
    return page


class TestUnfollowWithLlm(unittest.TestCase):
    """Tests for unfollow_with_llm.

    These tests mock collect_batch and do_unfollow at a high level
    to avoid complex page/cell mock interactions with the loop logic.
    """

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "do_unfollow")
    @patch.object(x_bulk_unfollow, "ask_llm_pick_unfollow")
    @patch.object(x_bulk_unfollow, "collect_batch")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_unfollow_selected_profile(
        self,
        mock_dt,
        mock_collect,
        mock_llm,
        mock_do_unfollow,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        """LLM picks a profile → do_unfollow increments the counter."""
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = (0, "spammy")
        profile = {
            "handle": "spam_user",
            "name": "Spam",
            "bio": "buy",
            "premium": False,
        }
        # collect_batch is called 2x per iteration (main + scroll).
        # Both calls return the batch, then loop exits because unfollowed reaches count.
        mock_collect.return_value = [(0, profile)]

        def _do_unfollow_side(page, cell_index, prof, report, count, delay, unfollowed):
            unfollowed[0] += 1
            return True

        mock_do_unfollow.side_effect = _do_unfollow_side

        page = MagicMock()
        page.locator.return_value.count.return_value = 1

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(page, "myuser", 1, 2)
        self.assertEqual(total, 1)
        self.assertEqual(evaluated, 1)
        mock_llm.assert_called_once_with([profile])
        mock_do_unfollow.assert_called_once()

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "do_unfollow")
    @patch.object(x_bulk_unfollow, "ask_llm_pick_unfollow")
    @patch.object(x_bulk_unfollow, "collect_batch")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_no_profile_picked(
        self,
        mock_dt,
        mock_collect,
        mock_llm,
        mock_do_unfollow,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        """LLM returns -1 → nobody is unfollowed, loop stops when batch runs out."""
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = (-1, "llm_error")
        profile = {
            "handle": "someone",
            "name": "Someone",
            "bio": "ok",
            "premium": False,
        }
        # First iteration: 2 calls (main + scroll), returns batch.
        # Second iteration: collect_batch returns empty → loop breaks.
        _calls = [0]

        def _collect_side(*args):
            _calls[0] += 1
            if _calls[0] <= 2:
                return [(0, profile)]
            return []

        mock_collect.side_effect = _collect_side

        page = MagicMock()
        page.locator.return_value.count.return_value = 1

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(page, "myuser", 1, 2)
        self.assertEqual(total, 0)
        self.assertEqual(evaluated, 1)
        mock_do_unfollow.assert_not_called()

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "collect_batch")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_no_cells_found(
        self,
        mock_dt,
        mock_collect,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        """Page has no cells at all → 0 total, 0 evaluated."""
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}

        page = MagicMock()
        page.locator.return_value.count.return_value = 0

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(page, "myuser", 1, 2)
        self.assertEqual(total, 0)
        self.assertEqual(evaluated, 0)
        mock_collect.assert_not_called()

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "do_unfollow")
    @patch.object(x_bulk_unfollow, "ask_llm_pick_unfollow")
    @patch.object(x_bulk_unfollow, "collect_batch")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_reaches_target_count(
        self,
        mock_dt,
        mock_collect,
        mock_llm,
        mock_do_unfollow,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        """Multiple batches until target count is reached.

        collect_batch is called 2x per iteration (main + scroll).
        We alternate between two profiles across iterations.
        """
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = (0, "spammy")

        profile_a = {
            "handle": "user_a",
            "name": "A",
            "bio": "a",
            "premium": False,
        }
        profile_b = {
            "handle": "user_b",
            "name": "B",
            "bio": "b",
            "premium": False,
        }

        # 2 calls per iteration × 2 iterations = 4 calls, then empty to stop
        _calls = [0]
        _profiles = [profile_a, profile_b]

        def _collect_side(*args):
            idx = _calls[0]
            _calls[0] += 1
            if idx < 4:  # 2 iterations × 2 calls each
                return [(0, _profiles[idx // 2])]
            return []

        mock_collect.side_effect = _collect_side

        def _do_unfollow_side(page, cell_index, prof, report, count, delay, unfollowed):
            unfollowed[0] += 1
            return True

        mock_do_unfollow.side_effect = _do_unfollow_side

        page = MagicMock()
        page.locator.return_value.count.return_value = 1

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(page, "myuser", 3, 2)
        # Only 2 profiles were evaluated before batch ran out
        self.assertEqual(total, 2)
        self.assertEqual(evaluated, 2)

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "collect_batch")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_invisible_cell_skipped(
        self,
        mock_dt,
        mock_collect,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        """collect_batch returns empty if no visible/unseen cells."""
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}

        mock_collect.return_value = []

        page = MagicMock()
        page.locator.return_value.count.return_value = 1

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(page, "myuser", 1, 2)
        self.assertEqual(total, 0)
        self.assertEqual(evaluated, 0)


class TestGetUsername(unittest.TestCase):
    def test_get_username(self):
        page = MagicMock()
        nav_link = MagicMock()
        nav_link.get_attribute.return_value = "/testuser"
        page.locator.return_value = nav_link
        result = x_bulk_unfollow.get_username(page)
        self.assertEqual(result, "testuser")


class TestLoginManually(unittest.TestCase):
    @patch("builtins.input")
    @patch("builtins.print")
    def test_login_manually(self, mock_print, mock_input):
        page = MagicMock()
        x_bulk_unfollow.login_manually(page)
        page.goto.assert_called_once_with("https://x.com/login")
        mock_input.assert_called_once()


if __name__ == "__main__":
    unittest.main()


# Cleanup sys.modules to prevent test pollution
import sys as _sys  # noqa: E402

_saved = {k: _sys.modules.get(k) for k in ["playwright", "playwright.sync_api"]}


def tearDownModule():
    for key, original in _saved.items():
        if original is None:
            _sys.modules.pop(key, None)
        else:
            _sys.modules[key] = original
