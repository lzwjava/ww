import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestDeduplicate(unittest.TestCase):
    def test_removes_duplicate_domain_title_pairs(self):
        from ww.search.search_web import _deduplicate

        results = [
            {"title": "Same", "url": "https://example.com/a"},
            {"title": "Same", "url": "https://example.com/b"},
        ]
        deduped = _deduplicate(results)
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["url"], "https://example.com/a")

    def test_keeps_same_domain_different_titles(self):
        from ww.search.search_web import _deduplicate

        results = [
            {"title": "Title A", "url": "https://example.com/a"},
            {"title": "Title B", "url": "https://example.com/b"},
        ]
        deduped = _deduplicate(results)
        self.assertEqual(len(deduped), 2)

    def test_keeps_different_domains_same_title(self):
        from ww.search.search_web import _deduplicate

        results = [
            {"title": "Same", "url": "https://a.com/page"},
            {"title": "Same", "url": "https://b.com/page"},
        ]
        deduped = _deduplicate(results)
        self.assertEqual(len(deduped), 2)

    def test_empty_results(self):
        from ww.search.search_web import _deduplicate

        self.assertEqual(_deduplicate([]), [])

    def test_preserves_order(self):
        from ww.search.search_web import _deduplicate

        results = [
            {"title": "A", "url": "https://x.com/a"},
            {"title": "B", "url": "https://y.com/b"},
            {"title": "A", "url": "https://x.com/c"},
        ]
        deduped = _deduplicate(results)
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["title"], "A")
        self.assertEqual(deduped[1]["title"], "B")


class TestSearchBing(unittest.TestCase):
    @patch("ww.search.search_web.requests.Session")
    def test_returns_parsed_results(self, mock_session_cls):
        from ww.search.search_web import search_bing

        html = """
        <html><body>
        <li class="b_algo"><h2><a href="https://example.com">Example</a></h2></li>
        <li class="b_algo"><h2><a href="https://test.com">Test</a></h2></li>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        results = search_bing("test query", num_results=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Example")
        self.assertEqual(results[0]["url"], "https://example.com")

    @patch("ww.search.search_web.requests.Session")
    def test_handles_relative_protocol(self, mock_session_cls):
        from ww.search.search_web import search_bing

        html = """
        <html><body>
        <li class="b_algo"><h2><a href="//example.com/page">Example</a></h2></li>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        results = search_bing("query")
        self.assertEqual(results[0]["url"], "https://example.com/page")

    @patch("ww.search.search_web.requests.Session")
    def test_returns_empty_on_exception(self, mock_session_cls):
        from ww.search.search_web import search_bing

        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("network error")
        mock_session_cls.return_value = mock_session

        results = search_bing("query")
        self.assertEqual(results, [])

    @patch("ww.search.search_web.requests.Session")
    def test_respects_num_results(self, mock_session_cls):
        from ww.search.search_web import search_bing

        items = "".join(
            f'<li class="b_algo"><h2><a href="https://example{i}.com">T{i}</a></h2></li>'
            for i in range(10)
        )
        html = f"<html><body>{items}</body></html>"

        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()

        mock_session = MagicMock()
        mock_session.get.return_value = mock_resp
        mock_session_cls.return_value = mock_session

        results = search_bing("query", num_results=3)
        self.assertEqual(len(results), 3)


class TestSearchDdg(unittest.TestCase):
    @patch("ww.search.search_web.requests.get")
    def test_returns_parsed_results(self, mock_get):
        from ww.search.search_web import search_ddg

        html = """
        <html><body>
        <div class="result__title">
            <a class="result__a" href="https://example.com">Example</a>
        </div>
        <div class="result__title">
            <a class="result__a" href="https://test.com">Test</a>
        </div>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_ddg("query", num_results=10)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["title"], "Example")

    @patch("ww.search.search_web.requests.get")
    def test_resolves_ddg_redirect_urls(self, mock_get):
        from ww.search.search_web import search_ddg

        html = """
        <html><body>
        <div class="result__title">
            <a class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage">Example</a>
        </div>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_ddg("query")
        self.assertEqual(results[0]["url"], "https://example.com/page")

    @patch("ww.search.search_web.requests.get")
    def test_returns_empty_on_exception(self, mock_get):
        from ww.search.search_web import search_ddg

        mock_get.side_effect = Exception("timeout")
        results = search_ddg("query")
        self.assertEqual(results, [])

    @patch("ww.search.search_web.requests.get")
    def test_returns_empty_on_captcha(self, mock_get):
        from ww.search.search_web import search_ddg

        mock_resp = MagicMock()
        mock_resp.text = "<html>anomaly-modal</html>"
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_ddg("query")
        self.assertEqual(results, [])


class TestSearchStartpage(unittest.TestCase):
    @patch("ww.search.search_web.requests.get")
    def test_returns_parsed_results(self, mock_get):
        from ww.search.search_web import search_startpage

        html = """
        <html><body>
        <div class="result">
            <a class="result-link" href="https://example.com">link</a>
            <span class="wgl-title">Example Title</span>
        </div>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_startpage("query", num_results=10)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Example Title")
        self.assertEqual(results[0]["url"], "https://example.com")

    @patch("ww.search.search_web.requests.get")
    def test_skips_items_without_link_or_title(self, mock_get):
        from ww.search.search_web import search_startpage

        html = """
        <html><body>
        <div class="result">
            <span class="wgl-title">No Link</span>
        </div>
        <div class="result">
            <a class="result-link" href="https://example.com">link</a>
        </div>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = search_startpage("query")
        self.assertEqual(len(results), 0)

    @patch("ww.search.search_web.requests.get")
    def test_returns_empty_on_exception(self, mock_get):
        from ww.search.search_web import search_startpage

        mock_get.side_effect = Exception("network error")
        results = search_startpage("query")
        self.assertEqual(results, [])


class TestWebSearch(unittest.TestCase):
    @patch("ww.search.search_web.fetch_results_parallel")
    def test_returns_no_results_message(self, mock_fetch):
        from ww.search.search_web import web_search

        mock_ddg = MagicMock(return_value=[])
        with patch.dict("ww.search.search_web.ENGINES", {"ddg": mock_ddg}):
            result = web_search("query")
            self.assertEqual(result, "No results found.")

    @patch("ww.search.search_web.fetch_results_parallel")
    def test_calls_deduplicate_and_fetch(self, mock_fetch):
        from ww.search.search_web import web_search

        mock_ddg = MagicMock(
            return_value=[
                {"title": "T", "url": "https://example.com"},
            ]
        )
        with patch.dict("ww.search.search_web.ENGINES", {"ddg": mock_ddg}):
            mock_fetch.return_value = [
                {"title": "T", "url": "https://example.com", "content": "text"},
            ]
            result = web_search("query", provider="ddg")
            self.assertIn("Source 1", result)
            mock_fetch.assert_called_once()

    @patch("ww.search.search_web.fetch_results_parallel")
    def test_uses_specified_provider(self, mock_fetch):
        from ww.search.search_web import web_search

        mock_bing = MagicMock(
            return_value=[
                {"title": "T", "url": "https://example.com"},
            ]
        )
        with patch.dict("ww.search.search_web.ENGINES", {"bing": mock_bing}):
            mock_fetch.return_value = [
                {"title": "T", "url": "https://example.com", "content": "text"},
            ]
            result = web_search("query", provider="bing")
            mock_bing.assert_called_once()


if __name__ == "__main__":
    unittest.main()
