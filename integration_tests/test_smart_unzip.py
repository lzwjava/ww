import unittest
import tempfile
import zipfile
import os
from integration_tests.helpers import run_ww


class TestSmartUnzipCommand(unittest.TestCase):
    def test_smart_unzip_renames_extensionless(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
            temp_zip = tf.name

        try:
            with zipfile.ZipFile(temp_zip, "w") as zf:
                zf.writestr("file.txt", "content")
                zf.writestr("README", "no extension")

            returncode, stdout, stderr = run_ww("utils", "smart-unzip", temp_zip)
            self.assertEqual(returncode, 0, stderr)

            output_zip = temp_zip.replace(".zip", "_processed.zip")
            self.assertTrue(os.path.exists(output_zip))

            with zipfile.ZipFile(output_zip, "r") as zf:
                names = zf.namelist()
            self.assertIn("file.txt", names)
            self.assertIn("README.unknown", names)
        finally:
            os.unlink(temp_zip)
            output_zip = temp_zip.replace(".zip", "_processed.zip")
            if os.path.exists(output_zip):
                os.unlink(output_zip)
            extract_dir = temp_zip.replace(".zip", "_unzipped")
            if os.path.exists(extract_dir):
                for f in os.listdir(extract_dir):
                    os.unlink(os.path.join(extract_dir, f))
                os.rmdir(extract_dir)


if __name__ == "__main__":
    unittest.main()
