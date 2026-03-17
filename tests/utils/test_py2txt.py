import os
import shutil
import tempfile
import unittest

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestConvertFilesToTxt(unittest.TestCase):
    def setUp(self):
        self.source_dir = tempfile.mkdtemp()
        self.dest_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.source_dir, ignore_errors=True)
        shutil.rmtree(self.dest_dir, ignore_errors=True)

    def test_copies_files_with_txt_extension(self):
        from ww.utils.py2txt import convert_files_to_txt

        open(os.path.join(self.source_dir, "hello.py"), "w").close()
        convert_files_to_txt(self.source_dir, self.dest_dir)
        self.assertTrue(os.path.exists(os.path.join(self.dest_dir, "hello.txt")))

    def test_creates_dest_dir_if_missing(self):
        from ww.utils.py2txt import convert_files_to_txt

        new_dest = os.path.join(self.dest_dir, "new_subdir")
        open(os.path.join(self.source_dir, "a.py"), "w").close()
        convert_files_to_txt(self.source_dir, new_dest)
        self.assertTrue(os.path.isdir(new_dest))

    def test_strips_original_extension(self):
        from ww.utils.py2txt import convert_files_to_txt

        open(os.path.join(self.source_dir, "script.py"), "w").close()
        convert_files_to_txt(self.source_dir, self.dest_dir)
        self.assertFalse(os.path.exists(os.path.join(self.dest_dir, "script.py.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.dest_dir, "script.txt")))

    def test_handles_empty_source_dir(self):
        from ww.utils.py2txt import convert_files_to_txt

        convert_files_to_txt(self.source_dir, self.dest_dir)
        self.assertEqual(os.listdir(self.dest_dir), [])

    def test_copies_multiple_files(self):
        from ww.utils.py2txt import convert_files_to_txt

        for name in ["a.py", "b.md", "c.js"]:
            open(os.path.join(self.source_dir, name), "w").close()
        convert_files_to_txt(self.source_dir, self.dest_dir)
        result = os.listdir(self.dest_dir)
        self.assertIn("a.txt", result)
        self.assertIn("b.txt", result)
        self.assertIn("c.txt", result)

    def test_ignores_subdirectories(self):
        from ww.utils.py2txt import convert_files_to_txt

        os.makedirs(os.path.join(self.source_dir, "subdir"))
        open(os.path.join(self.source_dir, "file.py"), "w").close()
        convert_files_to_txt(self.source_dir, self.dest_dir)
        result = os.listdir(self.dest_dir)
        self.assertNotIn("subdir.txt", result)
        self.assertIn("file.txt", result)


class TestPy2TxtMain(unittest.TestCase):
    def setUp(self):
        self.source_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.source_dir, ignore_errors=True)
        txt_dir = os.path.join(self.source_dir, "txt")
        shutil.rmtree(txt_dir, ignore_errors=True)

    def test_main_uses_default_dest_dir(self):
        from ww.utils.py2txt import main
        import sys
        from unittest.mock import patch

        open(os.path.join(self.source_dir, "test.py"), "w").close()
        with patch.object(sys, "argv", ["py2txt", self.source_dir]):
            main()
        self.assertTrue(
            os.path.exists(os.path.join(self.source_dir, "txt", "test.txt"))
        )

    def test_main_uses_explicit_dest_dir(self):
        from ww.utils.py2txt import main
        import sys
        from unittest.mock import patch

        dest = tempfile.mkdtemp()
        try:
            open(os.path.join(self.source_dir, "file.py"), "w").close()
            with patch.object(sys, "argv", ["py2txt", self.source_dir, dest]):
                main()
            self.assertTrue(os.path.exists(os.path.join(dest, "file.txt")))
        finally:
            shutil.rmtree(dest, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
