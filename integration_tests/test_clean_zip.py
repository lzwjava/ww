import unittest
import tempfile
import zipfile
import os
from integration_tests.helpers import run_ww


class TestCleanZipCommand(unittest.TestCase):
    def test_clean_zip_removes_extensionless(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            temp_zip = tf.name

        try:
            with zipfile.ZipFile(temp_zip, "w") as zf:
                zf.writestr("file.txt", "content")
                zf.writestr("README", "no extension")
                zf.writestr("data/dat.json", '{"key": "value"}')

            returncode, stdout, stderr = run_ww("utils", "clean-zip", temp_zip)
            self.assertEqual(returncode, 0, stderr)

            output_zip = temp_zip.replace(".zip", "_output.zip")
            self.assertTrue(os.path.exists(output_zip))

            with zipfile.ZipFile(output_zip, "r") as zf:
                names = zf.namelist()
            self.assertIn("file.txt", names)
            self.assertIn("data/dat.json", names)
            self.assertNotIn("README", names)
        finally:
            os.unlink(temp_zip)
            output_zip = temp_zip.replace(".zip", "_output.zip")
            if os.path.exists(output_zip):
                os.unlink(output_zip)


if __name__ == "__main__":
    unittest.main()
