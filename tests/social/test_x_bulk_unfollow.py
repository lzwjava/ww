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

from ww.social import x_bulk_unfollow


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
    @patch("ww.social.x_bulk_unfollow.time")
    @patch("ww.social.x_bulk_unfollow.subprocess")
    def test_launch_chrome(self, mock_subprocess, mock_time):
        mock_proc = MagicMock()
        mock_subprocess.Popen.return_value = mock_proc
        mock_subprocess.DEVNULL = -1

        result = x_bulk_unfollow.launch_chrome()
        self.assertEqual(result, mock_proc)
        mock_subprocess.Popen.assert_called_once()
        cmd = mock_subprocess.Popen.call_args[0][0]
        self.assertIn("--remote-debugging-port=9222", cmd)
        mock_time.sleep.assert_called_once_with(3)


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


class TestAskLlmShouldUnfollow(unittest.TestCase):
    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_keep_decision(self, mock_api):
        mock_api.return_value = '{"decision": "keep", "reason": "tech person"}'
        profile = {
            "handle": "techguy",
            "name": "Tech Guy",
            "bio": "Engineer",
            "premium": False,
        }
        decision, reason = x_bulk_unfollow.ask_llm_should_unfollow(profile)
        self.assertEqual(decision, "keep")
        self.assertEqual(reason, "tech person")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_unfollow_decision(self, mock_api):
        mock_api.return_value = '{"decision": "unfollow", "reason": "spam"}'
        profile = {"handle": "spam", "name": "Spam", "bio": "buy", "premium": False}
        decision, reason = x_bulk_unfollow.ask_llm_should_unfollow(profile)
        self.assertEqual(decision, "unfollow")
        self.assertEqual(reason, "spam")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_llm_error_defaults_to_keep(self, mock_api):
        mock_api.side_effect = Exception("API error")
        profile = {"handle": "user", "name": "User", "bio": "", "premium": False}
        decision, reason = x_bulk_unfollow.ask_llm_should_unfollow(profile)
        self.assertEqual(decision, "keep")
        self.assertEqual(reason, "llm_error")

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_profile_text_includes_premium(self, mock_api):
        mock_api.return_value = '{"decision": "keep", "reason": "verified"}'
        profile = {"handle": "vip", "name": "VIP", "bio": "important", "premium": True}
        x_bulk_unfollow.ask_llm_should_unfollow(profile)
        user_msg = mock_api.call_args[0][0][1]["content"]
        self.assertIn("Yes", user_msg)

    @patch.object(x_bulk_unfollow, "call_openrouter_api_with_messages")
    def test_missing_fields_handled(self, mock_api):
        mock_api.return_value = '{"decision": "keep"}'
        decision, _ = x_bulk_unfollow.ask_llm_should_unfollow({})
        self.assertEqual(decision, "keep")


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


def _make_page_with_cells(cells_data, locators=None):
    """Helper to create a mock page that returns cells on first count(), then 0."""
    page = MagicMock()
    call_count = [0]

    def locator_side_effect(selector):
        m = MagicMock()
        if selector == '[data-testid="UserCell"]':

            def count_side_effect():
                call_count[0] += 1
                return len(cells_data) if call_count[0] <= 1 else 0

            m.count.side_effect = count_side_effect
            m.nth.side_effect = lambda i: cells_data[i]
        return m

    page.locator.side_effect = locator_side_effect
    return page


class TestUnfollowWithLlm(unittest.TestCase):
    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "ask_llm_should_unfollow")
    @patch.object(x_bulk_unfollow, "extract_profile_info")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_dry_run_unfollow(
        self,
        mock_dt,
        mock_extract,
        mock_llm,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = ("unfollow", "spam")
        mock_extract.return_value = {
            "handle": "spam_user",
            "name": "Spam",
            "bio": "buy",
            "premium": False,
        }

        cell = MagicMock()
        cell.is_visible.return_value = True
        page = _make_page_with_cells([cell])

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(
            page, "myuser", 1, 2, dry_run=True
        )
        self.assertEqual(total, 1)
        self.assertEqual(evaluated, 1)

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "ask_llm_should_unfollow")
    @patch.object(x_bulk_unfollow, "extract_profile_info")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_keep_decision(
        self,
        mock_dt,
        mock_extract,
        mock_llm,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = ("keep", "tech person")
        mock_extract.return_value = {
            "handle": "techguy",
            "name": "Tech",
            "bio": "eng",
            "premium": False,
        }

        cell = MagicMock()
        cell.is_visible.return_value = True
        page = _make_page_with_cells([cell])

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(
            page, "myuser", 1, 2, dry_run=False
        )
        self.assertEqual(total, 0)
        self.assertEqual(evaluated, 1)

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "ask_llm_should_unfollow")
    @patch.object(x_bulk_unfollow, "extract_profile_info")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_no_cells_found(
        self,
        mock_dt,
        mock_extract,
        mock_llm,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}

        page = MagicMock()
        page.locator.return_value.count.return_value = 0

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(
            page, "myuser", 1, 2, dry_run=False
        )
        self.assertEqual(total, 0)
        self.assertEqual(evaluated, 0)

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "ask_llm_should_unfollow")
    @patch.object(x_bulk_unfollow, "extract_profile_info")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_live_unfollow_with_button(
        self,
        mock_dt,
        mock_extract,
        mock_llm,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = ("unfollow", "spam")
        mock_extract.return_value = {
            "handle": "spam_user",
            "name": "Spam",
            "bio": "buy",
            "premium": False,
        }

        cell = MagicMock()
        cell.is_visible.return_value = True
        unfollow_btn = MagicMock()
        unfollow_btn.count.return_value = 1
        confirm_btn = MagicMock()
        confirm_btn.is_visible.return_value = True

        def cell_locator(selector):
            if "-unfollow" in selector:
                return unfollow_btn
            elif "confirmationSheetConfirm" in selector:
                return confirm_btn
            return MagicMock(count=MagicMock(return_value=0))

        cell.locator.side_effect = cell_locator
        page = _make_page_with_cells([cell])

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(
            page, "myuser", 1, 2, dry_run=False
        )
        self.assertEqual(total, 1)
        self.assertEqual(evaluated, 1)

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "ask_llm_should_unfollow")
    @patch.object(x_bulk_unfollow, "extract_profile_info")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_unfollow_button_not_found(
        self,
        mock_dt,
        mock_extract,
        mock_llm,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}
        mock_random.uniform.return_value = 1.0
        mock_llm.return_value = ("unfollow", "spam")
        mock_extract.return_value = {
            "handle": "spam_user",
            "name": "Spam",
            "bio": "buy",
            "premium": False,
        }

        cell = MagicMock()
        cell.is_visible.return_value = True
        unfollow_btn = MagicMock()
        unfollow_btn.count.return_value = 0

        cell.locator.return_value = unfollow_btn
        page = _make_page_with_cells([cell])

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(
            page, "myuser", 1, 2, dry_run=False
        )
        self.assertEqual(total, 0)
        self.assertEqual(evaluated, 1)

    @patch.object(x_bulk_unfollow, "time")
    @patch.object(x_bulk_unfollow, "random")
    @patch.object(x_bulk_unfollow, "save_report")
    @patch.object(x_bulk_unfollow, "load_report")
    @patch.object(x_bulk_unfollow, "ask_llm_should_unfollow")
    @patch.object(x_bulk_unfollow, "extract_profile_info")
    @patch.object(x_bulk_unfollow, "datetime")
    def test_invisible_cell_skipped(
        self,
        mock_dt,
        mock_extract,
        mock_llm,
        mock_load,
        mock_save,
        mock_random,
        mock_time,
    ):
        mock_dt.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        mock_load.return_value = {"unfollowed": [], "kept": [], "run_date": ""}

        cell = MagicMock()
        cell.is_visible.return_value = False
        page = _make_page_with_cells([cell])

        total, evaluated = x_bulk_unfollow.unfollow_with_llm(
            page, "myuser", 1, 2, dry_run=False
        )
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
