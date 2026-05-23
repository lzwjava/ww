import os
import subprocess
import unittest
from unittest.mock import patch, MagicMock, mock_open

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")


class TestRunCommand(unittest.TestCase):
    @patch("ww.linux.system.subprocess.run")
    def test_returns_stdout_on_success(self, mock_run):
        from ww.linux.system import run_command

        mock_run.return_value = MagicMock(returncode=0, stdout="hello world\n")
        result = run_command("echo hello world")
        self.assertEqual(result, "hello world")
        mock_run.assert_called_once()

    @patch("ww.linux.system.subprocess.run")
    def test_returns_fallback_on_nonzero(self, mock_run):
        from ww.linux.system import run_command

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = run_command("bad_cmd", fallback="default")
        self.assertEqual(result, "default")

    @patch("ww.linux.system.subprocess.run", side_effect=FileNotFoundError)
    def test_returns_fallback_on_file_not_found(self, mock_run):
        from ww.linux.system import run_command

        result = run_command("nonexistent", fallback="fb")
        self.assertEqual(result, "fb")

    @patch("ww.linux.system.subprocess.run")
    def test_returns_fallback_on_timeout(self, mock_run):
        import subprocess as sp
        from ww.linux.system import run_command

        mock_run.side_effect = sp.TimeoutExpired("cmd", 5)
        result = run_command("slow_cmd", fallback="timeout_fb")
        self.assertEqual(result, "timeout_fb")

    @patch("ww.linux.system.subprocess.run")
    def test_returns_none_when_no_fallback(self, mock_run):
        from ww.linux.system import run_command

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = run_command("fail")
        self.assertIsNone(result)


class TestGetOsInfo(unittest.TestCase):
    @patch(
        "builtins.open",
        mock_open(read_data='PRETTY_NAME="Ubuntu 22.04"\nNAME="Ubuntu"\n'),
    )
    def test_reads_pretty_name(self):
        from ww.linux.system import get_os_info

        result = get_os_info()
        self.assertEqual(result, "Ubuntu 22.04")

    @patch("builtins.open", mock_open(read_data='NAME="Ubuntu"\nVERSION="22.04"\n'))
    def test_falls_back_to_name_version(self):
        from ww.linux.system import get_os_info

        result = get_os_info()
        self.assertEqual(result, "Ubuntu 22.04")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("ww.linux.system.run_command", return_value="Ubuntu 22.04")
    def test_falls_back_to_lsb_release(self, mock_rc, mock_fo):
        from ww.linux.system import get_os_info

        result = get_os_info()
        self.assertEqual(result, "Ubuntu 22.04")

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("ww.linux.system.run_command", return_value=None)
    def test_returns_unknown_when_nothing_found(self, mock_rc, mock_fo):
        from ww.linux.system import get_os_info

        result = get_os_info()
        self.assertEqual(result, "Unknown")


class TestGetArchitecture(unittest.TestCase):
    @patch("ww.linux.system.platform.machine", return_value="x86_64")
    def test_x86_64(self, mock_machine):
        from ww.linux.system import get_architecture

        self.assertEqual(get_architecture(), "64-bit")

    @patch("ww.linux.system.platform.machine", return_value="amd64")
    def test_amd64(self, mock_machine):
        from ww.linux.system import get_architecture

        self.assertEqual(get_architecture(), "64-bit")

    @patch("ww.linux.system.platform.machine", return_value="i686")
    def test_i686(self, mock_machine):
        from ww.linux.system import get_architecture

        self.assertEqual(get_architecture(), "32-bit")

    @patch("ww.linux.system.platform.machine", return_value="aarch64")
    def test_aarch64(self, mock_machine):
        from ww.linux.system import get_architecture

        result = get_architecture()
        self.assertIn("aarch64", result)
        self.assertIn("64-bit", result)


class TestGetPythonVersion(unittest.TestCase):
    def test_returns_version_string(self):
        from ww.linux.system import get_python_version

        result = get_python_version()
        parts = result.split(".")
        self.assertEqual(len(parts), 3)
        for p in parts:
            self.assertTrue(p.isdigit())


class TestGetJavaVersion(unittest.TestCase):
    @patch("ww.linux.system.run_command")
    def test_parses_java_version_with_quotes(self, mock_rc):
        from ww.linux.system import get_java_version

        mock_rc.return_value = 'openjdk version "17.0.1" 2021-10-19'
        result = get_java_version()
        self.assertEqual(result, "17.0.1")

    @patch("ww.linux.system.run_command", return_value=None)
    def test_returns_not_found(self, mock_rc):
        from ww.linux.system import get_java_version

        result = get_java_version()
        self.assertEqual(result, "Java not found")

    @patch("ww.linux.system.run_command")
    def test_parses_version_without_quotes(self, mock_rc):
        from ww.linux.system import get_java_version

        mock_rc.return_value = "java version 11.0.2 extra"
        result = get_java_version()
        self.assertEqual(result, "11.0.2")


class TestGetGnomeVersion(unittest.TestCase):
    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"})
    @patch("ww.linux.system.run_command")
    def test_gnome_running(self, mock_rc):
        from ww.linux.system import get_gnome_version

        mock_rc.return_value = "GNOME Shell 42.0"
        result = get_gnome_version()
        self.assertEqual(result, "42.0")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": ""}, clear=False)
    @patch("ww.linux.system.run_command")
    def test_gnome_installed_not_running(self, mock_rc):
        from ww.linux.system import get_gnome_version

        mock_rc.side_effect = [None, "/usr/bin/gdm"]
        result = get_gnome_version()
        self.assertEqual(result, "GNOME installed (not currently running)")

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": ""}, clear=False)
    @patch("ww.linux.system.run_command", return_value=None)
    def test_gnome_not_detected(self, mock_rc):
        from ww.linux.system import get_gnome_version

        result = get_gnome_version()
        self.assertEqual(result, "GNOME not detected")


class TestGetKernelInfo(unittest.TestCase):
    @patch("ww.linux.system.run_command", return_value="5.15.0-generic")
    def test_returns_kernel(self, mock_rc):
        from ww.linux.system import get_kernel_info

        self.assertEqual(get_kernel_info(), "5.15.0-generic")


class TestGetDiskInfo(unittest.TestCase):
    @patch("ww.linux.system.subprocess.run")
    def test_parses_disk_output(self, mock_run):
        from ww.linux.system import get_disk_info

        stdout = "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   50G   45G  53% /\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=stdout)
        result = get_disk_info()
        self.assertIn("Total: 100G", result)
        self.assertIn("Used: 50G", result)
        self.assertIn("Available: 45G", result)

    @patch(
        "ww.linux.system.subprocess.run",
        side_effect=subprocess.TimeoutExpired("df -h /", 5),
    )
    def test_returns_error_message(self, mock_run):
        from ww.linux.system import get_disk_info

        result = get_disk_info()
        self.assertEqual(result, "Unable to retrieve disk information")

    @patch("ww.linux.system.subprocess.run")
    def test_returns_error_on_failure(self, mock_run):
        from ww.linux.system import get_disk_info

        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = get_disk_info()
        self.assertEqual(result, "Unable to retrieve disk information")


class TestGetMemoryInfo(unittest.TestCase):
    @patch(
        "builtins.open",
        mock_open(
            read_data="MemTotal:       16384000 kB\nMemAvailable:    8192000 kB\n"
        ),
    )
    def test_parses_meminfo(self):
        from ww.linux.system import get_memory_info

        result = get_memory_info()
        self.assertIn("Total:", result)
        self.assertIn("Used:", result)
        self.assertIn("Available:", result)

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_returns_error_when_no_proc(self, mock_fo):
        from ww.linux.system import get_memory_info

        result = get_memory_info()
        self.assertEqual(result, "Unable to retrieve memory information")


class TestGetGpuInfo(unittest.TestCase):
    @patch("ww.linux.system.run_command")
    def test_nvidia_gpu(self, mock_rc):
        from ww.linux.system import get_gpu_info

        # nvidia-smi call returns data, AMD/Intel/PCI return None
        mock_rc.side_effect = [
            "RTX 3090, 24576, 1024, 23552",  # nvidia
            None,  # amd
            None,  # intel
            None,  # pci fallback
        ]
        result = get_gpu_info()
        self.assertIn("NVIDIA RTX 3090", result)

    @patch("ww.linux.system.run_command", return_value=None)
    def test_no_gpu(self, mock_rc):
        from ww.linux.system import get_gpu_info

        result = get_gpu_info()
        self.assertEqual(result, "No GPU detected")

    @patch("ww.linux.system.run_command")
    def test_pci_fallback(self, mock_rc):
        from ww.linux.system import get_gpu_info

        mock_rc.side_effect = [None, None, None, "VGA compatible controller: Some GPU"]
        result = get_gpu_info()
        self.assertIn("GPU detected", result)


class TestGetCudaInfo(unittest.TestCase):
    @patch("ww.linux.system.run_command")
    def test_full_cuda_info(self, mock_rc):
        from ww.linux.system import get_cuda_info

        mock_rc.side_effect = [
            "525.60",  # driver version
            "12.0",  # cuda runtime
            "12.0",  # nvcc
            "8",  # cudnn major
            "6",  # cudnn minor
            "0",  # cudnn patch
        ]
        result = get_cuda_info()
        self.assertIn("NVIDIA Driver: 525.60", result)
        self.assertIn("CUDA Runtime: 12.0", result)
        self.assertIn("NVCC Compiler: 12.0", result)
        self.assertIn("cuDNN: 8.6.0", result)

    @patch("ww.linux.system.run_command", return_value=None)
    def test_no_cuda(self, mock_rc):
        from ww.linux.system import get_cuda_info

        result = get_cuda_info()
        self.assertEqual(result, "CUDA/NVIDIA drivers not detected")

    @patch("ww.linux.system.run_command")
    def test_driver_only(self, mock_rc):
        from ww.linux.system import get_cuda_info

        mock_rc.side_effect = ["525.60", None, None, None]
        result = get_cuda_info()
        self.assertIn("NVIDIA Driver: 525.60", result)
        self.assertNotIn("CUDA", result)


class TestRun(unittest.TestCase):
    @patch("ww.linux.system.get_cuda_info", return_value="No CUDA")
    @patch("ww.linux.system.get_gpu_info", return_value="No GPU")
    @patch("ww.linux.system.get_disk_info", return_value="Disk: ok")
    @patch("ww.linux.system.get_memory_info", return_value="Mem: ok")
    @patch("ww.linux.system.platform")
    @patch("ww.linux.system.get_gnome_version", return_value="GNOME 42")
    @patch("ww.linux.system.get_java_version", return_value="17.0.1")
    @patch("ww.linux.system.get_python_version", return_value="3.14.0")
    @patch("ww.linux.system.get_kernel_info", return_value="5.15.0")
    @patch("ww.linux.system.get_architecture", return_value="64-bit")
    @patch("ww.linux.system.get_os_info", return_value="Ubuntu 22.04")
    def test_run_prints_info(self, *mocks):
        from ww.linux.system import run

        # Should not raise
        run()


if __name__ == "__main__":
    unittest.main()
