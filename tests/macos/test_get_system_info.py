import os
import subprocess
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRunCommand(unittest.TestCase):
    @patch("ww.macos.get_system_info.subprocess.run")
    def test_returns_stdout_on_success(self, mock_run):
        from ww.macos.get_system_info import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="hello\n")
        self.assertEqual(run_command("echo hello"), "hello")

    @patch("ww.macos.get_system_info.subprocess.run")
    def test_returns_fallback_on_failure(self, mock_run):
        from ww.macos.get_system_info import run_command

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertEqual(run_command("bad", fallback="fb"), "fb")

    @patch("ww.macos.get_system_info.subprocess.run", side_effect=FileNotFoundError)
    def test_returns_fallback_on_error(self, mock_run):
        from ww.macos.get_system_info import run_command

        self.assertEqual(run_command("nope", fallback="x"), "x")

    @patch("ww.macos.get_system_info.subprocess.run")
    def test_returns_none_without_fallback(self, mock_run):
        from ww.macos.get_system_info import run_command

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertIsNone(run_command("fail"))


class TestGetOsInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.subprocess.run")
    def test_parses_sw_vers(self, mock_run):
        from ww.macos.get_system_info import get_os_info

        stdout = (
            "ProductName:\t\tmacOS\nProductVersion:\t\t14.2\nBuildVersion:\t\t23C64\n"
        )
        mock_run.return_value = MagicMock(returncode=0, stdout=stdout)
        result = get_os_info()
        self.assertEqual(result, "macOS 14.2 (Build 23C64)")

    @patch("ww.macos.get_system_info.run_command", return_value="Darwin 23.0.0 arm64")
    @patch(
        "ww.macos.get_system_info.subprocess.run",
        side_effect=subprocess.TimeoutExpired("sw_vers", 5),
    )
    def test_falls_back_to_uname(self, mock_run, mock_rc):
        from ww.macos.get_system_info import get_os_info

        result = get_os_info()
        self.assertEqual(result, "Darwin 23.0.0 arm64")

    @patch("ww.macos.get_system_info.subprocess.run")
    def test_returns_uname_on_nonzero(self, mock_run):
        from ww.macos.get_system_info import get_os_info

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        with patch("ww.macos.get_system_info.run_command", return_value="Darwin x"):
            result = get_os_info()
            self.assertEqual(result, "Darwin x")


class TestGetArchitecture(unittest.TestCase):
    @patch("ww.macos.get_system_info.platform.machine", return_value="x86_64")
    def test_intel(self, mock_machine):
        from ww.macos.get_system_info import get_architecture

        self.assertEqual(get_architecture(), "Intel 64-bit")

    @patch("ww.macos.get_system_info.platform.machine", return_value="arm64")
    def test_apple_silicon(self, mock_machine):
        from ww.macos.get_system_info import get_architecture

        self.assertEqual(get_architecture(), "Apple Silicon 64-bit")

    @patch("ww.macos.get_system_info.platform.machine", return_value="i386")
    def test_other(self, mock_machine):
        from ww.macos.get_system_info import get_architecture

        result = get_architecture()
        self.assertIn("i386", result)


class TestGetPythonVersion(unittest.TestCase):
    def test_returns_version_string(self):
        from ww.macos.get_system_info import get_python_version

        parts = get_python_version().split(".")
        self.assertEqual(len(parts), 3)


class TestGetJavaVersion(unittest.TestCase):
    @patch("ww.macos.get_system_info.run_command")
    def test_parses_quoted_version(self, mock_rc):
        from ww.macos.get_system_info import get_java_version

        mock_rc.return_value = 'openjdk version "21.0.1"'
        self.assertEqual(get_java_version(), "21.0.1")

    @patch("ww.macos.get_system_info.run_command", return_value=None)
    def test_not_found(self, mock_rc):
        from ww.macos.get_system_info import get_java_version

        self.assertEqual(get_java_version(), "Java not found")

    @patch("ww.macos.get_system_info.run_command")
    def test_parses_unquoted_version(self, mock_rc):
        from ww.macos.get_system_info import get_java_version

        mock_rc.return_value = "java version 11.0.2 extra"
        self.assertEqual(get_java_version(), "11.0.2")


class TestGetMacosUiInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.run_command", return_value="Dark")
    @patch.dict(os.environ, {"DISPLAY": ":0"}, clear=False)
    def test_dark_mode_gui(self, mock_rc):
        from ww.macos.get_system_info import get_macos_ui_info

        result = get_macos_ui_info()
        self.assertIn("Dark Mode", result)
        self.assertIn("GUI Session", result)

    @patch("ww.macos.get_system_info.run_command", return_value=None)
    @patch.dict(
        os.environ, {"TERM_PROGRAM": "Apple_Terminal", "DISPLAY": ""}, clear=False
    )
    def test_light_mode_console(self, mock_rc):
        from ww.macos.get_system_info import get_macos_ui_info

        result = get_macos_ui_info()
        self.assertIn("Light Mode", result)
        self.assertIn("Console Session", result)


class TestGetKernelInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.run_command", return_value="23.0.0")
    def test_returns_kernel(self, mock_rc):
        from ww.macos.get_system_info import get_kernel_info

        self.assertEqual(get_kernel_info(), "23.0.0")


class TestGetDiskInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.subprocess.run")
    def test_parses_disk(self, mock_run):
        from ww.macos.get_system_info import get_disk_info

        stdout = "Filesystem     Size   Used  Avail Capacity  Mounted on\n/dev/disk1     100G    50G    45G    53%    /\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=stdout)
        result = get_disk_info()
        self.assertIn("Total: 100G", result)

    @patch(
        "ww.macos.get_system_info.subprocess.run",
        side_effect=subprocess.TimeoutExpired("df -h /", 5),
    )
    def test_error(self, mock_run):
        from ww.macos.get_system_info import get_disk_info

        self.assertEqual(get_disk_info(), "Unable to retrieve disk information")

    @patch("ww.macos.get_system_info.subprocess.run")
    def test_failure_returncode(self, mock_run):
        from ww.macos.get_system_info import get_disk_info

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertEqual(
            get_disk_info(),
            "Unable to retrieve memory information"
            if False
            else "Unable to retrieve disk information",
        )


class TestGetMemoryInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.run_command")
    def test_parses_memory(self, mock_rc):
        from ww.macos.get_system_info import get_memory_info

        mock_rc.side_effect = [
            str(16 * 1024**3),  # hw.memsize
            "0",  # pressure
            "Pages free: 100000.\nPages active: 50000.\nPages wired down: 30000.\n",  # vm_stat
        ]
        result = get_memory_info()
        self.assertIn("Total: 16.0 GB", result)
        self.assertIn("Used:", result)

    @patch("ww.macos.get_system_info.run_command", return_value=None)
    def test_unable_to_retrieve(self, mock_rc):
        from ww.macos.get_system_info import get_memory_info

        result = get_memory_info()
        self.assertEqual(result, "Unable to retrieve memory information")


class TestGetGpuInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.run_command")
    def test_detects_apple_gpu(self, mock_rc):
        from ww.macos.get_system_info import get_gpu_info

        mock_rc.side_effect = [
            None,
            None,
            None,
            "Apple M1 Pro\nChipset Model: Apple M1 Pro",
        ]
        result = get_gpu_info()
        self.assertIn("Apple Silicon GPU", result)

    @patch("ww.macos.get_system_info.run_command", return_value=None)
    def test_no_gpu(self, mock_rc):
        from ww.macos.get_system_info import get_gpu_info

        result = get_gpu_info()
        self.assertEqual(result, "Unable to detect GPU information")

    @patch("ww.macos.get_system_info.run_command")
    def test_intel_gpu(self, mock_rc):
        from ww.macos.get_system_info import get_gpu_info

        mock_rc.side_effect = ["Intel UHD Graphics 630", None, None, None]
        result = get_gpu_info()
        self.assertIn("Intel Integrated Graphics", result)


class TestGetMacosHardwareInfo(unittest.TestCase):
    @patch("ww.macos.get_system_info.run_command")
    def test_full_info(self, mock_rc):
        from ww.macos.get_system_info import get_macos_hardware_info

        mock_rc.side_effect = ["MacBookPro18,3", "Apple M1 Pro", "10", "C02X1234"]
        result = get_macos_hardware_info()
        self.assertIn("Model: MacBookPro18,3", result)
        self.assertIn("CPU: Apple M1 Pro", result)
        self.assertIn("Cores: 10", result)
        self.assertIn("Serial: C02X1234", result)

    @patch("ww.macos.get_system_info.run_command", return_value=None)
    def test_no_info(self, mock_rc):
        from ww.macos.get_system_info import get_macos_hardware_info

        result = get_macos_hardware_info()
        self.assertEqual(result, "Unable to retrieve hardware info")


class TestMain(unittest.TestCase):
    @patch("ww.macos.get_system_info.get_gpu_info", return_value="GPU ok")
    @patch("ww.macos.get_system_info.get_memory_info", return_value="Mem ok")
    @patch("ww.macos.get_system_info.get_disk_info", return_value="Disk ok")
    @patch("ww.macos.get_system_info.get_macos_ui_info", return_value="UI ok")
    @patch("ww.macos.get_system_info.get_java_version", return_value="17")
    @patch("ww.macos.get_system_info.get_python_version", return_value="3.14")
    @patch("ww.macos.get_system_info.get_macos_hardware_info", return_value="HW ok")
    @patch("ww.macos.get_system_info.get_kernel_info", return_value="23.0")
    @patch("ww.macos.get_system_info.get_architecture", return_value="Apple Silicon")
    @patch("ww.macos.get_system_info.get_os_info", return_value="macOS 14.2")
    def test_main_runs(self, *mocks):
        from ww.macos.get_system_info import main

        main()  # should not raise


if __name__ == "__main__":
    unittest.main()
