import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("OPENROUTER_API_KEY", "test-fake-key")

from ww.linux import gpu


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


class TestGetGpuInfo(unittest.TestCase):
    @patch("ww.linux.gpu.run_command")
    def test_nvidia_gpu(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "nvidia-smi" in cmd and "query-gpu=name" in cmd:
                return "RTX 3090, 24576, 1024, 23552"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_gpu_info()
        self.assertIn("NVIDIA RTX 3090", result)
        self.assertIn("24576 MB total", result)

    @patch("ww.linux.gpu.run_command")
    def test_amd_gpu(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "lspci" in cmd and "amd" in cmd.lower():
                return "VGA compatible controller: AMD Radeon RX 6800"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_gpu_info()
        self.assertIn("AMD GPU detected", result)

    @patch("ww.linux.gpu.run_command")
    def test_intel_gpu(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "lspci" in cmd and "intel" in cmd.lower():
                return "VGA compatible controller: Intel UHD Graphics"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_gpu_info()
        self.assertIn("Intel GPU detected", result)

    @patch("ww.linux.gpu.run_command")
    def test_pci_fallback(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if cmd == "lspci | grep -i vga | head -5":
                return "00:02.0 VGA compatible controller: Unknown GPU"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_gpu_info()
        self.assertIn("GPU detected", result)

    @patch("ww.linux.gpu.run_command")
    def test_no_gpu(self, mock_cmd):
        mock_cmd.return_value = None
        result = gpu.get_gpu_info()
        self.assertEqual(result, "No GPU detected")

    @patch("ww.linux.gpu.run_command")
    def test_nvidia_failed_string(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "nvidia-smi" in cmd:
                return "failed to initialize NVML"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_gpu_info()
        self.assertEqual(result, "No GPU detected")

    @patch("ww.linux.gpu.run_command")
    def test_multiple_gpus(self, mock_cmd):
        def side_effect(cmd, fallback=None):
            if "nvidia-smi" in cmd and "query-gpu=name" in cmd:
                return "RTX 3090, 24576, 1024, 23552\nRTX 4090, 49152, 2048, 47104"
            return fallback

        mock_cmd.side_effect = side_effect
        result = gpu.get_gpu_info()
        self.assertIn("RTX 3090", result)
        self.assertIn("RTX 4090", result)


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
        result = gpu.get_cuda_info()
        self.assertEqual(result, "CUDA/NVIDIA drivers not detected")

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
        result = gpu.get_cuda_info()
        self.assertEqual(result, "CUDA/NVIDIA drivers not detected")

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
        self.assertIn("Vulkan ICD", result)
        self.assertIn("Vulkan SDK", result)

    @patch("ww.linux.gpu.run_command")
    def test_vulkan_not_detected(self, mock_cmd):
        mock_cmd.return_value = None
        result = gpu.get_vulkan_info()
        self.assertEqual(result, "Vulkan not detected")


class TestCheckProxySettings(unittest.TestCase):
    def test_no_proxy(self):
        with patch.dict(os.environ, {}, clear=True):
            result = gpu.check_proxy_settings()
            self.assertIsNone(result)

    def test_http_proxy(self):
        with patch.dict(os.environ, {"HTTP_PROXY": "http://proxy:8080"}, clear=True):
            result = gpu.check_proxy_settings()
            self.assertIsNotNone(result)
            self.assertIn("HTTP_PROXY", result)

    def test_https_proxy(self):
        with patch.dict(os.environ, {"HTTPS_PROXY": "https://proxy:8443"}, clear=True):
            result = gpu.check_proxy_settings()
            self.assertIsNotNone(result)
            self.assertIn("HTTPS_PROXY", result)

    def test_both_proxies(self):
        env = {"HTTP_PROXY": "http://p:80", "HTTPS_PROXY": "https://p:443"}
        with patch.dict(os.environ, env, clear=True):
            result = gpu.check_proxy_settings()
            self.assertIn("HTTP_PROXY", result)
            self.assertIn("HTTPS_PROXY", result)


class TestRun(unittest.TestCase):
    @patch("ww.linux.gpu.get_vulkan_info", return_value="Vulkan not detected")
    @patch(
        "ww.linux.gpu.get_cuda_info", return_value="CUDA/NVIDIA drivers not detected"
    )
    @patch("ww.linux.gpu.get_gpu_info", return_value="No GPU detected")
    @patch("ww.linux.gpu.check_proxy_settings", return_value=None)
    def test_run_no_gpu(self, mock_proxy, mock_gpu, mock_cuda, mock_vulkan):
        # Should not raise
        gpu.run()

    @patch("ww.linux.gpu.get_vulkan_info", return_value="Vulkan ICD: RTX 3090")
    @patch("ww.linux.gpu.get_cuda_info", return_value="NVIDIA Driver: 535.0")
    @patch(
        "ww.linux.gpu.get_gpu_info",
        return_value="NVIDIA RTX 3090: 24576 MB total, 1024 MB used, 23552 MB free",
    )
    @patch("ww.linux.gpu.check_proxy_settings", return_value="HTTP_PROXY: http://p:80")
    def test_run_with_gpu(self, mock_proxy, mock_gpu, mock_cuda, mock_vulkan):
        gpu.run()


if __name__ == "__main__":
    unittest.main()
