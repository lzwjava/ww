import unittest
from unittest.mock import patch, MagicMock, mock_open
import os

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

try:
    import importlib.util

    _HAS_DEPS = importlib.util.find_spec("selenium") is not None
    if _HAS_DEPS:
        from ww.crawler.weibo import scrape_weibo  # noqa: F401
except ImportError:
    _HAS_DEPS = False


def setUpModule():
    if not _HAS_DEPS:
        raise unittest.SkipTest("Missing optional dependency: selenium")


@unittest.skipUnless(_HAS_DEPS, "Missing optional dependency: selenium")
class TestScrapeWeibo(unittest.TestCase):
    @patch("ww.crawler.weibo.webdriver.Chrome")
    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.dirname", return_value="/tmp")
    @patch("os.path.abspath", return_value="/tmp/weibo.py")
    def test_no_posts_found(
        self, mock_abspath, mock_dirname, mock_exists, mock_file, mock_chrome
    ):
        from ww.crawler.weibo import scrape_weibo

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html><body></body></html>"

        # WebDriverWait will raise on presence_of_element_located
        mock_driver.find_elements.return_value = []

        with patch("ww.crawler.weibo.WebDriverWait") as mock_wait:
            # First wait (login check) succeeds, second wait (posts) raises
            mock_wait_instance = MagicMock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.side_effect = [None, Exception("timeout")]

            result = scrape_weibo("https://weibo.com/u/123")

        self.assertEqual(result, [])
        mock_driver.quit.assert_called()

    @patch("ww.crawler.weibo.webdriver.Chrome")
    @patch("builtins.open", new_callable=mock_open, read_data='{"session": "abc"}')
    @patch("os.path.exists", return_value=True)
    @patch("os.path.dirname", return_value="/tmp")
    @patch("os.path.abspath", return_value="/tmp/weibo.py")
    def test_with_json_cookies(
        self, mock_abspath, mock_dirname, mock_exists, mock_file, mock_chrome
    ):
        from ww.crawler.weibo import scrape_weibo

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html></html>"
        mock_driver.find_elements.return_value = []

        with patch("ww.crawler.weibo.WebDriverWait") as mock_wait:
            mock_wait_instance = MagicMock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.side_effect = [None, Exception("timeout")]

            result = scrape_weibo("https://weibo.com/u/123")

        mock_driver.add_cookie.assert_called()
        self.assertEqual(result, [])

    @patch("ww.crawler.weibo.webdriver.Chrome")
    @patch("builtins.open", new_callable=mock_open, read_data="key1=val1; key2=val2")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.dirname", return_value="/tmp")
    @patch("os.path.abspath", return_value="/tmp/weibo.py")
    def test_with_string_cookies(
        self, mock_abspath, mock_dirname, mock_exists, mock_file, mock_chrome
    ):
        from ww.crawler.weibo import scrape_weibo

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html></html>"
        mock_driver.find_elements.return_value = []

        with patch("ww.crawler.weibo.WebDriverWait") as mock_wait:
            mock_wait_instance = MagicMock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.side_effect = [None, Exception("timeout")]

            result = scrape_weibo("https://weibo.com/u/123")

        self.assertEqual(result, [])

    @patch("ww.crawler.weibo.webdriver.Chrome")
    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("os.path.exists", return_value=False)
    @patch("os.path.dirname", return_value="/tmp")
    @patch("os.path.abspath", return_value="/tmp/weibo.py")
    def test_no_cookies_file(
        self, mock_abspath, mock_dirname, mock_exists, mock_file, mock_chrome
    ):
        from ww.crawler.weibo import scrape_weibo

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html></html>"
        mock_driver.find_elements.return_value = []

        with patch("ww.crawler.weibo.WebDriverWait") as mock_wait:
            mock_wait_instance = MagicMock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.side_effect = [None, Exception("timeout")]

            result = scrape_weibo("https://weibo.com/u/123")

        self.assertEqual(result, [])

    @patch("ww.crawler.weibo.webdriver.Chrome")
    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.dirname", return_value="/tmp")
    @patch("os.path.abspath", return_value="/tmp/weibo.py")
    def test_with_end_time(
        self, mock_abspath, mock_dirname, mock_exists, mock_file, mock_chrome
    ):
        from ww.crawler.weibo import scrape_weibo

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html></html>"
        mock_driver.find_elements.return_value = []

        with patch("ww.crawler.weibo.WebDriverWait") as mock_wait:
            mock_wait_instance = MagicMock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.side_effect = [None, Exception("timeout")]

            result = scrape_weibo("https://weibo.com/u/123", end_time=1737561600)

        # Verify the URL was modified with end_time parameter
        first_get_call = mock_driver.get.call_args_list[0][0][0]
        self.assertIn("end_time=1737561600", first_get_call)

    @patch("ww.crawler.weibo.webdriver.Chrome")
    def test_critical_error(self, mock_chrome):
        from ww.crawler.weibo import scrape_weibo

        mock_chrome.side_effect = Exception("Chrome not found")
        result = scrape_weibo("https://weibo.com/u/123")
        self.assertIsNone(result)

    @patch("ww.crawler.weibo.webdriver.Chrome")
    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("os.path.exists", return_value=True)
    @patch("os.path.dirname", return_value="/tmp")
    @patch("os.path.abspath", return_value="/tmp/weibo.py")
    def test_with_posts(
        self, mock_abspath, mock_dirname, mock_exists, mock_file, mock_chrome
    ):
        from ww.crawler.weibo import scrape_weibo

        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_driver.page_source = "<html></html>"
        mock_driver.find_elements.return_value = []

        # Create a mock post element
        mock_post = MagicMock()
        mock_text_div = MagicMock()
        mock_text_div.get_text.return_value = "Hello World"
        mock_post.find.return_value = mock_text_div
        mock_post.select.return_value = []
        mock_post.select_one.return_value = None
        mock_from_link = MagicMock()
        mock_from_link.get_text.return_value = "2024-01-01"

        def post_find(tag, class_=None):
            if class_ == "weibo-text":
                return mock_text_div
            if class_ == "from":
                return mock_from_link
            return None

        mock_post.find.side_effect = post_find

        mock_soup = MagicMock()
        mock_soup.find_all.return_value = [mock_post]

        with (
            patch("ww.crawler.weibo.WebDriverWait") as mock_wait,
            patch("ww.crawler.weibo.BeautifulSoup", return_value=mock_soup),
        ):
            mock_wait_instance = MagicMock()
            mock_wait.return_value = mock_wait_instance
            mock_wait_instance.until.side_effect = [None, None]

            result = scrape_weibo("https://weibo.com/u/123")

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["text"], "Hello World")


if __name__ == "__main__":
    unittest.main()
