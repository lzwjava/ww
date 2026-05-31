"""Tests for note queue and watcher — file-based queue operations."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestContentHash(unittest.TestCase):
    def test_returns_12_char_hex(self):
        from ww.note.note_queue import content_hash

        h = content_hash("hello world")
        self.assertEqual(len(h), 12)
        # Should be hex
        int(h, 16)

    def test_deterministic(self):
        from ww.note.note_queue import content_hash

        self.assertEqual(content_hash("abc"), content_hash("abc"))

    def test_different_inputs_different_hashes(self):
        from ww.note.note_queue import content_hash

        self.assertNotEqual(content_hash("abc"), content_hash("def"))


class TestQueueOperations(unittest.TestCase):
    """Test queue load/save/enqueue using a temp directory."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.queue_file = Path(self.tmpdir) / "note_queue.json"

    def _patch_queue_file(self):
        return patch("ww.note.note_queue._queue_file", return_value=self.queue_file)

    def test_load_queue_missing_file(self):
        from ww.note.note_queue import _load_queue

        with self._patch_queue_file():
            result = _load_queue()
            self.assertEqual(result, [])

    def test_load_queue_corrupt_json(self):
        self.queue_file.write_text("not json{{{")
        from ww.note.note_queue import _load_queue

        with self._patch_queue_file():
            result = _load_queue()
            self.assertEqual(result, [])

    def test_save_and_load_roundtrip(self):
        from ww.note.note_queue import _load_queue, _save_queue

        entries = [{"id": "abc", "status": "pending", "content": "test"}]
        with self._patch_queue_file():
            _save_queue(entries)
            loaded = _load_queue()
            self.assertEqual(loaded, entries)

    def test_save_atomic(self):
        """_save_queue writes to .tmp then renames — no partial writes."""
        from ww.note.note_queue import _save_queue

        entries = [{"id": "x", "status": "done"}]
        with self._patch_queue_file():
            _save_queue(entries)
            # .tmp should not exist after rename
            tmp = self.queue_file.with_suffix(".tmp")
            self.assertFalse(tmp.exists())
            self.assertTrue(self.queue_file.exists())


class TestEnqueueClipboard(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.queue_file = Path(self.tmpdir) / "note_queue.json"

    def _patch_queue_file(self):
        return patch("ww.note.note_queue._queue_file", return_value=self.queue_file)

    def test_empty_clipboard_returns_none(self):
        from ww.note.note_queue import enqueue_clipboard

        with (
            self._patch_queue_file(),
            patch("ww.note.note_queue._get_clipboard", return_value=""),
        ):
            result = enqueue_clipboard()
            self.assertIsNone(result)

    def test_short_clipboard_returns_none(self):
        from ww.note.note_queue import enqueue_clipboard

        with (
            self._patch_queue_file(),
            patch("ww.note.note_queue._get_clipboard", return_value="short"),
        ):
            result = enqueue_clipboard()
            self.assertIsNone(result)

    def test_valid_clipboard_enqueued(self):
        from ww.note.note_queue import enqueue_clipboard, _load_queue

        long_text = "x" * 250
        with (
            self._patch_queue_file(),
            patch("ww.note.note_queue._get_clipboard", return_value=long_text),
        ):
            entry_id = enqueue_clipboard()
            self.assertIsNotNone(entry_id)
            queue = _load_queue()
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["status"], "pending")
            self.assertEqual(queue[0]["content"], long_text)

    def test_duplicate_pending_skipped(self):
        from ww.note.note_queue import enqueue_clipboard, _load_queue

        long_text = "y" * 250
        with (
            self._patch_queue_file(),
            patch("ww.note.note_queue._get_clipboard", return_value=long_text),
        ):
            enqueue_clipboard()
            result = enqueue_clipboard()  # duplicate
            self.assertIsNone(result)
            queue = _load_queue()
            self.assertEqual(len(queue), 1)


class TestMarkDoneFailed(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.queue_file = Path(self.tmpdir) / "note_queue.json"

    def _patch_queue_file(self):
        return patch("ww.note.note_queue._queue_file", return_value=self.queue_file)

    def test_mark_done(self):
        from ww.note.note_queue import _save_queue, _load_queue, mark_done

        entries = [{"id": "abc", "status": "pending", "content": "test"}]
        with self._patch_queue_file():
            _save_queue(entries)
            mark_done("abc", "/notes/test.md")
            queue = _load_queue()
            self.assertEqual(queue[0]["status"], "done")
            self.assertEqual(queue[0]["note_path"], "/notes/test.md")
            self.assertIn("processed_at", queue[0])

    def test_mark_failed(self):
        from ww.note.note_queue import _save_queue, _load_queue, mark_failed

        entries = [{"id": "abc", "status": "pending", "content": "test"}]
        with self._patch_queue_file():
            _save_queue(entries)
            mark_failed("abc", "API error")
            queue = _load_queue()
            self.assertEqual(queue[0]["status"], "failed")
            self.assertEqual(queue[0]["error"], "API error")
            self.assertIn("failed_at", queue[0])


class TestClearDone(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.queue_file = Path(self.tmpdir) / "note_queue.json"

    def _patch_queue_file(self):
        return patch("ww.note.note_queue._queue_file", return_value=self.queue_file)

    def test_clear_removes_done_and_failed(self):
        from ww.note.note_queue import _save_queue, clear_done, _load_queue

        entries = [
            {"id": "a", "status": "pending", "content": "x"},
            {"id": "b", "status": "done", "content": "y"},
            {"id": "c", "status": "failed", "content": "z"},
        ]
        with self._patch_queue_file():
            _save_queue(entries)
            removed = clear_done()
            self.assertEqual(removed, 2)
            queue = _load_queue()
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0]["id"], "a")

    def test_clear_empty_queue(self):
        from ww.note.note_queue import clear_done

        with self._patch_queue_file():
            removed = clear_done()
            self.assertEqual(removed, 0)


class TestGetPending(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.queue_file = Path(self.tmpdir) / "note_queue.json"

    def _patch_queue_file(self):
        return patch("ww.note.note_queue._queue_file", return_value=self.queue_file)

    def test_filters_pending_only(self):
        from ww.note.note_queue import _save_queue, get_pending

        entries = [
            {"id": "a", "status": "pending", "content": "x"},
            {"id": "b", "status": "done", "content": "y"},
        ]
        with self._patch_queue_file():
            _save_queue(entries)
            pending = get_pending()
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["id"], "a")


class TestWatcherFileHash(unittest.TestCase):
    def test_file_hash_deterministic(self):
        from ww.note.note_watcher import _file_hash

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"test": true}')
            f.flush()
            path = Path(f.name)

        try:
            h1 = _file_hash(path)
            h2 = _file_hash(path)
            self.assertEqual(h1, h2)
            self.assertEqual(len(h1), 32)  # MD5 hex
        finally:
            path.unlink()

    def test_file_hash_missing_file(self):
        from ww.note.note_watcher import _file_hash

        result = _file_hash(Path("/nonexistent/file.json"))
        self.assertEqual(result, "")

    def test_file_hash_detects_change(self):
        from ww.note.note_watcher import _file_hash

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"version": 1}')
            f.flush()
            path = Path(f.name)

        try:
            h1 = _file_hash(path)
            path.write_text('{"version": 2}')
            h2 = _file_hash(path)
            self.assertNotEqual(h1, h2)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
