import os
import tempfile
import unittest
import shutil

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.java.analyze_packages import extract_package, find_java_files


class TestExtractPackage(unittest.TestCase):
    def test_regular_import(self):
        self.assertEqual(
            extract_package("import com.example.MyClass;"),
            "com.example",
        )

    def test_star_import(self):
        self.assertEqual(
            extract_package("import java.util.*;"),
            "java.util",
        )

    def test_static_import(self):
        self.assertEqual(
            extract_package("import static org.junit.Assert.*;"),
            "org.junit",
        )

    def test_static_import_specific(self):
        self.assertEqual(
            extract_package("import static org.junit.Assert.assertEquals;"),
            "org.junit",
        )

    def test_single_class_import(self):
        self.assertEqual(
            extract_package("import java.util.List;"),
            "java.util",
        )

    def test_deep_package(self):
        result = extract_package("import com.google.common.collect.ImmutableList;")
        self.assertEqual(result, "com.google.common.collect")

    def test_import_without_semicolon(self):
        result = extract_package("import com.example.Foo")
        self.assertEqual(result, "com.example")

    def test_no_import_keyword(self):
        # When "import" keyword is missing, first token is the package path
        result = extract_package("com.example.MyClass;")
        self.assertEqual(result, "com.example")


class TestFindJavaFiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _touch(self, rel_path):
        full = os.path.join(self.tmpdir, rel_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        open(full, "w").close()
        return full

    def test_finds_java_files(self):
        self._touch("src/Main.java")
        self._touch("src/Utils.java")
        result = list(find_java_files(self.tmpdir))
        self.assertEqual(len(result), 2)
        self.assertTrue(all(f.endswith(".java") for f in result))

    def test_ignores_non_java_files(self):
        self._touch("src/Main.java")
        self._touch("src/readme.txt")
        self._touch("src/build.xml")
        result = list(find_java_files(self.tmpdir))
        self.assertEqual(len(result), 1)

    def test_finds_nested_files(self):
        self._touch("src/com/example/Foo.java")
        self._touch("src/com/example/bar/Baz.java")
        result = list(find_java_files(self.tmpdir))
        self.assertEqual(len(result), 2)

    def test_empty_directory(self):
        result = list(find_java_files(self.tmpdir))
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
