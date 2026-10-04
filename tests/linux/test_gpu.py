import os
import unittest
from unittest.mock import MagicMock, mock_open, patch

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.linux import gpu

_NVIDIA_UEVENT = "DRIVER=nvidia\nPCI_SLOT_NAME=0000:01:00.0\nPCI_CLASS=30000\n"
_NON_GPU_UEVENT = "DRIVER=r8169\nPCI_SLOT_NAME=0000:02:00.0\nPCI_CLASS=020000\n"

_NVIDIA_LSPCI = (
    "0000:01:00.0: VGA compatible controller: "
    "NVIDIA Corporation GA102 [GeForce RTX 3090] (rev a1)"
)


class TestRunCommand(unittest.TestCase):
    @patch("ww.linux.gpu.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output\n")
        result = gpu.run_command("echo hello")
        self.assertEqual(result, "output")

    @patch("ww.linux.gpu.subprocess.run")
    def test_failure_returns_fallback(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = gpu.run_command("bad_cmd", fallback="default")
        self.assertEqual(result, "default")

    @patch("ww.linux.gpu.subprocess.run")
    def test_failure_no_fallback(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        result = gpu.run_command("bad_cmd")
        self.assertIsNone(result)

    @patch("ww.linux.gpu.subprocess.run")
    def test_timeout_returns_fallback(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)
        result = gpu.run_command("slow_cmd", fallback="timeout_default")
        self.assertEqual(result, "timeout_default")

    @patch("ww.linux.gpu.subprocess.run")
    def test_file_not_found_returns_fallback(self, mock_run):
        mock_run.side_effect = FileNotFoundError("no such file")
        result = gpu.run_command("nonexistent", fallback="fb")
        self.assertEqual(result, "fb")

    @patch("ww.linux.gpu.subprocess.run")
    def test_subprocess_error_returns_fallback(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.SubprocessError("err")
        result = gpu.run_command("cmd", fallback="fb")
        self.assertEqual(result, "fb")


class TestDetectGpus(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    @patch("ww.linux.gpu.os.path.exists", return_value=True)
    @patch("ww.linux.gpu.glob.glob", return_value=["/sys/class/drm/card0"])
    @patch("builtins.open", mock_open(read_data=_NVIDIA_UEVENT))
    def test_nvidia_gpu_detected(self, mock_glob, mock_exists, mock_cmd):
        mock_cmd.return_value = _NVIDIA_LSPCI
        result = gpu.detect_gpus()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["card"], "card0")
        self.assertEqual(result[0]["driver"], "nvidia")
        self.assertEqual(result[0]["pci_id"], "0000:01:00.0")
        self.assertIn("RTX 3090", result[0]["name"])
        mock_cmd.assert_called_once()
        self.assertIn("lspci -s 0000:01:00.0", mock_cmd.call_args[0][0])

    @patch("ww.linux.gpu.run_command")
    @patch("ww.linux.gpu.os.path.exists", return_value=True)
    @patch("ww.linux.gpu.glob.glob", return_value=["/sys/class/drm/card0"])
    @patch("builtins.open", mock_open(read_data=_NON_GPU_UEVENT))
    def test_skips_non_display_device(self, mock_glob, mock_exists, mock_cmd):
        self.assertEqual(gpu.detect_gpus(), [])

    @patch("ww.linux.gpu.run_command")
    @patch("ww.linux.gpu.os.path.exists", return_value=False)
    @patch("ww.linux.gpu.glob.glob", return_value=["/sys/class/drm/card0"])
    def test_missing_uevent_skipped(self, mock_glob, mock_exists, mock_cmd):
        self.assertEqual(gpu.detect_gpus(), [])

    @patch("ww.linux.gpu.run_command")
    @patch("ww.linux.gpu.glob.glob", return_value=[])
    def test_no_cards(self, mock_glob, mock_cmd):
        self.assertEqual(gpu.detect_gpus(), [])


class TestNvidiaProprietaryInfo(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    def test_memory_info(self, mock_cmd):
        mock_cmd.return_value = "NVIDIA GeForce RTX 3090, 24576, 1024, 23552"
        result = gpu.get_nvidia_proprietary_info({"card": "card0"})
        self.assertIn("24576 MiB total, 1024 MiB used, 23552 MiB free", result)

    @patch("ww.linux.gpu.run_command")
    def test_multiple_gpus(self, mock_cmd):
        mock_cmd.return_value = (
            "NVIDIA GeForce RTX 3090, 24576, 1024, 23552\n"
            "NVIDIA GeForce RTX 4090, 49152, 2048, 47104"
        )
        result = gpu.get_nvidia_proprietary_info({"card": "card0"})
        self.assertIn("24576 MiB total", result)
        self.assertIn("49152 MiB total", result)

    @patch("ww.linux.gpu.run_command")
    def test_nvidia_smi_failed_string(self, mock_cmd):
        mock_cmd.return_value = "failed to initialize NVML"
        self.assertIsNone(gpu.get_nvidia_proprietary_info({"card": "card0"}))

    @patch("ww.linux.gpu.run_command")
    def test_nvidia_smi_missing(self, mock_cmd):
        mock_cmd.return_value = None
        self.assertIsNone(gpu.get_nvidia_proprietary_info({"card": "card0"}))


class TestNouveauMemoryInfo(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    def test_memory_from_eglinfo(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "eglinfo" in cmd:
                return (
                    "OpenGL information:\n"
                    "  Dedicated video memory: 8192 MB\n"
                    "  Currently available dedicated video memory: 2048 MB"
                )
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_nouveau_memory_info()
        self.assertIn("8192 MiB total, 6144 MiB used, 2048 MiB free", result)

    @patch("ww.linux.gpu.run_command", return_value=None)
    def test_no_info(self, mock_cmd):
        self.assertIsNone(gpu.get_nouveau_memory_info())


class TestAmdMemoryInfo(unittest.TestCase):
    def test_vram_from_sysfs(self):
        def fake_open(path, *args, **kwargs):
            p = str(path)
            if p.endswith("mem_info_vram_total"):
                return mock_open(read_data=str(16 * 1024**3))()
            if p.endswith("mem_info_vram_used"):
                return mock_open(read_data=str(4 * 1024**3))()
            raise FileNotFoundError(p)

        with patch("builtins.open", side_effect=fake_open):
            result = gpu.get_amd_memory_info("card0")
        self.assertEqual(result, "  16384 MiB total, 4096 MiB used, 12288 MiB free")

    def test_sysfs_missing(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            self.assertIsNone(gpu.get_amd_memory_info("card0"))


class TestGpuTemperature(unittest.TestCase):
    @patch("builtins.open", mock_open(read_data="45600"))
    @patch("ww.linux.gpu.os.path.exists", return_value=True)
    @patch(
        "ww.linux.gpu.glob.glob",
        return_value=["/sys/class/drm/card0/device/hwmon/hwmon1"],
    )
    def test_temperature_read(self, mock_glob, mock_exists):
        self.assertEqual(gpu.get_gpu_temperature("card0"), "45.6°C")

    @patch("ww.linux.gpu.glob.glob", return_value=[])
    def test_no_hwmon(self, mock_glob):
        self.assertIsNone(gpu.get_gpu_temperature("card0"))


class TestRendererInfo(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    def test_renderer_from_glxinfo(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "OpenGL renderer string" in cmd:
                return "OpenGL renderer string: NVIDIA GeForce RTX 3090/PCIe/SSE2"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_renderer_info()
        self.assertEqual(result, "NVIDIA GeForce RTX 3090/PCIe/SSE2")

    @patch("ww.linux.gpu.run_command", return_value=None)
    def test_no_renderer(self, mock_cmd):
        self.assertIsNone(gpu.get_renderer_info())


class TestToolAvailable(unittest.TestCase):
    @patch("ww.linux.gpu.run_command", return_value="/usr/bin/nvtop")
    def test_installed(self, mock_cmd):
        self.assertTrue(gpu.tool_available("nvtop"))

    @patch("ww.linux.gpu.run_command", return_value=None)
    def test_missing(self, mock_cmd):
        self.assertFalse(gpu.tool_available("nvtop"))


class TestGetCudaInfo(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    def test_full_cuda_info(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "driver_version" in cmd:
                return "535.104.05"
            if "cuda_runtime_version" in cmd:
                return "12.2"
            if "nvcc" in cmd:
                return "12.2.91"
            if "CUDNN_MAJOR" in cmd:
                return "8"
            if "CUDNN_MINOR" in cmd:
                return "9"
            if "CUDNN_PATCHLEVEL" in cmd:
                return "7"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_cuda_info()
        self.assertIn("NVIDIA Driver: 535.104.05", result)
        self.assertIn("CUDA Runtime: 12.2", result)
        self.assertIn("NVCC Compiler: 12.2.91", result)
        self.assertIn("cuDNN: 8.9.7", result)

    @patch("ww.linux.gpu.run_command")
    def test_no_cuda(self, mock_cmd):
        mock_cmd.return_value = None
        self.assertIsNone(gpu.get_cuda_info())

    @patch("ww.linux.gpu.run_command")
    def test_driver_only(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "driver_version" in cmd:
                return "535.104.05"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_cuda_info()
        self.assertIn("NVIDIA Driver: 535.104.05", result)
        self.assertNotIn("CUDA Runtime", result)

    @patch("ww.linux.gpu.run_command")
    def test_driver_failed_string(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "driver_version" in cmd:
                return "failed to initialize"
            return fallback

        mock_cmd.side_effect = side_effect
        self.assertIsNone(gpu.get_cuda_info())

    @patch("ww.linux.gpu.run_command")
    def test_nvcc_empty(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "driver_version" in cmd:
                return "535.0"
            if "nvcc" in cmd:
                return ""
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_cuda_info()
        self.assertNotIn("NVCC", result)


class TestGetVulkanInfo(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    def test_vulkan_detected(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "device name" in cmd:
                return "NVIDIA GeForce RTX 3090"
            if "vulkan" in cmd.lower():
                return "Vulkan Instance Version: 1.3.250"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_vulkan_info()
        self.assertIn("Devices: NVIDIA GeForce RTX 3090", result)
        self.assertIn("Runtime: Vulkan Instance Version: 1.3.250", result)

    @patch("ww.linux.gpu.run_command", return_value=None)
    def test_vulkan_not_detected(self, mock_cmd):
        self.assertIsNone(gpu.get_vulkan_info())


class TestRun(unittest.TestCase):
    @patch("ww.linux.gpu.tool_available", return_value=False)
    @patch("ww.linux.gpu.get_vulkan_info", return_value=None)
    @patch("ww.linux.gpu.get_cuda_info", return_value=None)
    @patch("ww.linux.gpu.run_command", return_value=None)
    @patch("ww.linux.gpu.detect_gpus", return_value=[])
    def test_run_no_gpu(self, mock_detect, mock_run, mock_cuda, mock_vulkan, mock_tool):
        # Should not raise
        gpu.run()

    @patch("ww.linux.gpu.tool_available", return_value=False)
    @patch("ww.linux.gpu.get_vulkan_info", return_value=None)
    @patch("ww.linux.gpu.get_cuda_info", return_value=None)
    @patch("ww.linux.gpu.get_nvidia_proprietary_info", return_value=None)
    @patch("ww.linux.gpu.get_gpu_temperature", return_value=None)
    @patch(
        "ww.linux.gpu.detect_gpus",
        return_value=[
            {
                "card": "card0",
                "pci_id": "0000:01:00.0",
                "driver": "nvidia",
                "name": "NVIDIA Corporation GA102 [GeForce RTX 3090]",
            }
        ],
    )
    def test_run_with_gpu(
        self, mock_detect, mock_temp, mock_nvidia, mock_cuda, mock_vulkan, mock_tool
    ):
        gpu.run()


if __name__ == "__main__":
    unittest.main()
